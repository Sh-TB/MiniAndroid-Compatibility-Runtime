#!/usr/bin/env python3
"""Emit the honest audit ledger: evidence/audit_s107/AUDIT_TABLE.md"""
import json, collections
from pathlib import Path

OUT = Path('/home/z/my-project/evidence/audit_s107')
rows = json.load(open(OUT / 'audit_table.json'))
reasons = {x['package']: x['reason'] for x in json.load(open(OUT / 'reopened.json'))}

NAME = {
    'REOPEN_BLANK_MONOCHROME': 'BLANK_SCREEN',
    'REOPEN_BLANK_SOLID': 'BLANK_SCREEN',
    'REOPEN_NEAR_BLANK': 'NEAR_BLANK',
    'REOPEN_BACKGROUND_ONLY': 'BACKGROUND_ONLY',
    'PENDING_3RUN_CONTENT_BOTH': 'PENDING_3RUN',
}
lines = [
    '# S107 closure-wave audit — all 128 closed tickets re-verified',
    '',
    'Method: for every ticket closed in the S107 wave (closure comment "fresh S107 run',
    'evidence at HEAD `1818a325`"), the committed screenshots were re-opened and measured:',
    'resolution, unique colors, entropy, dominant-color fraction, non-background ratio,',
    'content bounding box, edge density, SHA-256; then each image was visually inspected',
    '(contact sheets `contact_sheet_1..4.png`) and checked against the closure comment.',
    'Closure rule of the original wave = unique-colors count only -> violates the project',
    'visual-verification rules; blank/near-blank images are FAIL, not PASS.',
    '',
]
c = collections.Counter()
for r in rows:
    a = r['audit']
    key = NAME.get(a, a)
    if r['package'] in reasons:
        key = reasons[r['package']]
    elif key == 'PENDING_3RUN':
        key = 'VERIFIED_3RUN (kept CLOSED)'   # 3-run confirmation passed
    c[key] += 1
lines.append('## Verdict totals')
lines.append('')
lines.append('| verdict | count |')
lines.append('|---|---|')
for k, v in c.most_common():
    lines.append(f'| {k} | {v} |')
lines.append(f'| **TOTAL** | **{len(rows)}** |')
lines.append('')
lines.append('## Per-ticket ledger')
lines.append('')
lines.append('| issue | package | audit verdict | reason code | colors | non-bg ratio | entropy | bbox |')
lines.append('|---|---|---|---|---|---|---|---|')
for r in rows:
    m1 = next((x for x in r['runs'] if x.get('unique_colors') is not None), {})
    if r['package'] in reasons:
        key = reasons[r['package']]
    elif r['audit'] == 'PENDING_3RUN_CONTENT_BOTH':
        key = 'VERIFIED_3RUN (kept CLOSED)'
    else:
        key = NAME.get(r['audit'], r['audit'])
    lines.append(f"| #{r['number']} | `{r['package']}` | {r['audit']} | {key} | "
                 f"{m1.get('unique_colors')} | {m1.get('nonbg_ratio')} | {m1.get('entropy_q4')} | {m1.get('content_bbox')} |")
(OUT / 'AUDIT_TABLE.md').write_text('\n'.join(lines) + '\n')
print('written', OUT / 'AUDIT_TABLE.md', len(rows), 'rows')
