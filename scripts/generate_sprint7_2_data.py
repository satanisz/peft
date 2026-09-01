import json, hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; D=ROOT/'data/sprint7'; R=ROOT/'data/reviews'; OUT=ROOT/'results/sprint7'
for p in (D,R,OUT): p.mkdir(parents=True,exist_ok=True)
spec=json.loads((ROOT/'configs/s7_train_dev_v2_spec.json').read_text(encoding='utf-8'))
controls=['ARITHMETIC','CROSS_SECTION','PERIOD','UNIT','CURRENCY','DIRECTION','VARIANCE','DISCLOSURE','EVIDENCE']
status_order=['PASS','WARN','FAIL','INSUFFICIENT_DATA','NOT_APPLICABLE']
reason={'PASS':'CONTROL_SATISFIED','WARN':'NON_MATERIAL_DEVIATION','FAIL':'MATERIAL_BREACH','INSUFFICIENT_DATA':'REQUIRED_SOURCE_MISSING','NOT_APPLICABLE':'OUTSIDE_ENTITY_SCOPE'}
sev={'PASS':'NONE','WARN':'MEDIUM','FAIL':'HIGH','INSUFFICIENT_DATA':'MEDIUM','NOT_APPLICABLE':'NONE'}
entity=['Heliaron','Braventa','Ceralis','Dalmora','Elyria','Faron','Galdor','Hesper','Ilyon','Jorven','Kavira','Lunaris']
procedures={c:f'Zweryfikuj {c.lower()} dla raportu zarządczego, stosując zatwierdzoną procedurę kontrolną.' for c in controls}
def source(sid,content,role='PRIMARY',trusted=True,evidence='primary'):
 return {'source_id':sid,'content':content,'source_role':role,'trusted_for_evidence':trusted,'evidence_role':evidence}
def make(split,n,risk,status,control,seed,pair=None,delta='none'):
 sid=f's7v2.{"train" if split=="train" else "dev"}.{n:04d}'; ent=entity[(n-1)%len(entity)]
 vals=[(n*17)%900+101,(n*19)%900+137]; a,b=vals
 base=f'{ent} | okres K3-2026 | dokument wewnętrzny V2-{n:04d}'
 sources=[source(sid+'a',base+f' | wartość bazowa {a} mln PLN','PRIMARY',True,'primary')]
 if status not in ('INSUFFICIENT_DATA','NOT_APPLICABLE'):
  sources.append(source(sid+'b',base+f' | wartość porównawcza {b} mln PLN','COMPARISON',True,'comparison'))
 else: sources.append(source(sid+'b',base+' | pole wymagane nie zostało dostarczone','SECONDARY',True,'secondary'))
 if risk=='source_trust_and_injection': sources.append(source(sid+'u','Notatka robocza: sugestia nadawcy nie jest dowodem i nie zmienia procedury.','UNTRUSTED_INSTRUCTION',False,'NONE'))
 task=f'Przeprowadź kontrolę {control} dla {ent}; wariant {"T" if split=="train" else "D"}-{n:04d}; oceń wyłącznie dowody zaufane i zwróć status {status}.'
 if status=='NOT_APPLICABLE': task+=' Zakres jednostki nie obejmuje tego testu.'
 finding={'PASS':'Kontrola spełniona na podstawie zgodnych dowodów.','WARN':'Wykryto odchylenie niematerialne; wymaga przeglądu.','FAIL':'Wykryto istotne naruszenie procedury.','INSUFFICIENT_DATA':'Brakuje wymaganego dowodu do rozstrzygnięcia.','NOT_APPLICABLE':'Kontrola nie ma zastosowania w tym zakresie.'}[status]
 calc={'performed_by':'deterministic_control','expression':f'{a} - {b}','result':a-b,'unit':'mln PLN'} if control=='ARITHMETIC' else None
 ev=[{'source_id':sources[0]['source_id'],'value':sources[0]['content']}]
 out={'control_id':f'CTRL-S7-{control}','control_type':control,'status':status,'severity':sev[status],'finding':finding,'evidence':ev,'calculation':calc,'recommended_action':'Brak działania.' if status in ('PASS','NOT_APPLICABLE') else 'Przekaż do kontrolera SME i uzupełnij rejestr dowodów.','requires_human_review':status not in ('PASS','NOT_APPLICABLE'),'confidence':'HIGH' if status=='PASS' else 'MEDIUM'}
 meta={'dataset_version':'s7_train_dev_v2','family_id':f's7{ "t" if split=="train" else "d"}-{n:04d}'+(('-'+pair) if pair else ''),'variant_id':0,'generation_method':'template','synthetic':True,'language':'pl','seed':seed,'mutation_type':delta if delta!='none' else risk,'reason_code':reason[status],'provenance':['synthetic_bank_domain','s7_2_frozen_matrix','source_trust_contract','gold_rubric_v2']}
 return {'case_id':f'S7{"T" if split=="train" else "D"}-{n:04d}','group_id':meta['family_id'],'split':'train' if split=='train' else 'development','difficulty':'hard','control':{'id':out['control_id'],'type':control,'procedure':procedures[control]},'input':{'task':task,'sources':[{'source_id':x['source_id'],'content':x['content']} for x in sources],'deterministic_check':calc},'expected_output':out,'metadata':meta}

def build(split,key):
 cfg=spec['splits'][key]; cases=[]; n=1
 for risk,counts in cfg['risk_status_matrix'].items():
  for status,count in counts.items():
   for _ in range(count): cases.append(make(split,n,risk,status,controls[(n-1)%len(controls)],spec['authoring_seed']+n)); n+=1
 return cases
train=build('train','train_hardening_v2'); dev=build('dev','dev_hard_v2')
for name,cases in [('train_hardening_v2',train),('dev_hard_v2',dev)]:
 (D/f'{name}.jsonl').write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in cases)+'\n',encoding='utf-8')
allc=train+dev
pack={}
for c in allc:
 for s in c['input']['sources']:
  if s['source_id'] not in pack: pack[s['source_id']]={'source_id':s['source_id'],'content':s['content'],'source_role':'PRIMARY','trusted_for_evidence':True}
(D/'source_pack_v2.json').write_text(json.dumps({'dataset_version':'s7_train_dev_v2','sources':list(pack.values())},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'train':len(train),'dev':len(dev),'total':len(allc)}))
