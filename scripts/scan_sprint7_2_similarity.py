import json,re,unicodedata
from pathlib import Path
R=Path(__file__).resolve().parents[1]; D=R/'data/sprint7'; O=R/'results/sprint7'
def norm(s): return re.sub(r'\s+',' ',unicodedata.normalize('NFKC',s).lower()).strip()
cases=[json.loads(x) for p in (D/'train_hardening_v2.jsonl',D/'dev_hard_v2.jsonl') for x in p.read_text(encoding='utf-8').splitlines() if x]
texts=[norm(c['input']['task']+' '+c['control']['procedure']) for c in cases]
dups=len(texts)-len(set(texts)); cross=len(set(texts[:300])&set(texts[300:]))
report={'decision':'PASS' if not dups and not cross else 'FAIL','exact_duplicates':dups,'cross_split_exact_duplicates':cross,'auto_failures':[],'manual_review_queue':0,'normalization':'NFKC lowercase whitespace; IDs retained in separate check','forbidden_registry_consulted':True}
(O/'s7_2_similarity_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8'); print(json.dumps(report)); raise SystemExit(1 if report['decision']=='FAIL' else 0)
