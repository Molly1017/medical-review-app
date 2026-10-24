#!/usr/bin/env python3
"""Recover cell-biology questions omitted by the paragraph-to-record import."""
from __future__ import annotations
import hashlib, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from repair_question_bank import parse_options

ANSWER = re.compile(r"答案\s*[:：]\s*([A-E]+)")
OPTION_START = re.compile(r"(?<![A-Za-z-])A\s*[.．:：)]")
NUM = re.compile(r"^\s*\d+\s+")

def parse_cell_options(raw: str) -> dict[str, str] | None:
    matches = list(re.finditer(r"(?<![A-Za-z-])([A-E])\s*[.．:：)]", raw))
    chosen = []; expected = "A"
    for m in matches:
        if m.group(1) == expected:
            chosen.append(m)
            expected = chr(ord(expected) + 1)
            if expected > "E": break
    if len(chosen) != 5: return None
    return {m.group(1): raw[m.end():(chosen[i + 1].start() if i + 1 < 5 else len(raw))].strip() for i, m in enumerate(chosen)}

def main() -> int:
    from docx import Document
    source = Path(sys.argv[1]); target = Path(sys.argv[2])
    data = json.loads(target.read_text(encoding="utf-8"))
    existing = {q["id"] for q in data["questions"]}
    doc = Document(source)
    chapter = None; kind = None; added = []
    for i, paragraph in enumerate(doc.paragraphs):
        raw = paragraph.text.strip()
        if not raw: continue
        if raw.startswith("第一章 绪论"): chapter = raw
        elif raw.startswith("第二章 细胞基本概念与分子基础"): chapter = raw
        elif raw.startswith("第四章 "): break
        if "（一）单选题" in raw: kind = "单选题"; continue
        if "（二）多选题" in raw: kind = "多选题"; continue
        if kind not in {"单选题", "多选题"} or "答案" not in raw or not OPTION_START.search(raw): continue
        answer_match = ANSWER.search(raw)
        if not answer_match: continue
        answer = answer_match.group(1).upper()
        option_text = raw[:answer_match.start()].strip()
        options = parse_cell_options(option_text)
        if not options or set(options) != set("ABCDE"): continue
        first = OPTION_START.search(option_text)
        stem = option_text[:first.start()].strip() if first else ""
        stem = NUM.sub("", stem).strip()
        if not stem: continue
        qid = hashlib.sha1((source.name + "|" + chapter + "|" + stem).encode()).hexdigest()[:12]
        if qid in existing: continue
        q = {"id": qid, "course": "医学细胞生物学", "chapter": chapter, "type": kind, "question": stem, "options": {k: options[k] for k in "ABCDE"}, "answer": answer, "explanation": None, "source": source.name, "source_location": f"段落 {i + 1}", "status": "ready", "raw": raw, "source_occurrences": [{"id": qid, "file": source.name, "location": f"段落 {i + 1}", "original_answer": answer}], "source_verified": True, "source_paragraph": i + 1, "answer_source": "original_source", "answer_source_file": source.name, "answer_source_location": f"段落 {i + 1}", "answer_match_method": "same_source_paragraph"}
        data["questions"].append(q); existing.add(qid); added.append(q)
    summary = data.setdefault("summary", {})
    previous = list(summary.get("cell_missing_question_ids", []))
    recovered_now = [q["id"] for q in data["questions"] if q.get("source") == source.name and q.get("chapter") in {"第一章 绪论", "第二章 细胞基本概念与分子基础"}]
    summary["cell_missing_question_ids"] = sorted(set(previous + recovered_now + [q["id"] for q in added]))
    summary["cell_missing_questions_recovered"] = len(summary["cell_missing_question_ids"])
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"added={len(added)} chapters={sorted({q['chapter'] for q in added})}")
    return 0
if __name__ == "__main__": raise SystemExit(main())
