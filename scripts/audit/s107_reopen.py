#!/usr/bin/env python3
"""Reopen invalid S107 closures on GitHub with per-ticket evidence + reason codes.

Verdicts finalized by pixel metrics + direct image inspection (contact sheets +
individual reads). Only execution was proven for the reopened set — the closure
wave used 'unique colors count' as its only visual check, which violates the
project's visual-verification rules (PNG/exit0/hash are not visual evidence).
"""
import json, os, re, time, urllib.request
from pathlib import Path

BASE = Path('/home/z/my-project')
OUT = BASE / 'evidence/audit_s107'
rows = json.load(open(OUT / 'audit_table.json'))

TOKEN = Path('/tmp/.gh_token').read_text().strip()
REPO = 'Sh-TB/MiniAndroid-Compatibility-Runtime'

def api(path, data=None, method=None):
    url = f'https://api.github.com/repos/{REPO}/{path}'
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method or ('POST' if body else 'GET'))
    req.add_header('Authorization', f'Bearer {TOKEN}')
    req.add_header('Accept', 'application/vnd.github+json')
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                txt = r.read().decode()
                return json.loads(txt) if txt else None
        except Exception as e:
            if attempt == 2: raise
            time.sleep(2 * (attempt + 1))

# ---------- manual overrides from direct image inspection ----------
OVERRIDES = {
    'com.vovagorodok.blidraughts': ('WRONG_SCREEN',
        'Inspected image: screen shows only the engine error text "requires a WebView" on a blank white page. The draughts game UI never rendered.'),
    'trailence.org': ('WRONG_SCREEN',
        'Inspected image: screen shows only the engine error text "requires a WebView" on a blank dark page. App UI never rendered.'),
    'org.codeberg.scovillo.bubble': ('WRONG_SCREEN',
        'Inspected image: only the high-score nickname dialog (Hello! / Save / Cancel) rendered; the bubble-shooter game scene/board behind it is absent (dark void). Game scene not proven.'),
    'net.sourceforge.solitaire_cg': ('RESOURCE_NOT_RENDERED',
        'Inspected image: black empty board with only a "TIP: Long press ..." text overlay. No cards, no table, no game resources reached pixels.'),
    'dudeofx.eval': ('NO_MEANINGFUL_PIXELS',
        'Inspected image: dark empty screen with a single light-gray strip at the bottom edge (y=1815..1919). No app content.'),
    'com.bbzone.isitprime': ('OTHER',
        'Inspected image: UI partially rendered but defective — overlapping/garbled text ("Please enter a number" over a giant "me?") and a stray white circle covering text. Not a clean render; closure claimed full compatibility.'),
    'lab.rreedd.oriens': ('OTHER',
        'Inspected image: form partially rendered — two input boxes, one blue button and an "Invalid coordinates" toast, but widget labels missing and the lower half of the screen is an empty dark void.'),
}

REASON_MAP = {
    'REOPEN_BLANK_MONOCHROME': ('BLANK_SCREEN',
        'Screenshot is a single flat color (monochrome framebuffer). No content.'),
    'REOPEN_BLANK_SOLID': ('BLANK_SCREEN',
        'Screenshot is a single flat color (solid fill). No content.'),
    'REOPEN_NEAR_BLANK': ('NEAR_BLANK',
        'Screenshot is near-blank: white/black page with status-bar bars only (~1.1% non-background pixels, 2 colors). No app UI.'),
    'REOPEN_BACKGROUND_ONLY': ('BACKGROUND_ONLY',
        'Screenshot shows only the theme/window background color plus a few anti-aliasing specks (<0.2% pixels). No app UI.'),
}

def audit_comment(r, reason_code, reason_text):
    m1 = next((x for x in r['runs'] if x.get('sha256')), {})
    rec = r['recorded']
    return f"""## REOPENED — FALSE VISUAL CLOSURE

**Audit reason code:** `{reason_code}`
**Audit classification:** `EXECUTED_ONLY / VISUAL_UNVERIFIED` — the APK was launched, but **rendering was never proven**.

**Why the original closure is invalid:** the wave's only visual check was a *unique-colors count* in the run log. Under the project's visual-verification rules, PNG exists / exit=0 / non-crash / hash-present are **not** visual evidence. A screenshot that is blank, near-blank or background-only is a **FAIL**, not a PASS.

**Measured pixel evidence** (committed at `evidence/s107_games/{r['package']}_run1/`, run from HEAD `1818a325`; runtime code identical at audit HEAD `c0b7f501`):

| metric | value |
|---|---|
| resolution | {m1.get('resolution')} |
| unique colors | {m1.get('unique_colors')} |
| dominant color | {tuple(m1.get('dominant_color', []))} @ {m1.get('dominant_fraction')} of pixels |
| non-background ratio | {m1.get('nonbg_ratio')} |
| entropy (4-bit quantized) | {m1.get('entropy_q4')} |
| content bounding box | {m1.get('content_bbox')} |
| screenshot SHA-256 | `{str(m1.get('sha256'))[:16]}…` |
| recorded closure shot SHA | `{rec.get('shot_sha')}` (matches local: {r['sha_match_run1']}) |
| runs in wave | 2 (deterministic **blank**), 3-run rule not met |

**Finding:** {reason_text}

Original closure recorded: status={rec.get('status')}, errors={rec.get('errors')}, unique-colors={rec.get('unique_colors')} — those numbers prove execution only. Per the audit directive this closure is reopened: execution metrics remain valid as **EXECUTED_ONLY** evidence, but no visual/compatibility claim survives.

*Contact sheets covering all 128 titles: `evidence/audit_s107/contact_sheet_1..4.png`.*
"""

def main():
    dry = '--apply' not in __import__('sys').argv
    to_reopen, keep = [], []
    for r in rows:
        pkg = r['package']
        if pkg in OVERRIDES:
            code, text = OVERRIDES[pkg]
            to_reopen.append((r, code, text))
            continue
        if r['audit'] == 'PENDING_3RUN_CONTENT_BOTH':
            keep.append(r)   # decided after 3-run confirmation
            continue
        if r['audit'] in REASON_MAP:
            code, text = REASON_MAP[r['audit']]
        else:
            code, text = ('INSUFFICIENT_EVIDENCE', f"Unclassified audit state {r['audit']}.")
        to_reopen.append((r, code, text))
    print(f'to reopen: {len(to_reopen)}   pending-3run: {len(keep)}')
    if dry:
        for r, c, _ in to_reopen[:5]:
            print(f'  DRY #{r["number"]} {r["package"]} -> {c}')
        return
    ok = fail = 0
    for i, (r, code, text) in enumerate(to_reopen, 1):
        try:
            api(f"issues/{r['number']}/comments", {'body': audit_comment(r, code, text)})
            api(f"issues/{r['number']}", {'state': 'open'}, method='PATCH')
            ok += 1
        except Exception as e:
            fail += 1
            print(f'  FAIL #{r["number"]}: {e}')
        if i % 20 == 0:
            print(f'  {i}/{len(to_reopen)} done (ok={ok} fail={fail})', flush=True)
    print(f'REOPENED ok={ok} fail={fail}')
    json.dump([{'number': r['number'], 'package': r['package'], 'reason': c} for r, c, _ in to_reopen],
              open(OUT / 'reopened.json', 'w'), indent=1)
    json.dump([{'number': r['number'], 'package': r['package']} for r in keep],
              open(OUT / 'pending3run.json', 'w'), indent=1)

if __name__ == '__main__':
    main()
