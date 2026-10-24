#!/usr/bin/env python3
"""Conservatively repair option boundaries and preserve case relationships.

This script only uses text already present in each record's ``raw`` field.  It
never invents answers or chapter names.  Ambiguous records stay needs_review.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

OPTION_PATTERNS = [
    re.compile(r"(?<![A-Za-z-])([A-E])\s*[.．:：)]"),
    re.compile(r"(?:^|[\s])([A-E])\s*[、,，]"),
    re.compile(r"(?<=[\u4e00-\u9fff])([A-E])\s*[,，]"),
    re.compile(r"(?:^|[\s])([A-E])(?=[\u4e00-\u9fff])"),
]
ANSWER_RE = re.compile(r"(?:【\s*答案\s*】|答案\s*[:：]?)[\s]*([A-E](?:\s*[,、和及/]\s*[A-E])*)", re.I)
ANSWER_TAIL_RE = re.compile(r"(?:答案|参考答案|正确答案)\s*[:：]\s*[A-E]+.*$", re.I | re.S)
CASE_RE = re.compile(r"案例\s*(\d+)")


def parse_options(raw: str) -> dict[str, str] | None:
    """Return one complete A-E option set, or None when the text is ambiguous."""
    matches = []
    for pattern in OPTION_PATTERNS:
        for match in pattern.finditer(raw):
            label = match.group(1)
            start = match.start(1)
            if not any(existing[0] == start for existing in matches):
                matches.append((start, label, match.end()))
    matches.sort()
    if len(matches) != 5 or [m[1] for m in matches] != list("ABCDE"):
        return None
    options: dict[str, str] = {}
    for i, (start, label, end_marker) in enumerate(matches):
        end = matches[i + 1][0] if i + 1 < len(matches) else len(raw)
        value = raw[end_marker:end].strip(" \t\r\n;；")
        if not value or label in options:
            return None
        options[label] = value
    return options


def answer_from_raw(raw: str) -> str | None:
    match = ANSWER_RE.search(raw)
    if not match:
        return None
    return "".join(re.findall(r"[A-E]", match.group(1).upper())) or None


def paragraph_number(value: str) -> int:
    match = re.search(r"(\d+)", value or "")
    return int(match.group(1)) if match else 10**9


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} INPUT OUTPUT", file=sys.stderr)
        return 2
    source, destination = map(Path, sys.argv[1:])
    data = json.loads(source.read_text(encoding="utf-8"))
    questions = data.get("questions", data)
    repaired_options = 0
    repaired_types = 0
    inferred_answers = 0

    for question in questions:
        raw = str(question.get("raw") or "")
        answer_tail = ANSWER_TAIL_RE.search(raw)
        if answer_tail and not question.get("answer"):
            extracted = re.search(r"[A-E]+", answer_tail.group(0).upper())
            if extracted:
                question["answer"] = extracted.group(0)
        parsed = parse_options(raw)
        existing = question.get("options") or {}
        malformed = any(k not in "ABCDE" or not str(v).strip() or re.search(r"(?:^|\s)[A-E][.．、:：)]", str(v)) for k, v in existing.items())
        if parsed and (not existing or malformed or existing != parsed):
            question["options"] = parsed
            repaired_options += 1
        elif question.get("type") in {"单选题", "多选题"} and malformed:
            question["status"] = "needs_review"
            question["needs_review"] = True
            question["exclude_from_quiz"] = True
            question["needs_review_reason"] = "选项边界无法从原始记录唯一恢复，暂不进入刷题。"
        if parsed and question.get("type") == "未分类":
            question["type"] = "单选题"
            repaired_types += 1
        if parsed and not question.get("answer"):
            answer = answer_from_raw(raw)
            if answer:
                question["answer"] = answer
                inferred_answers += 1
        if question.get("source") == "案例分析.docx":
            # The source export is flattened. Keep every record review-only
            # until the original case document is available for verification.
            question["status"] = "needs_review"
            question["needs_review"] = True
            question["needs_review_reason"] = "原始案例文档未提供；病例背景与小题关联只能依据导出顺序保守分组。"
        if question.get("options"):
            cleaned = {}
            for label, value in question["options"].items():
                value = ANSWER_TAIL_RE.split(str(value), maxsplit=1)[0].strip()
                if value:
                    cleaned[label] = value
            question["options"] = cleaned
            question["options"] = {label: question["options"][label] for label in "ABCDE" if label in question["options"]}
        if question.get("type") in {"单选题", "多选题"} and set(question.get("options", {})) != set("ABCDE"):
            question["status"] = "needs_review"
            question["needs_review"] = True
            question["exclude_from_quiz"] = True
            question["needs_review_reason"] = "选择题缺少完整 A-E 选项，暂不进入刷题。"

        # A record marked ready must be safe for the browser's automatic
        # grader. Downgrade any incomplete/corrupted option set instead of
        # allowing a missing choice or shifted answer to be graded.
        if question.get("status") == "ready" and question.get("type") in {"单选题", "多选题", "判断题"}:
            labels = set((question.get("options") or {}).keys())
            answer = str(question.get("answer") or "").upper()
            if labels != set("ABCDE") or not answer or not set(answer) <= set("ABCDE"):
                question["status"] = "needs_review"
                question["needs_review"] = True
                question["needs_review_reason"] = "选项集合或答案标记不完整，待原始题库核对后再自动判分。"

    # Assign conservative case groups by source paragraph order. A record that
    # contains a transition can belong to the current case while listing all
    # case markers visible in its raw text for later source-level recovery.
    case_questions = sorted(
        (q for q in questions if q.get("source") == "案例分析.docx"),
        key=lambda q: paragraph_number(q.get("source_location", "")),
    )
    current_case = 1
    for question in case_questions:
        markers = [int(n) for n in CASE_RE.findall(str(question.get("raw") or ""))]
        ids = [current_case]
        for marker in markers:
            if marker not in ids:
                ids.append(marker)
        question["case_id"] = f"case-{current_case}"
        question["case_ids_in_raw"] = [f"case-{n}" for n in ids]
        question["case_group_source"] = "案例分析.docx 导出段落顺序"
        if markers:
            current_case = markers[-1]
            if current_case not in ids:
                ids.append(current_case)

    if isinstance(data, dict):
        data["version"] = "0.3-conservative-repair"
        summary = data.setdefault("summary", {})
        summary["repair_notes"] = [
            "选项仅在 raw 中存在唯一完整 A-E 选项集时重建。",
            "案例分析原始文档未随仓库提供；案例记录保留 needs_review 并按导出段落建立保守 case_id。",
            "未分章/未分类章节未依据关键词猜测。",
        ]
        summary["repaired_option_sets"] = repaired_options
        summary["repaired_question_types"] = repaired_types
        summary["inferred_answers"] = inferred_answers
    destination.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"repaired_options={repaired_options} repaired_types={repaired_types} inferred_answers={inferred_answers}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
