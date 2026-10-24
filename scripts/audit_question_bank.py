#!/usr/bin/env python3
import json,re
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
MARKER=re.compile(r'(?:答案|参考答案|正确答案)\s*[:：]',re.I); NUMBERED=re.compile(r'(?:^|\n)\s*\d+\s*[.、)]\s+')
def main():
 p=Path('medical_question_bank_deduplicated.json');d=json.loads(p.read_text());qs=d['questions'];issues=[];seen=defaultdict(list)
 def add(q,k,s,detail,suggest):issues.append({'id':q.get('id'),'course':q.get('course'),'chapter':q.get('chapter'),'source':q.get('source'),'source_location':q.get('source_location'),'type':q.get('type'),'severity':s,'kind':k,'detail':detail,'suggestion':suggest})
 for q in qs:
  text=str(q.get('question') or '').strip();seen[(q.get('course'),re.sub(r'\s+','',text))].append(q);opts=q.get('options') or {}
  if not text:add(q,'empty_stem','high','题干为空','依据原始文件恢复题干')
  if MARKER.search(text):add(q,'answer_marker_in_stem','high','题干混入答案标记','从原始段落重新切分')
  if q.get('type')=='名词解释' and (NUMBERED.search(text) or len(text)>120 or text.count('；')>=3):add(q,'term_merge_suspected','high','名词解释可能粘连多个术语或后续题目','按原始段落/题号拆分')
  if q.get('type') in {'单选题','多选题'}:
   labels=list(opts)
   if labels and labels!=sorted(labels,key='ABCDE'.index):add(q,'option_order','high',f'选项键顺序为 {labels}','按键排序，保持字母与内容对应')
   if set(labels)!=set('ABCDE'):add(q,'option_incomplete','high',f'选项集合为 {labels}','从原始记录恢复；无法确认则待审核')
   for label,value in opts.items():
    if MARKER.search(str(value)):add(q,'answer_marker_in_option','critical',f'{label} 选项混入答案标记','截断答案标记并保留答案字段')
    if NUMBERED.search(str(value)):add(q,'next_question_in_option','critical',f'{label} 选项疑似混入下一题','按原始题号重新拆分')
   ans=''.join(re.findall('[A-E]',str(q.get('answer') or '').upper()))
   if ans and not set(ans)<=set(opts):add(q,'answer_outside_options','critical',f'答案 {ans} 不在选项集合中','核对答案表与原题')
   if q.get('type')=='多选题' and ans and len(set(ans))<2:add(q,'multi_answer_incomplete','high','多选题答案少于两个选项','核对原始答案表')
  if q.get('answer_source')=='original_source' and not q.get('answer_source_location'):add(q,'answer_provenance_missing','medium','原始答案缺少来源位置','补充原始文件和位置')
  if q.get('source_verified') is not True and q.get('type') in {'单选题','多选题','判断题'}:add(q,'source_unmatched','medium','题目未与原始来源明确匹配','人工对照原始文件')
 for key,g in seen.items():
  if key[1] and len(g)>1:
   for q in g[1:]:add(q,'duplicate_stem','medium',f'与 {g[0]["id"]} 题干重复','核对是否重复题或不同选项版本')
 report=ROOT/'reports';report.mkdir(exist_ok=True);counts=Counter(x['kind'] for x in issues)
 (report/'question_bank_audit.json').write_text(json.dumps({'records':len(qs),'issues':issues,'issue_counts':dict(counts),'courses':dict(Counter(x.get('course') for x in qs))},ensure_ascii=False,indent=2)+'\n')
 lines=['# 题库质量审计报告','',f'- 扫描记录：{len(qs)}',f'- 问题总数：{len(issues)}','','## 问题分类','']+[f'- `{k}`：{n}' for k,n in counts.most_common()]+['','## 数据概况','', '| 科目 | 记录数 |','|---|---:|']+[f'| {c} | {n} |' for c,n in Counter(x.get('course') for x in qs).items()]+['','## 处理策略','','高置信度的答案标记污染、选项键顺序和完整性问题可由原始记录自动修复；疑似名词合并、题干截断、重复题和来源不匹配记录进入机器清单，需逐条对照原始 Word/PDF。','', '机器清单见 `reports/question_bank_audit.json`。']
 (report/'question_bank_audit.md').write_text('\n'.join(lines)+'\n');print(f'records={len(qs)} issues={len(issues)} categories={dict(counts)}')
if __name__=='__main__':main()
