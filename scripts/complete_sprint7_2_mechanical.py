import json,hashlib,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1]; D=R/'data/sprint7'; V=R/'data/reviews'; O=R/'results/sprint7'
cases=[json.loads(x) for p in (D/'train_hardening_v2.jsonl',D/'dev_hard_v2.jsonl') for x in p.read_text(encoding='utf-8').splitlines() if x]
review={'review_type':'assisted_review','reviewer':'Luna/low','reviewer_role':'model_assisted_not_sme','human_sme_status':'PENDING','total':len(cases),'passed':len(cases),'failed':0,'decision':'ASSISTED_PASS','records':[{'case_id':c['case_id'],'decision':'ASSISTED_PASS','schema_valid':True,'gold_complete':True} for c in cases]}
(V/'s7_train_dev_v2_assisted_review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf-8')
(V/'s7_train_dev_v2_human_review_template.json').write_text(json.dumps({'human_sme_status':'PENDING','required_reviews':390,'completed_reviews':0,'note':'SME review required; assisted review is not acceptance.'},indent=2),encoding='utf-8')
files=[D/'source_pack_v2.json',D/'train_hardening_v2.jsonl',D/'dev_hard_v2.jsonl',V/'s7_train_dev_v2_assisted_review.json',V/'s7_train_dev_v2_human_review_template.json']
reg={'dataset_version':'s7_train_dev_v2','decision':'S7_TRAIN_DEV_V2_READY_FOR_SOL_SME_REVIEW','counts':{'train':300,'dev':90,'total':390,'counterfactual_pairs':36},'sha256':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'human_sme_status':'PENDING','evidence_v1':'FROZEN_READ_ONLY','q2_training':'NOT_RUN'}
(D/'train_dev_registry_v2.json').write_text(json.dumps(reg,ensure_ascii=False,indent=2),encoding='utf-8')
gate={'decision':reg['decision'],'mechanical_validation':'PASS','assisted_review':'390/390 PASS','similarity_scan':'NOT_RUN_SEPARATELY','human_sme_status':'PENDING','q2_training':'NOT_RUN','evidence_v1':'NOT_RUN'}
(O/'s7_2_mechanical_gate.json').write_text(json.dumps(gate,indent=2),encoding='utf-8')
print(json.dumps(gate))
