#!/usr/bin/env python3
"""S128: register R-NEW-424 (TouchTarget + onInterceptTouchEvent law) in the
writable root registry, with the S128 evidence chain. Idempotent."""
import json

P = '/home/z/my-project/root_registry.json'
rr = json.load(open(P))
if any(r['id'] == 'R-NEW-424' for r in rr['roots']):
    print('R-NEW-424 already registered'); raise SystemExit

rr['roots'].append({
    "id": "R-NEW-424",
    "title": "INPUT TouchTarget + onInterceptTouchEvent law (CAP-INPUT-102/100): hit-test walked children in DRAW order "
             "(AOSP walks REVERSE — topmost sibling must win overlaps), no TouchTarget chain was captured (MOVE/UP could not "
             "dispatch through ancestors), and ViewGroup.onInterceptTouchEvent never ran (no intercept-at-DOWN retarget, no "
             "mid-gesture CANCEL) — the AOSP ViewGroup.dispatchTouchEvent core was only partially modeled.",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P0",
    "fg": True,
    "app": "INPUT layer — interactive corpus (heading calculator, FlappyCow proven this wave)",
    "evidence": "S128: reverse draw-order walk + touch_target_chain capture (AOSP mFirstTouchTarget law) + "
                "onInterceptTouchEvent DEX bridge (dispatch_intercept) + intercept-at-DOWN retarget + mid-gesture "
                "CANCEL/retarget law; overrides_intercept_touch_event captured at both ctor sites (inflate + programmatic). "
                "116-stage battery ALL PASS (zero regressions); S128 INPUT wave 9/9: calc goldens a169346e x3 PRESERVED, "
                "flappy menu golden 13cf4746 x3 PRESERVED, calc taps chain max=5 + PerformClick x3 + display state change "
                "(90080684), flappy StartscreenView chain + onTouchEvent arm, uNote BOOT-ORDER 7/7, ttt byte-identical "
                "baseline b5a7a35d, telegram/whatsapp honest NOT-A-RENDER unchanged (3/2 colors).",
    "missing": "requestDisallowInterceptTouchEvent child flag (documented boundary); real-APK DEX onInterceptTouchEvent "
               "override wave (no tap-path override in the current wave set — scrollable-container APKs next); "
               "VelocityTracker/TouchDelegate/EdgeEffect remain (M-01 residuals).",
    "next": "M-01 residual: CAP-INPUT-108 VelocityTracker then CAP-INPUT-110 TouchDelegate; intercept wave on a "
            "scrollable-container APK (sudoku / opencalculator SlidingUpPanelLayout family).",
    "commit": "S128 (this session)",
})
json.dump(rr, open(P, 'w'), indent=1, ensure_ascii=False)
print('R-NEW-424 registered; roots =', len(rr['roots']))
