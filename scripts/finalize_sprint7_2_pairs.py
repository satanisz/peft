import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]; D=R/'data/sprint7'
def load(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x]
def save(p,a): p.write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in a)+'\n',encoding='utf-8')
def pair(path,count,prefix):
 a=load(path); chosen=[]
 for i in range(0,count*2,2):
  x,y=a[i],a[i+1]; pid=f'{prefix}-{i//2+1:03d}'
  x['group_id']=pid; y['group_id']=pid; x['metadata']['mutation_type']='counterfactual_baseline'; y['metadata']['mutation_type']='counterfactual_premise_flip'; chosen += [x,y]
 return a
save(D/'train_hardening_v2.jsonl',pair(D/'train_hardening_v2.jsonl',24,'S7T-CF'))
save(D/'dev_hard_v2.jsonl',pair(D/'dev_hard_v2.jsonl',12,'S7D-CF'))
print('pairs finalized: 24 train, 12 dev')
