#!/usr/bin/env python3
import argparse,json,re
from collections import Counter,defaultdict
from pathlib import Path
from docx import Document
OPTION=re.compile(r'(?<![A-Za-z-])([A-E])\s*[.．:：),，]')
def doc_candidates(path):
 rows=[p.text.strip() for p in Document(path).paragraphs]; n=0
 for t in rows:
  if len({m.group(1) for m in OPTION.finditer(t)})>=3 and ('答案' in t or '\n' in t or re.search(r'\d+[.、)]',t)): n+=1
 return n

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--json',default='medical_question_bank_deduplicated.json');ap.add_argument('--output',default='reports/choice_coverage.json');a=ap.parse_args();D=json.load(open(a.json));q=D['questions'];current=Counter(x.get('course') for x in q if x.get('type') in {'单选题','多选题'});sources=[]
 for path,course in [(Path('/tmp/codex-remote-attachments/01a16969-fbf3-76d1-a6f8-f13d8b72e096/21E1C38F-93D3-43A8-8252-DE7FE92F4A04/1-医学免疫学题库.docx'),'医学免疫学'),(Path('/tmp/codex-remote-attachments/01a16969-fbf3-76d1-a6f8-f13d8b72e096/21E1C38F-93D3-43A8-8252-DE7FE92F4A04/2-医学细胞生物学题库B.docx'),'医学细胞生物学'),(Path('/tmp/medical-originals/8.docx'),'医学微生物学'),(Path('/tmp/medical-originals/0.docx'),'医学微生物学')]:
  if path.exists():sources.append({'file':path.name,'course':course,'paragraph_choice_candidates':doc_candidates(path)})
 out={'json_choice_counts':dict(current),'source_scans':sources,'notes':['paragraph_choice_candidates are conservative source-level candidates, not a claim of exact deduplicated question count.','Original source files are external attachments and are not copied into the repository.','Case questions require source-level grouping review.']};Path(a.output).parent.mkdir(exist_ok=True);Path(a.output).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(out)
main()
