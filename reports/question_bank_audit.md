# 题库质量审计报告

- 扫描记录：2071
- 问题总数：168

## 问题分类

- `source_unmatched`：97
- `option_incomplete`：31
- `answer_outside_options`：15
- `next_question_in_option`：13
- `duplicate_stem`：10
- `term_merge_suspected`：2

## 数据概况

| 科目 | 记录数 |
|---|---:|
| 医学免疫学 | 1157 |
| 医学细胞生物学 | 112 |
| 医学微生物学 | 802 |

## 处理策略

高置信度的答案标记污染、选项键顺序和完整性问题可由原始记录自动修复；疑似名词合并、题干截断、重复题和来源不匹配记录进入机器清单，需逐条对照原始 Word/PDF。

机器清单见 `reports/question_bank_audit.json`。

## 原始资料清单

本次审计使用仓库已导入记录及当前任务提供的原始资料：`医学免疫学题库.docx`、`医学细胞生物学题库B.docx`、`医学微生物学题库.docx`、`案例分析.docx`、`名词解释.pdf`、`判断题.pdf`。原始文件不写入仓库，题目记录保留 `source`、`source_location` 和 `source_occurrences`。
