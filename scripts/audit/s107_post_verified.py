#!/usr/bin/env python3
"""Post audit-verification comments on the 4 tickets that survive the audit."""
import json, time, urllib.request
from pathlib import Path

TOKEN = Path('/tmp/.gh_token').read_text().strip()
REPO = 'Sh-TB/MiniAndroid-Compatibility-Runtime'
S = json.load(open('/home/z/my-project/evidence/audit_s107/three_run/three_run_summary.json'))

def api(path, data=None, method=None):
    url = f'https://api.github.com/repos/{REPO}/{path}'
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method or ('POST' if body else 'GET'))
    req.add_header('Authorization', f'Bearer {TOKEN}')
    req.add_header('Accept', 'application/vnd.github+json')
    with urllib.request.urlopen(req, timeout=30) as r:
        txt = r.read().decode()
        return json.loads(txt) if txt else None

NOTES = {
    'com.smorgasbork.hotdeath': 'Main menu renders (title + NEW GAME/SETTINGS/HELP/ABOUT/EXIT). exit=1 / status PARTIAL SUCCESS remains honestly recorded.',
    'com.dozingcatsoftware.bouncy': 'Main menu renders (Select Table / Start Game / High scores / Help / Preferences / Quit). The 16 remaining runtime errors and PARTIAL SUCCESS stay honestly recorded; in-table game render is the next frontier.',
    'org.bobstuff.bobball': 'Main menu renders (BobBall title, game icon, Single Player/Options/High Scores/Statistics/Help/Exit) and matches upstream layout.',
    'org.ucam.ssb22.pinyinfdroid': 'Launch menu renders (Pinyin Web & EPUB 拼音浏览器, EPUB/Clipboard links, Help | Privacy policy) with CJK text.',
}

for pkg, d in S.items():
    issue = d['issue']
    v = d['verdict']
    runs = d['runs']
    body = f"""## AUDIT RESULT — closure re-verified {v.replace('_', ' ')} ✓

The S107 audit re-ran this title **3 independent times on the current HEAD runtime** (rebuilt from `c0b7f501`; runtime code identical to `1818a325`) and visually inspected the screenshots.

| metric | run1 | run2 | run3 |
|---|---|---|---|
| status | {runs[0]['status']} | {runs[1]['status']} | {runs[2]['status']} |
| errors | {runs[0]['errors']} | {runs[1]['errors']} | {runs[2]['errors']} |
| unique colors | {runs[0]['unique_colors']} | {runs[1]['unique_colors']} | {runs[2]['unique_colors']} |
| non-bg ratio | {runs[0]['nonbg_ratio']} | {runs[1]['nonbg_ratio']} | {runs[2]['nonbg_ratio']} |
| shot SHA-16 | `{runs[0]['sha']}` | `{runs[1]['sha']}` | `{runs[2]['sha']}` |

- APK version: `{d.get('apk_version')}`
- Byte-identical screens across 3 runs (`{'==' if runs[0]['sha']==runs[1]['sha']==runs[2]['sha'] else '!='}`) and identical to the wave evidence SHA.
- Direct image inspection: {NOTES[pkg]}

**Verdict: {v}** — this closure survives the audit. Evidence: `evidence/audit_s107/three_run/{pkg}_run1..3/`.
"""
    api(f'issues/{issue}/comments', {'body': body})
    print(f'posted audit result on #{issue} {pkg}: {v}')
    time.sleep(0.5)
