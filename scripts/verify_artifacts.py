"""Check executed notebook, source binding and export its actual chart outputs."""
import base64
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def verify():
    run=json.loads((ROOT/'outputs/run_manifest.json').read_text(encoding='utf-8'))
    summary=json.loads((ROOT/'outputs/summary.json').read_text(encoding='utf-8'))
    assert summary['snapshot']==run['snapshot']
    for relative,expected in run['input_sha256'].items():
        assert hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()==expected,relative
    notebook=json.loads((ROOT/'notebooks/01_mapping.ipynb').read_text(encoding='utf-8'))
    codes=[cell for cell in notebook['cells'] if cell['cell_type']=='code']
    assert codes and all(c.get('execution_count') is not None for c in codes),'Notebook has unexecuted cells'
    assert not any(o['output_type']=='error' for c in codes for o in c.get('outputs',[])),'Notebook cell error'
    output_text='\n'.join(''.join(o.get('text',[])) for c in codes for o in c.get('outputs',[]) if o['output_type']=='stream')
    assert summary['snapshot'] in output_text,'Notebook snapshot differs from current results'
    plots=[];destination=ROOT/'outputs/figures';destination.mkdir(exist_ok=True)
    for i,cell in enumerate(codes):
        for j,output in enumerate(cell.get('outputs',[])):
            payload=output.get('data',{}).get('image/png')
            if payload:
                path=destination/f'cell_{i+1:02d}_{j:02d}.png'
                path.write_bytes(base64.b64decode(''.join(payload)))
                plots.append(path.relative_to(ROOT).as_posix())
    assert len(plots)>=5,'Expected actual plot outputs from the notebook'
    report={'passed':True,'snapshot':summary['snapshot'],'source_files_verified':len(run['input_sha256']),
        'executed_code_cells':len(codes),'plots':plots,'legacy_mapping_inputs':run['legacy_mapping_inputs'],
        'external_requests':run['external_requests']}
    (ROOT/'outputs/verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':verify()
