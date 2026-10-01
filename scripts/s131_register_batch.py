#!/usr/bin/env python3
"""s131_register_batch.py — S131 mass registry update.

1. Register the 10 S130 law roots (R-NEW-427..436) that S130 implemented and
   law-tested but never registered (registry max was R-NEW-426). All carry
   the S130 evidence (law test 51/51 via `make laws130`, battery 124-stage
   ALL PASS at S131) + AOSP android-14 anchors (docs/upstream/aosp/s130_laws/).
2. Register R-NEW-437: S131 MEASURED finding — opencalculator GridLayout
   button bounds unassigned (MC-041 measure/layout family; blocks the M-01
   intercept wave on opencalculator; input-code fixes FORBIDDEN by the
   REUSE-FIRST audit — layout law, not input).
3. Upgrade CAP-INPUT-099 (dispatchTouchEvent) IMPLEMENTED -> TESTED: real-APK
   fan-out evidence (sudoku TutorialActivity$1/$2 CLICK DISPATCHED through
   the R-NEW-424 walk law; state change 45962e01 -> f78aa16c on Skip).
Idempotent.
"""
import json

P = "/home/z/my-project/root_registry.json"
doc = json.load(open(P))
roots = doc["roots"] if isinstance(doc, dict) and "roots" in doc else doc
by_id = {r["id"]: r for r in roots}

EV130 = ("S130 laws + S131 gate: s130_laws_test 51/51 (make laws130), "
         "battery 124-stage ALL PASS, AOSP android-14.0.0_r2 anchors in "
         "docs/upstream/aosp/s130_laws/")
S130 = [
    ("R-NEW-427", "Scroller/OverScroller 1:1 port (startScroll/fling spline physics/viscousFluid/DECELERATION_RATE/settle-at-final)", "scroller_shadow.{h,cpp}", "TESTED"),
    ("R-NEW-428", "View.scrollTo/scrollBy fire onScrollChanged hook (AOSP View law)", "android_shadows scroll hooks + dispatch_scroll_changed bridge", "IMPLEMENTED"),
    ("R-NEW-429", "GestureDetector state machine 1:1 (onDown/onShowPress/onSingleTapUp/onLongPress/onScroll/onFling/onSingleTapConfirmed + double-tap; timeouts 100/500/300/40ms; LSQ2 velocity)", "gesture_detector_shadow.{h,cpp} + dispatch_gesture_cb bridge", "TESTED"),
    ("R-NEW-430", "computeScroll dispatch per frame in the draw walk (AOSP ViewGroup draw law)", "call_compute_scroll bridge + overrides capture", "IMPLEMENTED"),
    ("R-NEW-431", "View.setChecked/toggle/isChecked + onCheckedChanged hook", "android_shadows checked laws + dispatch_checked_changed", "IMPLEMENTED"),
    ("R-NEW-432", "FocusFinder one-focus law: setFocusable/requestFocus/clearFocus/isFocused + set_focused_view", "android_shadows + key_event_shadow focus_search", "TESTED"),
    ("R-NEW-433", "View listener family storage (OnScrollChangeListener/OnCheckedChangeListener/OnItemClickListener/OnItemLongClickListener/OnItemSelectedListener/OnKeyListener)", "android_shadows listener storage", "IMPLEMENTED"),
    ("R-NEW-434", "KeyEvent dispatch: onKey listener -> onKeyDown/onKeyUp arms (AOSP View.java L6952+)", "key_event_shadow + dispatch_key_event bridge", "TESTED"),
    ("R-NEW-435", "ViewPropertyAnimator record + settle-on-start", "android_shadows animator record", "IMPLEMENTED"),
    ("R-NEW-436", "Scroll-clip walk law: scrolling-ancestor fully-outside skip + RenderTask clip fields", "execution_engine render task", "IMPLEMENTED"),
]
n_new, n_upd = 0, 0
for rid, title, impl, status in S130:
    if rid in by_id:
        continue
    by_id[rid] = {
        "id": rid, "status": status, "priority": "P1", "fg": False,
        "title": title, "evidence": f"{impl}; {EV130}",
        "missing": "real-APK fan-out evidence waves (S131 audit queue)",
        "next": "evidence wave per docs/REUSE_AUDIT_INPUT.md next-wave queue",
        "commit": "5b78ba70",
    }
    n_new += 1

if "R-NEW-437" not in by_id:
    by_id["R-NEW-437"] = {
        "id": "R-NEW-437", "status": "OBSERVED", "priority": "P1", "fg": False,
        "title": "opencalculator GridLayout button bounds unassigned (76 buttons, w=0 in tree dump) — measure/layout family",
        "evidence": ("S131 probe run/s131/opencalculator_probe2: 76 Buttons, "
                     "0 with bounds; only FitWindowsLinearLayout/"
                     "ContentFrameLayout laid out (1080x1920); blocks M-01 "
                     "intercept wave on opencalculator"),
        "missing": "GridLayout measure/layout pass assigning child bounds (MC-041 family; REUSE-FIRST audit forbids input-side workarounds)",
        "next": "MC-041 GridLayout measure law (AOSP GridLayout.java anchor)",
        "commit": "c3c6054f",
    }
    n_new += 1

# CAP-INPUT-099 upgrade (capability registry lives in canonical/)
CAP_UPDATED = False
try:
    CP = "/home/z/my-project/canonical/capability_registry.json"
    cdoc = json.load(open(CP))
    caps = cdoc["capabilities"] if isinstance(cdoc, dict) and "capabilities" in cdoc else cdoc
    if isinstance(caps, list):
        for c in caps:
            if c.get("id") == "CAP-INPUT-099" and c.get("status") == "IMPLEMENTED":
                c["status"] = "TESTED"
                c["evidence"] = ("S131 real-APK fan-out: sudoku TutorialActivity$1/$2 "
                                 "CLICK DISPATCHED through the R-NEW-424 walk law "
                                 "(run/s131/wave_report.json); state change "
                                 "45962e01 -> f78aa16c on Skip; S128 calc chain "
                                 "max=5 + PerformClick x3")
                CAP_UPDATED = True
    elif isinstance(caps, dict):
        c = caps.get("CAP-INPUT-099")
        if c and c.get("status") == "IMPLEMENTED":
            c["status"] = "TESTED"
            c["evidence"] = ("S131 real-APK fan-out: sudoku TutorialActivity$1/$2 "
                             "CLICK DISPATCHED through the R-NEW-424 walk law; "
                             "state change 45962e01 -> f78aa16c on Skip")
            CAP_UPDATED = True
    json.dump(cdoc, open(CP, "w"), indent=1, ensure_ascii=False)
except Exception as e:
    print("cap registry:", e)

doc["roots"] = list(by_id.values())
if isinstance(doc, dict):
    doc["total"] = len(doc["roots"])
json.dump(doc, open(P, "w"), indent=1, ensure_ascii=False)
print(f"registered {n_new} new roots (S130 batch 427-436 + R-NEW-437); "
      f"total={doc['total']}; CAP-INPUT-099->TESTED: {CAP_UPDATED}")
