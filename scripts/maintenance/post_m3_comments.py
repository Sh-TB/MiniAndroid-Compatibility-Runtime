#!/usr/bin/env python3
"""scripts/maintenance/post_m3_comments.py — MASTER CAMPAIGN 3 evidence publication (Rule 0.2).

Posts the M3 evidence comments to Issue #8 and appends the API-verified
direct URLs to scripts/maintenance/comment_urls.json. Requires /home/z/.gh_token.
Usage: python3 scripts/maintenance/post_m3_comments.py
"""
import json
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TOKEN_FILE = "/home/z/.gh_token"
ISSUE = 8
URLS_JSON = REPO / "scripts" / "comment_urls.json"

COMMENTS = [
    ("M3 baseline+frontier", """**MASTER CAMPAIGN 3 — §1 BASELINE + §2 FRONTIER (base c0f178a7)**

Env: restored from scratch (g++ 14.2.0, aapt2 2.20-14304508); 22 frozen APKs SHA-verified (15 base + 6 master_campaign additions + OpenLauncher arbitrated b3320463); Telegram BLOCKED-ON-FREEZE (HTML artifact) and TinyMusic 404 re-confirmed, no substitutes accepted. Baseline 52-stage battery ALL PASS at c0f178a7 before any change.

20-APK frontier at c0f178a7 (zero drift vs MASTER-2): 12 APKs with real content, 4 partial (gmdice 24.6%, microtimer 50.6%, headingcalculator 6.7% w/135 views, chessclock 2.7%), 3 blank (tictactoe/dooz/bgclock — 2 views), 1 timeout (SECUSO >150s in androidx color-state-list path). All 2x-deterministic.

Evidence artifacts committed: docs/evidence/m3_campaign/phase0/ (per-APK result JSONs + screenshots + prefix baseline for before/after).""", ),
    ("M3 laws+fixes", """**MASTER CAMPAIGN 3 — §6/§7/§13 LAWS + FIXES (commits 83f1a04d, 5d8303e4, 1df3b263, 2f91c63f, 32d38b53)**

Three independent root causes closed, all law-level, zero package branches:

1. FIX-M3-001 (cross-pass geometry §7): the DEX superclass classifier was registered on the LAZY default inflater and silently dropped by ensure_loaded() recreation — the AUTHORITATIVE window measure ran the substring fallback (CalculatorDisplay extends LinearLayout classified LEAF → View-default 1920) while the render pass re-asserted the DEX classifier (container → 158). Spec evidence: [U007-SPEC] container=0 (pass 1) vs container=1 (pass 2). Fix: apply_is_a() on every (re)creation (Factory law) + registration at the ResourceRuntime.

2. FIX-M3-003/003b (ARSC §13): ResTable_map stride 20 → 12 bytes (AOSP: name u32 + Res_value(8)); only coincidentally-aligned keys ever decoded — every multi-key style bag dropped attributes app-wide (ground truth aapt2: keypad_button keys [95,98,d4,e6,f4,f5,f6,181]). Also: bag parent ref was overwritten by complex_items[0]; now preserved in ArscEntry::bag_parent (style inheritance reachable again).

3. FIX-M3-002/002c (style-bag layout params §6): style= references now supply layout_width/height/weight/margin with AOSP precedence (direct XML > style > theme), including modern-aapt2 compiled references without raw strings; apply_style walks the style parent chain (child beats parent).

4. FIX-M3-004 + memo (§4): AOSP LinearLayout match-parent second-pass remeasure (remaining space after non-match siblings, child margins + parent padding in the spec) + §7 convergence memo (identical (view,spec) measured once per pass — also fixes the G04 hostile exponential timeout).

5. FIX-M3-005/005b/006/007/007b (API §15/§13): removed the substring "TextView+*setText*" no-op stub; ViewShadow.setTextColor capture (unresolved-default black does not clobber resolved style colors — documented deviation); Integer.remainderUnsigned/divideUnsigned/compare; Resources.getColor ARSC-first with name-map fallback.""", ),
    ("M3 cross-APK validation", """**MASTER CAMPAIGN 3 — §24 CROSS-APK VALIDATION + DETERMINISM**

headingcalculator: nonbg 6.71% → 82.51% (keypad fills the screen via style weight shares; keypad measured 1080x1762 = remaining-space law; buttons 264x474 weighted shares), 3-run byte-identical (8a6ce425...). microtimer: lawful delta — style/PadButton (0dp+weight+match+margins) now applied. All other corpus APKs pixel-identical at every commit boundary.

Law battery: m3_arsc_style_law_test (17 checks on a real aapt2 fixture ARSC) + m3_style_geometry_check (6 checks: 64dp header law, remaining-height remeasure, style-bag-through-parent-chain geometry, sequential weighted shares, direct-override precedence) + fixture m3_style_weight wired into the harness — battery now 55 stages ALL PASS; goldens byte-identical; zero package-specific code.

§9 event loop: real scheduling path PROVEN on chessclock (tap from live view geometry → PerformClick → app onClick real DEX → postDelayed → virtual-time drain → self-rescheduling tick Runnable → fired=1 across 11 consecutive frames; tick-1 state mutation "9:59:59" with frame SHA change). Multi-tick compute chain honestly BLOCKED: F-TIMER-COMPUTE (heap receiver class identity), F-ARGS (color(int) resid lost upstream), F-TIMER-STACK (getStackTrace synthetic frames lack shadow boundaries — microtimer).""", ),
]

def main():
    token = open(TOKEN_FILE).read().strip()
    urls = json.loads(URLS_JSON.read_text()) if URLS_JSON.exists() else {}
    for title, body in COMMENTS:
        req = urllib.request.Request(
            f"https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/{ISSUE}/comments",
            data=json.dumps({"body": body}).encode(),
            headers={"Authorization": f"token {token}", "Content-Type": "application/json"},
            method="POST")
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read())
            url = data.get("html_url", "")
            if url:
                urls[f"M3 {title}"] = url
                print(f"POSTED {title}: {url}")
        except Exception as e:
            print(f"FAILED {title}: {type(e).__name__} (token error redacted)")
    URLS_JSON.write_text(json.dumps(urls, indent=1) + "\n")
    print("urls ->", URLS_JSON)

if __name__ == "__main__":
    main()
