"""Copy only whitelisted content data; never copy credentials or old mappings."""
import argparse
import csv
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def import_sources(source_root):
    source_root = Path(source_root).resolve()
    paths = sorted((source_root/'data/full').glob('part*/raw/*.json'))
    paths += sorted((source_root/'data/supplemental/raw').glob('*.json'))
    if not paths:
        raise ValueError('No raw Santa content files found')
    pairs=[]
    for p in paths:
        relative=p.relative_to(source_root/'data')
        pairs.append((p, ROOT/'data/raw/santa'/relative))
    for name in ('questions.csv','lectures.csv'):
        pairs.append((source_root/'data/reference/ednet/contents'/name,ROOT/'data/raw/ednet'/name))
    manifest=[]
    for source,target in pairs:
        raw=source.read_bytes()
        if source.suffix=='.json':
            data=json.loads(raw.decode('utf-8-sig'))
            if 'oneOfDomainContent' not in data or 'baseContent' not in data:
                raise ValueError('Not a whitelisted content response: '+str(source))
            # Block credential-bearing content, rather than silently importing it.
            lowered=raw.lower()
            if b'bearer eyj' in lowered or b'"authorization"' in lowered or b'"accesstoken"' in lowered or b'"refreshtoken"' in lowered:
                raise ValueError('Potential credential in content; inspect locally before import: '+source.name)
        digest=hashlib.sha256(raw).hexdigest()
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()!=digest:
            raise ValueError('Destination differs; refusing to overwrite raw snapshot: '+str(target))
        target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():
            shutil.copyfile(source,target)
        manifest.append({'path':target.relative_to(ROOT).as_posix(),
            'source_relative_path':source.relative_to(source_root).as_posix(),'sha256':digest,'bytes':len(raw)})
    payload={'schema_version':1,'source_type':'local Santa raw content snapshot + EdNet content metadata',
        'files':manifest,'total_files':len(manifest),'total_bytes':sum(r['bytes'] for r in manifest),
        'excluded':['credentials','API catalogs/session history','prior mappings','prior experiment code','media binaries','payments/coupons'],
        'distribution':'Private local research copy; verify source terms before redistributing.'}
    (ROOT/'data/source_manifest.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:payload[k] for k in ('total_files','total_bytes','excluded')},ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source-root',type=Path,required=True)
    import_sources(parser.parse_args().source_root)
