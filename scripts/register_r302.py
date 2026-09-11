#!/usr/bin/env python3
"""Register R-NEW-302: demo layout regression at current HEAD
(FrameLayout margins ignored + root MATCH_PARENT not filling window),
discovered during the MC3 demo-proof re-test. Read-only w.r.t. code."""

import json

REG = '/home/z/my-project/MiniAndroid-Compatibility-Runtime/root_registry.json'
r = json.load(open(REG))

assert all(root['id'] != 'R-NEW-302' for root in r['roots']), 'R-NEW-302 already exists'

entry = {
    "id": "R-NEW-302",
    "status": "OBSERVED-FAIL",
    "priority": "P1",
    "fg": True,
    "evidence": (
        "MC3 demo-proof re-test at HEAD 355cf45a (F-076 binary), demo APK rebuilt "
        "5b273c2ef15c7896... run --click-count 8: validate_demo_proof.sh PASSES "
        "(9 distinct frames, state text advances count=1..9 exactly per DEX law, "
        "deterministic replay identical SHA256 sequence) BUT pixel forensics: "
        "box solid-color patch is 160x160 at x[0..159] y[132..291] in ALL 9 frames "
        "while declared pos cycles (220,370)(400,660)(580,950)(760,80)... — "
        "FrameLayout.LayoutParams leftMargin/topMargin are ignored (box pinned at "
        "stage origin). Additionally root LinearLayout MATCH_PARENT resolves to "
        "600x1432 wrap-bounds (widest-text child width; stage bottom 132+1300=1432) "
        "leaving white margins right/bottom of the 1080x1920 window, and the TAP ME "
        "button renders WRAP-width (~106px) instead of MATCH_PARENT. Regression vs "
        "committed demo proof (docs/demo at f12af85a...gif): old renderer moved the "
        "box across the declared 5x4 grid and filled the window width. Text "
        "rendering itself IMPROVED (old: overlapping glyphs; new: clean stacked "
        "lines, proper Material button). Old state cycle law still holds: box color "
        "cycles exact COLORS[] values GREEN(67,160,71) BLUE(30,136,229) "
        "YELLOW(253,216,53) RED(229,57,53)."
    ),
    "missing": (
        "LinearLayout/FrameLayout window-attach laws: (1) root MATCH_PARENT must "
        "resolve against the window decor size (1080x1920), not wrap to children; "
        "(2) MATCH_PARENT child width (button, title, status) must fill parent; "
        "(3) FrameLayout child gravity+leftMargin/topMargin must offset the child "
        "box during measure/layout."
    ),
    "next": (
        "Trace miniandroid view-layout measure/layout pass for the demo tree "
        "(LinearLayout vertical: title/status/button/stage; stage=FrameLayout with "
        "160x160 child, Gravity.TOP|LEFT, margins) — fix margin application + "
        "MATCH_PARENT window-fill as ONE generic layout-law fix; regression gate: "
        "box pixel position must equal declared pos each frame (window: stage "
        "origin + (x, y)) and root must fill 1080x1920."
    ),
    "commit": "5356c7f8ac9171deade44ea44826fafe9e26caa4",
}

r['roots'].append(entry)
r['summary']['total'] = 302
r['summary']['by_status']['OBSERVED-FAIL'] = r['summary']['by_status'].get('OBSERVED-FAIL', 0) + 1

json.dump(r, open(REG, 'w'), indent=1, ensure_ascii=False)
print('registry updated: total=302, OBSERVED-FAIL=%d' % r['summary']['by_status']['OBSERVED-FAIL'])
