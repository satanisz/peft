import json, re
from pathlib import Path
R=Path(__file__).resolve().parents[1]; D=R/'data/sprint7'; O=R/'results/sprint7'
def load(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x]
train=load(D/'train_hardening_v2.jsonl'); dev=load(D/'dev_hard_v2.jsonl'); allc=train+dev; errs=[]
if len(train)!=300 or len(dev)!=90: errs.append('count')
ids=[c['case_id'] for c in allc]
if len(set(ids))!=390 or not all(re.match(r'^S7[TD]-\d{4}$',i) for i in ids): errs.append('ids')
allowed={'PASS':('NONE',False),'WARN':('MEDIUM',True),'FAIL':('HIGH',True),'INSUFFICIENT_DATA':('MEDIUM',True),'NOT_APPLICABLE':('NONE',False)}
seen_src=set()
for c in allc:
 o=c['expected_output']; src={s['source_id']:s for s in c['input']['sources']}; seen_src |= set(src)
 if o['status'] not in allowed or (o['severity'],o['requires_human_review'])!=allowed[o['status']]: errs.append(c['case_id']+':status')
 if o['control_type']!=c['control']['type'] or o['control_id']!=c['control']['id']: errs.append(c['case_id']+':control')
 if not set(e['source_id'] for e in o['evidence'])<=set(src): errs.append(c['case_id']+':evidence')
 if len(c.get('metadata',{}).get('provenance',[]))<4: errs.append(c['case_id']+':prov')
 if any(s['source_id'].endswith('u') for s in c['input']['sources']) and any(e['source_id'].endswith('u') for e in o['evidence']): errs.append(c['case_id']+':untrusted')
groups={}
for c in allc: groups.setdefault(c['group_id'],[]).append(c)
pair_groups=[v for k,v in groups.items() if k.startswith('S7') and len(v)==2]
if len(pair_groups)!=36: errs.append('pairs')
report={'decision':'PASS' if not errs else 'FAIL','train_count':len(train),'dev_count':len(dev),'total_count':len(allc),'source_count':len(seen_src),'counterfactual_pairs':len(pair_groups),'errors':errs}
(O/'s7_2_generation_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))
raise SystemExit(1 if errs else 0)
