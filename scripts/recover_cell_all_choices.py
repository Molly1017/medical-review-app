import json,re,hashlib
from pathlib import Path
from docx import Document
from import_cell_missing import parse_cell_options,ANSWER,OPTION_START

def main():
 src=Path('/tmp/cell-source.docx');target=Path('medical_question_bank_deduplicated.json');d=json.loads(target.read_text());existing={re.sub(r'\s+','',q.get('question','')) for q in d['questions']};chapter=None;kind='单选题';added=[]
 for i,p in enumerate(Document(src).paragraphs):
  raw=p.text.strip()
  if not raw:continue
  if raw.startswith('第') and '章' in raw:chapter=raw
  if '（一）单选题' in raw:kind='单选题';continue
  if '（二）多选题' in raw:kind='多选题';continue
  m=ANSWER.search(raw);first=OPTION_START.search(raw)
  if not m or not first or not chapter:continue
  stem=re.sub(r'^\s*\d+[.、)]?\s*','',raw[:first.start()]).strip();opts=parse_cell_options(raw[:m.start()])
  if not stem or not opts or len(opts)<4:continue
  key=re.sub(r'\s+','',stem)
  if key in existing:continue
  qid=hashlib.sha1((src.name+'|'+str(i)+'|'+stem).encode()).hexdigest()[:12]
  q={'id':qid,'course':'医学细胞生物学','chapter':chapter,'type':kind,'question':stem,'options':{k:opts[k] for k in 'ABCDE' if k in opts},'answer':m.group(1).upper(),'explanation':None,'source':src.name,'source_location':f'段落 {i+1}','status':'ready','raw':raw,'source_occurrences':[{'id':qid,'file':src.name,'location':f'段落 {i+1}','original_answer':m.group(1).upper()}],'source_verified':True,'source_paragraph':i+1,'answer_source':'original_source','answer_source_file':src.name,'answer_source_location':f'段落 {i+1}','answer_match_method':'same_source_paragraph'}
  d['questions'].append(q);existing.add(key);added.append(q)
 d.setdefault('summary',{})['cell_all_choice_recovered']=len(added);target.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');print('added',len(added))
if __name__=='__main__':main()
