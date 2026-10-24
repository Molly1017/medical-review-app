#!/usr/bin/env python3
import json,re
from pathlib import Path
D=json.loads(Path('medical_question_bank_deduplicated.json').read_text());issues=json.loads(Path('reports/question_bank_audit.json').read_text())
assert issues['records']==len(D['questions'])
marker=re.compile(r'(?:答案|参考答案|正确答案)\s*[:：]',re.I)
choices=[q for q in D['questions'] if q.get('type') in {'单选题','多选题'}]
assert not any(marker.search(str(v)) for q in choices for v in (q.get('options') or {}).values())
assert Path('reports/question_bank_audit.md').exists()
print('audit_contract_ok records=%d choices=%d issues=%d'%(len(D['questions']),len(choices),len(issues['issues'])))
