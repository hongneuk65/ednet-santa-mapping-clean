"""Generate and optionally execute a self-contained process notebook."""
import argparse
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def create(execute=False):
    import nbformat as nbf
    md=nbf.v4.new_markdown_cell;code=nbf.v4.new_code_cell
    cells=[
        md('# EdNet × Santa — làm lại từ nguồn\n\nKhông dùng mapping cũ. Notebook đi qua kiểm kê → match → tỷ lệ → mapping thô → nhóm cha. Đọc `docs/PIPELINE.md` và `docs/RESULTS.md` để biết công thức, số liệu và giới hạn.\n\n**Không có gold accuracy. Part 1 không được xem như đã match câu nếu chỉ có lecture bridge.**'),
        code("from pathlib import Path\nimport sys, json\nimport pandas as pd\nimport numpy as np\nimport matplotlib.pyplot as plt\nfrom IPython.display import display\nROOT = Path.cwd().resolve()\nif not (ROOT / 'config/policy.json').exists():\n    ROOT = ROOT.parent\nassert (ROOT / 'src/pipeline.py').exists(), 'Open notebook from this repository'\nsys.path.insert(0, str(ROOT))\nREBUILD = False\nif REBUILD:\n    from src.pipeline import run\n    run()\nOUT = ROOT / 'outputs'\nassert (OUT / 'summary.json').exists(), 'Run python -m src.pipeline first'\nload = lambda name: json.loads((OUT / name).read_text(encoding='utf-8'))\nsummary = load('summary.json')\nmapping = load('tag_mapping.json')\nmatched = pd.DataFrame(load('matched_questions.json'))\nrates = pd.read_csv(OUT / 'tag_label_rates.csv')\ndecisions = pd.read_csv(OUT / 'mapping_decisions.csv')\nnames = load('label_names.json')\nplt.rcParams.update({'figure.dpi': 110, 'axes.spines.top': False, 'axes.spines.right': False})\nprint('Snapshot:', summary['snapshot'])"),
        md('## 1. Data có gì?\n\nNguồn duy nhất là raw content và hai CSV EdNet trong repo. Trường tự suy ra chỉ nằm trong outputs; raw không bị sửa.'),
        code("inventory = pd.Series({k: summary[k] for k in ['reference_questions','reference_tags','raw_content_files','crawl_question_occurrences','crawl_unique_questions','lecture_matches']}, name='count')\ndisplay(inventory.to_frame())\nfig, ax = plt.subplots(figsize=(8,3.2))\nparts = summary['crawl_questions_by_part']\nax.bar(sorted(parts), [parts[p] for p in sorted(parts)], color='#275d4b')\nax.set(xlabel='TOEIC Part', ylabel='Unique question IDs', title='Santa raw: distinct questions by Part')\nfor i,p in enumerate(sorted(parts)): ax.text(i, parts[p], str(parts[p]), ha='center', va='bottom')\nfig.tight_layout(); plt.show()"),
        md('## 2. Match ID và kiểm tra nối\n\nTừng cổng kiểm tra giữ số liệu riêng. Chỉ strict matches được dùng đo tỷ lệ. Trùng ID không đủ chứng minh cùng câu. Không ép UUID về ID số.'),
        code("funnel = pd.Series({'Santa unique IDs':summary['crawl_unique_questions'], 'EdNet ID overlap':summary['id_overlap'], 'ID + Part + answer':summary['three_key_matches'], '+ Exact bundle':summary['strict_question_matches']})\nfig, ax = plt.subplots(figsize=(9,3.6))\nax.barh(funnel.index[::-1], funnel.values[::-1], color='#275d4b')\nfor i,v in enumerate(funnel.values[::-1]): ax.text(v+20, i, f'{v:,}', va='center')\nax.set(xlabel='Distinct question IDs', title='Join audit: increasingly strict checks'); ax.set_xlim(0,max(funnel.values)*1.13)\nfig.tight_layout(); plt.show()\naudit = load('join_audit.json')\ndisplay(pd.DataFrame(audit['rejected_variants']))\nassert matched.question_id.is_unique\nprint('Matched Part 1:', int((matched.part == 'p1').sum()))"),
        md('## 3. Nhãn thô đến từ đâu?\n\nCác trục task / grammar / topic / format / accent được tách riêng. Xem config để sửa độ chi tiết. Mã metadata lặp giữa chapter và chapterList chỉ đếm một lần.'),
        code("families = json.loads((ROOT / 'config/label_families.json').read_text(encoding='utf-8'))\ndisplay(pd.DataFrame(families['rules'])[['id','axis','name','parts']])\ndisplay(decisions.groupby(['source','status']).size().rename('decisions').to_frame())"),
        md('## 4. Tag nào phủ nhãn nào, tỷ lệ bao nhiêu?\n\nP_observed = hits / observed, không phải hits / toàn EdNet. Luôn nhìn thêm observability, bridge coverage và số bundle. Nhãn nhiều thuộc tính có thể cùng đạt tỷ lệ cao; không cưỡng ép một tên duy nhất.'),
        code("columns = ['tag_id','part','axis','label','hits','observed','precision_observed','observed_fraction','bridge_coverage','reference_bundle_support','recall_same_part_observed','lift']\nranked = rates.sort_values(['precision_observed','reference_bundle_support'], ascending=[False,False])\ndisplay(ranked[columns].head(30))\nstrong = ranked[(ranked.observed >= 20) & (ranked.axis != 'accent')].head(20).copy()\nif len(strong):\n    labels = strong.apply(lambda r: f\"tag {r.tag_id} / {r.part}: {r.label}\", axis=1)\n    fig, ax = plt.subplots(figsize=(11,7))\n    ax.barh(labels.iloc[::-1], strong.precision_observed.iloc[::-1]*100, color='#275d4b')\n    ax.set(xlabel='P(proxy label | tag, Part, observed), %', title='Highest observed proxy rates (at least 20 observed questions)', xlim=(0,105))\n    fig.tight_layout(); plt.show()"),
        md('## 5. Độ phủ trên toàn EdNet\n\nBiểu đồ phân biệt có ít nhất một đề xuất và mọi tag đã có đề xuất. Accent không tính thành kỹ năng. Không bỏ tag chưa rõ khỏi mẫu số.'),
        code("coverage = pd.DataFrame(summary['coverage']).set_index('part')\ndisplay(coverage)\np = coverage.drop(index='all')\nx = np.arange(len(p)); fig, ax = plt.subplots(figsize=(9,4))\nax.bar(x-.18, p.any_semantic/p.questions*100, .36, label='At least one content/task/format proposal', color='#275d4b')\nax.bar(x+.18, p.all_original_tags_semantic/p.questions*100, .36, label='All original tags have proposals', color='#b79b68')\nax.set(xticks=x, xticklabels=p.index, xlabel='TOEIC Part', ylabel='EdNet questions, %', title='Proposal coverage, not semantic accuracy', ylim=(0,108))\nax.legend(loc='upper center', bbox_to_anchor=(.5,-.17), frameon=False)\nfig.tight_layout(); plt.show()"),
        md('## 6. Gom tag thành nhóm cha và nhóm yếu\n\nNhóm cùng nhãn thô giữ scope từng tag. Tag có thể nằm ở nhiều trục nên các nhóm có thể giao nhau: **không cộng số giảm như cluster rời nhau**. Nhóm yếu theo profile không tự nhận tên kỹ năng.'),
        code("clusters = pd.DataFrame(mapping['clusters'])\ndisplay(clusters[['cluster_id','kind','axis','label','members','status']])\nparents = clusters[clusters.kind == 'same_coarse_label_parent'].copy()\nparents['member_count'] = parents.members.map(len)\ntop = parents.sort_values('member_count', ascending=False).head(18)\nif len(top):\n    fig, ax = plt.subplots(figsize=(10,6))\n    ax.barh(top.cluster_id.iloc[::-1], top.member_count.iloc[::-1], color='#275d4b')\n    ax.set(xlabel='Distinct original tag IDs in parent', title='Largest proposed parent groups (members can overlap)')\n    fig.tight_layout(); plt.show()\nprint('Tag/Part/axis units:', summary['named_tag_part_axis_units'])\nprint('Distinct coarse axis-label units:', summary['distinct_coarse_axis_labels'])\nprint('These are different resolutions, not a validated skill count.')"),
        md('## 7. Đọc bằng chứng trước khi chốt\n\nThay TAG để xem một tag: tỷ lệ, scope, mẫu câu và lecture anchors. Câu proxy có đáp án nhưng chưa được chuyên gia gắn gold. Đừng dùng một mẫu để suy ra nghĩa toàn tag.'),
        code("TAG = 3\nrecord = next(r for r in mapping['tags'] if r['tag_id'] == TAG)\ndisplay(pd.DataFrame(record['mappings']))\nexamples = matched[matched.tags.map(lambda values: TAG in values)]\ndisplay(examples[['question_id','part','question','correct_text','source_raw']].head(8))\nprint('Tag has semantic proposal:', record['has_semantic_label'])\nprint('Reference question count:', record['reference_questions'])\nprint('Question bridge count:', record['bridge_questions'])"),
        md('## 8. Hàng chờ duyệt và giới hạn\n\n1. Duyệt nhóm cha trong config có đủ khái quát và cùng trục không.\n2. Duyệt các tag chỉ có lecture, ít mẫu, near-tie, nhãn metadata content hoặc nhóm profile chưa tên.\n3. Giữ unresolved khi thiếu dữ liệu.\n4. Chạy kiểm thử và đánh giá độc lập trước khi chốt dictionary dùng cho mô hình.'),
        code("pending = pd.DataFrame([{k:r[k] for k in ['tag_id','reference_questions','bridge_questions','has_semantic_label','has_any_descriptor','has_unnamed_family']} for r in mapping['tags']])\ndisplay(pending[~pending.has_semantic_label])\nprint('Gold accuracy:', summary['gold_accuracy'])\nprint((ROOT / 'docs/RESULTS.md').read_text(encoding='utf-8')[:3500])"),
    ]
    notebook=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},
        'language_info':{'name':'python'},'source_policy':'Only repo-local raw inputs, no prior mappings.'})
    path=ROOT/'notebooks/01_mapping.ipynb';path.parent.mkdir(exist_ok=True)
    if execute:
        from nbclient import NotebookClient
        from jupyter_client import KernelManager
        client=NotebookClient(notebook,timeout=180,startup_timeout=30,kernel_name='python3',resources={'metadata':{'path':str(ROOT)}})
        client.km=KernelManager(kernel_name='python3')
        client.km.kernel_spec.argv=[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}']
        print('Executing notebook with',sys.executable,flush=True)
        client.execute()
        if client.km is not None and client.km.has_kernel:
            client.km.shutdown_kernel(now=True)
    nbf.write(notebook,path)
    print('Notebook written:',path,'executed=',execute)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--execute',action='store_true')
    create(parser.parse_args().execute)
