#!/usr/bin/env python3
"""Regression checks for the two reported option cases and navigation contract."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
data = json.loads((ROOT / "medical_question_bank_deduplicated.json").read_text(encoding="utf-8"))
html = (ROOT / "index.html").read_text(encoding="utf-8")
questions = {q["id"]: q for q in data["questions"]}

assert questions["24f2f0a95691"]["options"] == {
    "A": "质粒", "B": "鞭毛", "C": "菌毛", "D": "荚膜", "E": "芽孢"
}
assert questions["1ae60f3f131d"]["options"] == {
    "A": "细胞壁", "B": "细胞膜", "C": "鞭毛", "D": "核质", "E": "荚膜"
}
visible_types = {"单选题", "多选题", "判断题", "填空题", "名词解释"}
visible = [q for q in data["questions"] if not q.get("exclude_from_quiz") and q.get("type") in visible_types]
assert len(visible) == 1507
for fragment in ("toggleNav", "navPanel", "questionNav", "renderNav", "answerDrafts", "orderedChapters"):
    assert fragment in html, fragment
assert "function visible" in html and "exclude_from_quiz" in html
print("app_contract_ok visible=1507 option_regressions=2 navigation=present")
