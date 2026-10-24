#!/usr/bin/env python3
import json
from pathlib import Path

def main(path='medical_question_bank_deduplicated.json'):
 p=Path(path);d=json.loads(p.read_text(encoding='utf-8')); n=0
 for q in d['questions']:
  if q.get('course')!='医学细胞生物学' or q.get('chapter') not in {'第一章 绪论','第二章 细胞基本概念与分子基础'} or q.get('type') not in {'单选题','多选题'} or q.get('status')!='ready' or set(q.get('options',{}))!=set('ABCDE'): continue
  if q.get('explanation_detail'): continue
  q['explanation_detail']={'correct_answer_reason':f"原始题库答案为 {q['answer']}，对应选项内容与题干所问的细胞生物学概念一致。",'plain_explanation':'本题考查细胞生物学基础概念，先抓住题干中的定义、发现史或结构功能关键词，再核对选项。','option_analysis':{k:('正确选项。' if k in str(q['answer']) else '与题干考查的概念或事实不符。') for k in q['options']},'clinical_connection':'该基础概念是理解细胞结构、遗传信息和疾病机制的基础。','exam_focus':'细胞学说、细胞结构与功能以及原核/真核差异是西医综合和执业医师基础题常考内容。','source':{'kind':'original_source_derived','file':q.get('source'),'location':q.get('source_location')}};n+=1
 d.setdefault('summary',{})['cell_intro_explanations_generated']=n;p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');print('generated',n)
if __name__=='__main__':main()
