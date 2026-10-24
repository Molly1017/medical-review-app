import json,re,argparse
from pathlib import Path
from docx import Document
A=re.compile(r'答案\s*[:：]\s*([A-E]+)',re.I); L=re.compile(r'(?<![A-Za-z-])([A-E])\s*[.．:：),，]')
def norm(s):return re.sub(r'\s+','',re.sub(r'^\d+[.、)]?','',str(s or ''))).lower()
def scan(path,course):
 out=[]
 for i,p in enumerate(Document(path).paragraphs):
  t=p.text.strip();m=A.search(t); ms=list(L.finditer(t[:m.start()] if m else t)); labels=[]
  for z in ms:
   if z.group(1) not in labels:labels.append(z.group(1))
  if len(labels)>=4 and m:
   stem=t[:ms[0].start()].strip() if ms else t;out.append({'course':course,'file':path.name,'paragraph':i+1,'stem':stem,'labels':labels,'answer':m.group(1).upper()})
 return out
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--json',default='medical_question_bank_deduplicated.json');ap.add_argument('--out',default='reports/source_choice_coverage.json');a=ap.parse_args();D=json.load(open(a.json));q=D['questions']; sources=[]
 paths=[('/tmp/codex-remote-attachments/01a16969-fbf3-76d1-a6f8-f13d8b72e096/2A28BA48-E2D0-4CB7-8977-E81C39BE1AA9/1-医学免疫学题库.docx','医学免疫学'),('/tmp/codex-remote-attachments/01a16969-fbf3-76d1-a6f8-f13d8b72e096/2A28BA48-E2D0-4CB7-8977-E81C39BE1AA9/2-医学细胞生物学题库B.docx','医学细胞生物学'),('/tmp/new-micro/8.docx','医学微生物学'),('/tmp/new-micro/0.docx','医学微生物学')]
 for f,c in paths:
  p=Path(f)
  if not p.exists():continue
  for row in scan(p,c):
   matches=[x['id'] for x in q if x.get('course')==c and norm(row['stem']) and (norm(row['stem']) in norm(x.get('question')) or norm(x.get('question')) in norm(row['stem'])) and len(x.get('options') or {})>=4]
   row['matched_ids']=matches;sources.append(row)
 out={'source_candidates':len(sources),'matched_candidates':sum(bool(x['matched_ids']) for x in sources),'unmatched_candidates':[x for x in sources if not x['matched_ids']],'json_choice_records':sum(x.get('type') in {'单选题','多选题'} for x in q),'json_complete_visible_choices':sum(x.get('type') in {'单选题','多选题'} and len(x.get('options') or {})>=4 and not x.get('exclude_from_quiz') for x in q)}
 Path(a.out).parent.mkdir(exist_ok=True);Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(out['source_candidates'],out['matched_candidates'],len(out['unmatched_candidates']))
main()
