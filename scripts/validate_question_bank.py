#!/usr/bin/env python3
"""Integrity checks for the question-bank invariants used by index.html."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

LABELS = set("ABCDE")
OPTION_MARKER = re.compile(r"\s[A-E][.．、:：)]")
GRADEABLE = {"单选题", "多选题", "判断题"}


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("medical_question_bank_deduplicated.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    questions = data["questions"]
    errors: list[str] = []
    ids: set[str] = set()
    for i, q in enumerate(questions):
        prefix = f"questions[{i}]/{q.get('id', '?')}"
        if q.get("id") in ids:
            errors.append(f"{prefix}: duplicate id")
        ids.add(q.get("id"))
        options = q.get("options") or {}
        if not set(options) <= LABELS:
            errors.append(f"{prefix}: invalid option label")
        for label, value in options.items():
            if not str(value).strip() or OPTION_MARKER.search(str(value)):
                errors.append(f"{prefix}: option {label} is empty or contains another option marker")
        if q.get("status") == "ready" and q.get("type") in GRADEABLE:
            if set(options) != LABELS:
                errors.append(f"{prefix}: ready gradeable question must have A-E options")
            answer = str(q.get("answer") or "").upper()
            if not answer or not set(answer) <= LABELS:
                errors.append(f"{prefix}: ready gradeable question has invalid answer")
        if q.get("source") == "案例分析.docx":
            if not q.get("case_id") or q.get("status") != "needs_review" or q.get("needs_review") is not True:
                errors.append(f"{prefix}: case records must retain case_id and needs_review")
        if q.get("chapter") in (None, ""):
            errors.append(f"{prefix}: missing chapter value")
        if q.get("chapter") in ("未分章", "未分类") and q.get("needs_review") is not True:
            # Existing non-case records retain their source label; they must be
            # review-only when no chapter source is available.
            errors.append(f"{prefix}: unresolved chapter must be marked needs_review")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"validated {len(questions)} questions; option, answer, case, and chapter invariants passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
