import json
from pathlib import Path
p=Path('medical_question_bank_deduplicated.json');d=json.loads(p.read_text());changed=[]
for q in d['questions']:
 if q.get('type')!='名词解释':continue
 text=str(q.get('question',''))
 if '：' in text or ':' in text:
  sep='：' if '：' in text else ':'; head,body=text.split(sep,1)
  if 1<=len(head.strip())<=40 and len(body.strip())>=20:
   q['question']=head.strip();q['reference_answer']=body.strip();q['answer_source']='original_source';q['answer_source_file']=q.get('source');q['answer_source_location']=q.get('source_location');q['answer_match_method']='same_record_definition';q['needs_review']=False;q['review_resolution']='从同一原始记录的术语与定义拆分';changed.append(q['id'])
d.setdefault('summary',{})['batch2_term_splits']=len(changed);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');print('term_splits',len(changed),changed)
