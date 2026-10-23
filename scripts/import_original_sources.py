#!/usr/bin/env python3
"""Import structure that is explicitly present in the supplied source files.

The generated question bank keeps the existing IDs and raw text.  It adds
verified chapter/type metadata and a case index; it does not synthesize text.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from docx import Document

CHAPTER_RE = re.compile(r"^第[一二三四五六七八九十百零〇两\d]+章\s*.*")
NUM_RE = re.compile(r"^\s*(\d+)\s*[.．、)]\s*(.*)$")
OPTION_RE = re.compile(r"^\s*([A-E])\s*[.．、:：)]\s*(.*)$")
CASE_RE = re.compile(r"^案例\s*(\d+)\s*$")
ANSWER_RE = re.compile(r"【答案】\s*([A-E]+)")


def clean(value: str) -> str:
    return re.sub(r"\s+", "", value or "").replace("．", ".")


def load_paragraphs(path: Path) -> list[str]:
    return [p.text.strip() for p in Document(path).paragraphs]


def source_context(path: Path) -> list[tuple[int, str, str | None, str | None]]:
    """Return paragraph index/text/current chapter/current type."""
    rows = load_paragraphs(path)
    chapter = None
    kind = None
    out = []
    for i, text in enumerate(rows):
        if CHAPTER_RE.match(text):
            chapter = text
        if re.search(r"名词解释", text):
            kind = "名词解释"
        elif re.search(r"填空题", text):
            kind = "填空题"
        elif re.search(r"判断题", text):
            kind = "判断题"
        elif re.search(r"问答题|简答题|思考问答题", text):
            kind = "问答题"
        elif re.search(r"配伍题", text):
            kind = "配伍题"
        elif re.search(r"多选题", text):
            kind = "多选题"
        elif re.search(r"单选题|选择题|A1型题|A2型题|B1型题", text):
            kind = "单选题"
        out.append((i, text, chapter, kind))
    return out


def apply_source_context(questions: list[dict], path: Path, source_name: str) -> None:
    rows = source_context(path)
    for q in questions:
        if q.get("source") != source_name or not q.get("question"):
            continue
        needle = clean(str(q["question"]))
        candidates = [(i, chapter, kind) for i, text, chapter, kind in rows if needle and needle in clean(text)]
        if not candidates:
            continue
        loc_match = re.search(r"(\d+)", str(q.get("source_location", "")))
        target = int(loc_match.group(1)) if loc_match else 0
        i, chapter, kind = min(candidates, key=lambda x: abs(x[0] - target))
        q["source_verified"] = True
        q["source_paragraph"] = i + 1
        if chapter:
            q["chapter"] = chapter
        if kind and q.get("type") in {None, "未分类"}:
            q["type"] = kind


def parse_cases(path: Path) -> tuple[dict[str, dict], dict[int, tuple[int, int]]]:
    rows = load_paragraphs(path)
    starts: list[tuple[int, int]] = []
    for i, text in enumerate(rows):
        m = CASE_RE.match(text)
        if m:
            starts.append((int(m.group(1)), i))
    cases: dict[str, dict] = {}
    ranges: dict[int, tuple[int, int]] = {}
    for pos, (number, start) in enumerate(starts):
        end = starts[pos + 1][1] if pos + 1 < len(starts) else len(rows)
        ranges[number] = (start, end)
        case_rows = [(i, t) for i, t in enumerate(rows[start:end], start)]
        problem_at = next((j for j, (_, t) in enumerate(case_rows) if "【问题】" in t), None)
        background_rows = case_rows[1 : problem_at if problem_at is not None else len(case_rows)]
        background = "\n".join(t for _, t in background_rows if t and not t.startswith("【答案"))
        subquestions: list[dict] = []
        current: dict | None = None
        seen_question = False
        answer_section = False
        for idx, text in case_rows[1:]:
            if not text or text.startswith("【案例介绍】") or text.startswith("【案例分析】"):
                continue
            if text.startswith("【答案解析】"):
                answer_section = True
                continue
            if text.startswith("【问题】"):
                body = text.split("】", 1)[1].strip()
                if body:
                    current = {"number": len(subquestions) + 1, "stem": body, "options": {}, "answer": None, "source_paragraph": idx + 1}
                    subquestions.append(current)
                    seen_question = True
                continue
            answer = ANSWER_RE.search(text)
            if answer and current is not None:
                current["answer"] = answer.group(1).upper()
                continue
            if answer_section:
                m = NUM_RE.match(text)
                if m and subquestions:
                    n = int(m.group(1))
                    target = next((x for x in subquestions if x["number"] == n), subquestions[-1])
                    target["answer_text"] = m.group(2).strip()
                elif current is not None and text:
                    current["answer_text"] = (current.get("answer_text", "") + "\n" + text).strip()
                continue
            option = OPTION_RE.match(text)
            if option and current is not None:
                current["options"][option.group(1)] = option.group(2).strip()
                continue
            number_match = NUM_RE.match(text)
            # Some cases (for example cases 3–4 and 6 onward) start numbered
            # questions directly after the clinical background without a
            # separate 【问题】 paragraph.
            if number_match and not answer_section:
                current = {"number": int(number_match.group(1)), "stem": number_match.group(2).strip(), "options": {}, "answer": None, "source_paragraph": idx + 1}
                subquestions.append(current)
                seen_question = True
                continue
            if current is not None and not text.startswith("【"):
                current["stem"] = (current["stem"] + " " + text).strip()
        cases[f"case-{number}"] = {
            "case_id": f"case-{number}",
            "title": f"案例{number}",
            "background": background,
            "subquestions": subquestions,
            "source": path.name,
            "source_range": [start + 1, end],
        }
    return cases, ranges


def map_case_records(questions: list[dict], cases: dict[str, dict], ranges: dict[int, tuple[int, int]], path: Path) -> None:
    rows = load_paragraphs(path)
    for q in questions:
        if q.get("source") != "案例分析.docx" or not q.get("question"):
            continue
        needle = clean(str(q["question"]))
        candidates = [(i, number) for number, (start, end) in ranges.items() for i in range(start, end) if needle and needle in clean(rows[i])]
        if not candidates:
            continue
        loc_match = re.search(r"(\d+)", str(q.get("source_location", "")))
        target = int(loc_match.group(1)) if loc_match else 0
        paragraph, number = min(candidates, key=lambda x: abs(x[0] - target - 5))
        case = cases[f"case-{number}"]
        q["case_id"] = f"case-{number}"
        q["case_group_source"] = path.name
        q["source_verified"] = True
        q["source_paragraph"] = paragraph + 1
        matching = [s for s in case["subquestions"] if clean(s["stem"]) in clean(q["question"]) or clean(q["question"]) in clean(s["stem"])]
        if matching:
            sub = matching[0]
            q["case_subquestion"] = sub["number"]
            if set(sub["options"]) == set("ABCDE"):
                q["options"] = sub["options"]
                q["type"] = "单选题"
                if sub.get("answer"):
                    q["answer"] = sub["answer"]
                    q["status"] = "ready"
                    q.pop("needs_review", None)
                    q.pop("needs_review_reason", None)
            elif not sub["options"]:
                q["type"] = "问答题"
                q["status"] = "needs_review"
                q["needs_review"] = True
                q["needs_review_reason"] = "原始案例题为开放问答，浏览器不自动判分。"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--immune", type=Path)
    parser.add_argument("--cell", type=Path)
    parser.add_argument("--micro", type=Path)
    parser.add_argument("--cases", type=Path)
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    questions = data["questions"]
    if args.immune:
        apply_source_context(questions, args.immune, "医学免疫学题库.docx")
    if args.cell:
        apply_source_context(questions, args.cell, "医学细胞生物学题库B.docx")
    if args.micro:
        apply_source_context(questions, args.micro, "医学微生物学题库.docx")
    if args.cases:
        cases, ranges = parse_cases(args.cases)
        map_case_records(questions, cases, ranges, args.cases)
        data["cases"] = cases
        data["summary"]["original_case_source"] = args.cases.name
        data["summary"]["case_records_imported"] = len(cases)
    data["version"] = "0.4-original-source-import"
    data["summary"].setdefault("repair_notes", []).append("已根据用户提供的原始 Word 文档恢复章节、病例背景及小题索引；无法解析的记录仍需审核。")
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"questions={len(questions)} cases={len(data.get('cases', {}))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
