#!/usr/bin/env python3
import json,sys
from pathlib import Path
from docx import Document

def main():
    source=Path(sys.argv[1]); target=Path(sys.argv[2]); data=json.loads(target.read_text(encoding='utf-8'))
    rows=[p.text.strip() for p in Document(source).paragraphs]
    # The original chapter answer section lists fill answers immediately after
    # the chapter's “参考答案/填空题” heading; record 1 is absent from the
    # deduplicated export, so map records 2–11 to answer lines 2–11.
    answers=[]
    for i in range(108,120):
        if i < len(rows) and rows[i] and not rows[i].startswith(('参考答案','填空题')): answers.append((i+1,rows[i]))
    qs=[q for q in data['questions'] if q.get('course')=='医学微生物学' and q.get('chapter')=='第一章 细菌的形态与结构' and q.get('type')=='填空题']
    restored=0
    for q,(loc,ans) in zip(qs,answers[1:]):
        if not q.get('answer'):
            q['answer']=ans;q['answer_source']='original_source';q['answer_source_file']=source.name;q['answer_source_location']=f'段落 {loc}';q['answer_match_method']='chapter_answer_section';q['reference_answer']=ans;restored+=1
    data.setdefault('summary',{})['micro_ch1_fill_answers_restored']=restored
    target.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('restored',restored)
if __name__=='__main__':main()
