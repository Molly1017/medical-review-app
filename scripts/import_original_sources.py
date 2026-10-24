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
INLINE_ANSWER_RE = re.compile(r"(?:答案|参考答案)\s*[:：;；]?\s*([A-E]+|正确|错误)", re.I)


def clean(value: str) -> str:
    return re.sub(r"\s+", "", value or "").replace("．", ".")


def load_paragraphs(path: Path) -> list[str]:
    return [p.text.strip() for p in Document(path).paragraphs]


def extract_chapter(text: str) -> str | None:
    lines = (text or "").splitlines()
    if not lines:
        return None
    first = lines[0].strip()
    if not CHAPTER_RE.match(first) or "_" in first or len(first) > 60:
        return None
    return first


def source_context(path: Path) -> list[tuple[int, str, str | None, str | None]]:
    """Return paragraph index/text/current chapter/current type."""
    rows = load_paragraphs(path)
    chapter = None
    kind = None
    out = []
    for i, text in enumerate(rows):
        found_chapter = extract_chapter(text)
        if found_chapter:
            chapter = found_chapter
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


def chapter_order(path: Path) -> list[str]:
    seen: list[str] = []
    for text in load_paragraphs(path):
        found = extract_chapter(text)
        if found and found not in seen:
            seen.append(found)
    return seen


def micro_choice_answers(path: Path) -> dict[int, str]:
    answers: dict[int, str] = {}
    for text in load_paragraphs(path):
        for match in re.finditer(r"(\d+)\s*[-~～]\s*(\d+)\s*([A-E]+)", text, re.I):
            start, end, letters = int(match.group(1)), int(match.group(2)), match.group(3).upper()
            if len(letters) == end - start + 1:
                answers.update({start + i: letter for i, letter in enumerate(letters)})
    return answers


def question_number_near(rows: list[str], paragraph: int) -> int | None:
    for i in range(min(paragraph, len(rows) - 1), max(-1, paragraph - 4), -1):
        numbers = re.findall(r"(?:^|\n)\s*(\d+)\s*[.、)]", rows[i])
        if numbers:
            return int(numbers[-1])
    return None


def answer_letters(value: object) -> str:
    return "".join(re.findall(r"[A-E]", str(value or "").upper()))


def reliable_gradeable_record(q: dict) -> bool:
    if not str(q.get("question") or "").strip() or len(str(q.get("question") or "").strip()) < 5:
        return False
    if q.get("type") == "判断题":
        return str(q.get("answer")) in {"正确", "错误"} and q.get("answer_source") == "original_source"
    options = q.get("options") or {}
    if set(options) != set("ABCDE") or any(not str(v).strip() or len(str(v).strip()) < 1 for v in options.values()):
        return False
    answer = answer_letters(q.get("answer"))
    if not answer or not set(answer) <= set(options):
        return False
    if q.get("type") == "多选题" and len(set(answer)) < 2:
        return False
    return q.get("answer_source") == "original_source" and bool(q.get("answer_match_method"))


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
        text = rows[i][1]
        q["source_verified"] = True
        q["source_paragraph"] = i + 1
        if chapter:
            q["chapter"] = chapter
        if kind and q.get("type") in {None, "未分类"}:
            q["type"] = kind
        answer_match = INLINE_ANSWER_RE.search(text)
        if answer_match and q.get("type") in {"单选题", "多选题", "判断题"}:
            answer = answer_match.group(1).upper()
            if q.get("answer") in (None, "", answer):
                q["answer"] = answer
                q["answer_source"] = "original_source"
                q["answer_source_file"] = path.name
                q["answer_source_location"] = f"段落 {i + 1}"
                q["answer_match_method"] = "same_source_paragraph"
                q["source_verified"] = True


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
        case_content = case_rows[1:]
        for row_pos, (idx, text) in enumerate(case_content):
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
            if current is None and not answer_section:
                next_text = next((t for _, t in case_content[row_pos + 1 :] if t), "")
                if OPTION_RE.match(next_text):
                    current = {"number": len(subquestions) + 1, "stem": text, "options": {}, "answer": None, "source_paragraph": idx + 1}
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
        answer_matching = [s for s in case["subquestions"] if s.get("answer_text") and clean(q["question"]) in clean(s["answer_text"])]
        if answer_matching:
            # The previous export emitted answer paragraphs as records. Keep
            # their text for traceability, but never present them as questions.
            answer_sub = answer_matching[0]
            q["record_role"] = "answer_fragment"
            q["exclude_from_quiz"] = True
            q["answer_fragment_for"] = answer_sub["number"]
            q["needs_review"] = True
            q["needs_review_reason"] = "原始文档中的答案/解析段落，已归入对应病例小题。"
            q["status"] = "needs_review"
            continue
        if matching:
            sub = matching[0]
            q["case_subquestion"] = sub["number"]
            if set(sub["options"]) == set("ABCDE"):
                q["options"] = sub["options"]
                q["type"] = "单选题"
                if sub.get("answer"):
                    q["answer"] = sub["answer"]
                    q["answer_source"] = "original_source"
                    q["answer_source_file"] = path.name
                    q["answer_source_location"] = f"段落 {sub['source_paragraph']}"
                    q["answer_match_method"] = "case_subquestion_answer"
                    q["status"] = "ready"
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
    chapter_orders = data.setdefault("chapter_order", {})
    if args.immune:
        apply_source_context(questions, args.immune, "医学免疫学题库.docx")
        chapter_orders["医学免疫学"] = chapter_order(args.immune)
    if args.cell:
        apply_source_context(questions, args.cell, "医学细胞生物学题库B.docx")
        chapter_orders["医学细胞生物学"] = chapter_order(args.cell)
    promoted: list[str] = []
    if args.micro:
        apply_source_context(questions, args.micro, "医学微生物学题库.docx")
        chapter_orders["医学微生物学"] = chapter_order(args.micro)
        micro_answers = micro_choice_answers(args.micro)
        micro_rows = load_paragraphs(args.micro)
        for q in questions:
            if q.get("source") != "医学微生物学题库.docx" or q.get("type") not in {"单选题", "多选题"}:
                continue
            paragraph = int(q.get("source_paragraph", 1)) - 1
            number = question_number_near(micro_rows, paragraph)
            answer = micro_answers.get(number)
            if answer and q.get("answer") and answer_letters(q["answer"]) != answer:
                q["answer_conflict"] = True
                q["status"] = "needs_review"
                q["needs_review"] = True
                q["needs_review_reason"] = "原始答案表与当前答案不一致，待人工核对。"
            elif answer:
                q["answer"] = answer
                q["answer_source"] = "original_source"
                q["answer_source_file"] = args.micro.name
                q["answer_source_location"] = f"答案表题号 {number}"
                q["answer_match_method"] = "micro_answer_table_question_number"
    if args.cases:
        cases, ranges = parse_cases(args.cases)
        map_case_records(questions, cases, ranges, args.cases)
        data["cases"] = cases
        data["summary"]["original_case_source"] = args.cases.name
        data["summary"]["case_records_imported"] = len(cases)
    for q in questions:
        occurrences = q.get("source_occurrences") or []
        original_answers = {str(o.get("original_answer")) for o in occurrences if o.get("original_answer")}
        if q.get("answer") and original_answers and str(q["answer"]) in original_answers and len(original_answers) == 1:
            q["answer_source"] = "original_source"
            q["answer_source_file"] = q.get("source")
            q["answer_source_location"] = q.get("source_location")
            q["answer_match_method"] = "source_occurrence_exact"
        if q.get("options"):
            q["options"] = {label: q["options"][label] for label in "ABCDE" if label in q["options"]}
        if q.get("answer_source") == "original_source" and q.get("type") in {"单选题", "多选题", "判断题"} and reliable_gradeable_record(q):
            previous_status = q.get("status")
            q["status"] = "ready"
            q["needs_review"] = False
            q["review_resolution"] = f"由 {q.get('answer_match_method')} 核实；原状态 {previous_status}"
            promoted.append(q["id"])
    for q in questions:
        if q.get("type") == "判断题" and q.get("source") == "判断题.pdf":
            answers = {str(o.get("original_answer")) for o in q.get("source_occurrences", []) if o.get("original_answer")}
            if str(q.get("answer")) in {"正确", "错误"} and answers <= {str(q.get("answer"))}:
                q["status"] = "ready"
                q["answer_source"] = "original_source"
                q["answer_match_method"] = "source_occurrence_exact"
                q["needs_review"] = False
                q["review_resolution"] = "由判断题 PDF 原始答案核实"
                promoted.append(q["id"])
    data["version"] = "0.4-original-source-import"
    data["summary"]["promoted_to_ready"] = sorted(set(promoted))
    data["summary"].setdefault("repair_notes", []).append("已根据用户提供的原始 Word 文档恢复章节、病例背景及小题索引；无法解析的记录仍需审核。")
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"questions={len(questions)} cases={len(data.get('cases', {}))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
