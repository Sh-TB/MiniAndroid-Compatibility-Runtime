#!/usr/bin/env python3
"""s72_w4_registry.py — register F-148/F-149/F-150 (S72-W4) into root_registry.json."""
import json

REG = "/home/z/my-project/root_registry.json"
d = json.load(open(REG))
ids = {r["id"] for r in d["roots"]}
assert "F-148" not in ids and "F-149" not in ids and "F-150" not in ids

d["roots"].append({
    "id": "F-148",
    "title": "ConstraintLayout anchor family unimplemented — every child measured 0-wide/stacked at x=0 (layout_constraint* attrs unparsed; no solver semantics)",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P0",
    "source": "github.com/zhangman523/AndroidGameSnake @ b4968c39 res/layout/activity_main.xml (1 root ConstraintLayout, 6 children, anchor family start/end/left/right/top/bottom + bias)",
    "upstream_law": "AOSP ConstraintLayout measure/onLayout: per-axis anchor resolution; MATCH_CONSTRAINT (0dp) + both anchors = EXACTLY span; fixed/wrap + both anchors = bias-positioned (default 0.5) in span; one anchor = edge from anchor +/- margin; margins on the anchored side; parent anchors bind to the padding box; onLayout replays measure-resolved edges",
    "first_divergence": "view_tree.json: SnakePanelView w=0 h=105; buttons at x=0, sequential y (105,223,341,459,577) instead of constrained geometry",
    "root_cause": "layout_inflater parse chain had no layout_constraint* handling; measure_layout had no ConstraintLayout branch (generic else measured children without anchor semantics)",
    "affected": "android.support.constraint.ConstraintLayout + androidx.constraintlayout.widget.ConstraintLayout trees (the largest modern layout family); every 0dp match-constraint child",
    "implementation": "layout_inflater.cpp: (1) apply_element_attrs parses 12 anchor attrs + 2 bias attrs (cl_* fields, compiled-ref fallback via arsc id table); (2) measure_layout is_cl_container branch — per-axis topological (Kahn) resolution, both/one/no-anchor laws, MATCH_CONSTRAINT spread, bias positioning, AOSP (0,0) no-anchor default, wrap content = max child extents; (3) layout phase is_cl branch replays cached edges (same onLayout-replay contract as RelativeLayout)",
    "test": "snake_v1.0_vc1 real APK: SnakePanelView EXACTLY(1080)x780; TOP btn (441,801) centered; LEFT (122,940)/RIGHT (760,940) biased pair; BOTTOM (441,1398) span 799 bias 0.5 -> EXACT; START (0,780)",
    "evidence": "docs/foundation/S72_WAVE4.md + run/s72_w4_snake_int*/view_tree.json; zero regressions (corpus 10/10 pixel-SAME, fixtures 25/25 pixel-SAME)",
    "fan_out": "unlocks the modern app layout family (ConstraintLayout is the dominant Android layout container); OPMT staged-layout workaround no longer required for this subset",
    "documented_deviations": "Cassowary global solver replaced by per-axis topological resolution; Guideline/chains/dimensionRatio/percent/Group/RTL baseline NOT in subset (attrs parsed for id-stability, semantics fall back to no-anchor law + diagnostic)",
    "session": "S72-W4",
})

d["roots"].append({
    "id": "F-149",
    "title": "Resources.getDisplayMetrics unimplemented (silent null) + DisplayMetrics singleton density=1.0 (mdpi) diverging from the 2.625 device-density authority + TypedValue.applyDimension DEX bridge missing -> app dp2px computed 0px, SnakePanelView.onMeasure returned 0x0",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P0",
    "source": "github.com/zhangman523/AndroidGameSnake @ b4968c39 SnakePanelView.java dp2px field-init (TypedValue.applyDimension(COMPLEX_UNIT_DIP, 15, context.getResources().getDisplayMetrics()))",
    "upstream_law": "AOSP Resources.java getDisplayMetrics returns the CURRENT DisplayMetrics (never null, never foreign density); TypedValue.java L1019 applyDimension switch (px identity; dip x density; sp x scaledDensity; pt x xdpi/72; in x xdpi; mm x xdpi/25.4); DisplayMetrics carries the device profile (density 2.625 = DENSITY_420 @1080x1920, scaledDensity = density x fontScale 1.0)",
    "first_divergence": "[DEX-MEASURE] SnakePanelView.onMeasure spec AT_MOST(1080)xUNSPEC -> 0x0 (mRectSize=0: applyDimension x getDisplayMetrics silent-null chain)",
    "root_cause": "three stacked silent gaps (SILENT WRONGNESS family, S038): getDisplayMetrics fell through unimplemented; get_or_create_singleton(DisplayMetrics) pre-populated density=1.0 contradicting the inflater DeviceMetrics authority (2.625); no applyDimension DEX bridge (res_id.cpp's C++ helper was inflater-path only)",
    "affected": "every app measuring in dp/sp at runtime via TypedValue/DisplayMetrics (custom-view measure/draw code paths)",
    "implementation": "dalvik_engine.cpp: Resources.getDisplayMetrics answers the DisplayMetrics singleton re-asserting device fields (density 2.625, densityDpi 420, scaledDensity 2.625, 1080x1920, xdpi/ydpi 420); TypedValue.applyDimension(IFDisplayMetrics)F bridge = exact AOSP switch reading the metrics object's heap fields; get_or_create_singleton DisplayMetrics population aligned to the device law",
    "test": "snake real APK: SnakePanelView measures 1080x780 (= 20 x 15dp x 2.625 EXACTLY, AOSP first-measure value); buttons 197x118 (= 75x45dp EXACTLY)",
    "evidence": "docs/foundation/S72_WAVE4.md; zero regressions (corpus 10/10 pixel-SAME, fixtures 25/25 pixel-SAME)",
    "fan_out": "dp/sp measurement now law-consistent for app-side TypedValue consumers (cross-component density authority unified)",
    "session": "S72-W4",
})

d["roots"].append({
    "id": "F-150",
    "title": "Thread game-loop family dead: (a) ThreadShadow no-op family swallowed Thread.sleep shadowing the real sleep law; (b) javac emits the SUBCLASS descriptor for unqualified Thread.sleep/start (invoke-static GameMainThread;->sleep(J)V) so literal Thread-class guards never matched; (c) hierarchy-routed thread starts never drained outside parks; (d) yielded bodies had no resume point",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P0",
    "source": "github.com/zhangman523/AndroidGameSnake @ b4968c39 SnakePanelView$GameMainThread.run (while(!mIsEndGame){move;check;refresh;tail;postInvalidate;sleep(1000/mSpeed);}) — real-time game-loop family",
    "upstream_law": "OpenJDK/AOSP Thread: start() runs the body on a concurrent thread; sleep(ms) suspends THIS thread and resumes it after ms on the real clock; Thread.start()/sleep() compile against the receiver's subclass descriptor (javac inherited-member rule); DEX method_ids table ground truth: GameMainThread.sleep/start entries",
    "first_divergence": "[F084-HALT] Infinite loop at PC=0x2 in GameMainThread.run (visited 50001 times, op 0x71 invoke-static) — the loop never slept, the body never yielded, the VirtualMachineError poisoned onCreate (APP BOUNDARY unwind)",
    "root_cause": "four stacked gaps: ThreadShadow handled sleep as handled_void before the real sleep law; sleep/start/run guards were literal class_name==Thread; pending_starts_ only drained inside drain_park_queues_bounded; a body that yielded at sleep had no re-drain path (died silently after slice 1)",
    "affected": "the app-own Thread game-loop/scheduler family (while(!done){tick;sleep(T);}); every Thread subclass whose unqualified sleep/start compile against the subclass; bouncy (L1 game-loop corpus member), secuso game family",
    "implementation": "(1) sleep removed from the ThreadShadow no-op family; (2) is_thread_receiver() walks the DEX superclass chain — sleep law + both start/run drain sites now hierarchy-aware; (3) stage_frame_sequence drains pending starts + due yielded bodies at every frame boundary (bounded 4 starts / 8 resumes); (4) ThreadShadow yielded-threads registry (thread -> {target, wake_at}): run_thread_start_body registers a sleep-yielded body with wake = boundary now + sleep-ms; boundaries re-drain earliest-wake-due bodies; completion (no yield) clears the registry entry; inside drained bodies sleep does NOT advance the shared clock (the boundary owns it) — outside (main quiescence) the M3 advance law is preserved",
    "test": "snake real APK: 14-frame run — START tap -> thread starts, ticks 2x/frame (125ms sleep @ 250ms frame-delay EXACT); direction taps steer the snake (BOTTOM/RIGHT/LEFT turn chains visible cell-by-cell; the app's own reverse-guard correctly ignores illegal turns); game state = snake cells + food cell rendered per frame",
    "evidence": "docs/foundation/S72_WAVE4.md + docs/evidence/s72_w4_snake/ (frame chain, metrics, SHAs); determinism x3 BYTE-IDENTICAL (pixel sha 1a419545419deb3a); zero regressions (corpus 10/10 pixel-SAME, fixtures 25/25 pixel-SAME, dooz det x3 unchanged)",
    "fan_out": "the real-time game-loop architecture family (first of its corpus: bouncy wall, secuso L2 walls) becomes reachable; wake-time scheduler is the deterministic counterpart of concurrent Thread scheduling",
    "documented_deviations": "serialized execution: a body slice = one run() invocation between sleeps (no mid-body continuation capture); bodies NOT structured as loop+sleep re-run from entry (recorded); postInvalidate rides frame-driven rendering (no explicit invalidation model)",
    "session": "S72-W4",
})

d["total"] = len(d["roots"])
d["summary"] = d.get("summary", 0) if isinstance(d.get("summary"), int) else d.get("summary")
json.dump(d, open(REG, "w"), indent=1, ensure_ascii=False)
print("registry:", d["total"], "roots (F-148/149/150 registered)")
