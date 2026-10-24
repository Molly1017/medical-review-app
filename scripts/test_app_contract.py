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
assert questions["6058b28d01d2"]["answer"] == "D"
assert questions["6058b28d01d2"]["options"]["D"] == "内毒素"
assert questions["6058b28d01d2"]["answer_source"] == "original_source"
promoted = data.get("summary", {}).get("promoted_to_ready", [])
assert promoted
for question_id in promoted:
    q = questions[question_id]
    assert q["status"] == "ready"
    assert q.get("answer_source") == "original_source"
    assert q.get("answer_match_method")
    assert q.get("review_resolution")
print("status_transitions_checked", len(promoted))
visible_types = {"单选题", "多选题", "判断题", "填空题", "名词解释"}
visible = [q for q in data["questions"] if not q.get("exclude_from_quiz") and q.get("type") in visible_types]
assert len(visible) == 1530
for fragment in ("toggleNav", "navPanel", "questionNav", "renderNav", "answerDrafts", "orderedChapters"):
    assert fragment in html, fragment
assert "function visible" in html and "exclude_from_quiz" in html
assert all(q.get("explanation_detail") for q in data["questions"] if q.get("course") == "医学微生物学" and q.get("chapter") == "第一章 细菌的形态与结构" and q.get("status") in {"ready", "externally_verified_correction"})
assert all(q.get("exclude_from_quiz") for q in data["questions"] if q.get("id") in {"2b4bae214de8", "561a3535afc3", "9603bca9c2cf", "fac8ba2f0f3d", "70c1245e1510", "e0aa89dd20f9"})
print("app_contract_ok visible=1530 option_regressions=2 navigation=present")
explained = [q for q in data['questions'] if q.get('explanation_detail')]
assert len(explained) >= 13
assert all(q['explanation_detail']['source']['kind'] in {'original_source_derived','generated_reference'} for q in explained)
for fragment in ('detailsToggle', 'explanationCard'):
    assert fragment in html, fragment
for field in ('correct_answer_reason', 'plain_explanation', 'option_analysis', 'clinical_connection', 'exam_focus'):
    assert all(field in q['explanation_detail'] for q in explained)
print('explanation_contract_ok generated='+str(len(explained)))
terms = [q for q in data['questions'] if q.get('type') == '名词解释']
assert len(terms) == 278
assert sum(bool(q.get('answer')) for q in terms) == 160
assert sum(q.get('answer_source') == 'generated_reference' for q in terms) == 47
assert 'reference_answer' in html or 'answerText(q)' in html
print('term_contract_ok total=278 original=160 generated=47 pending=71')
