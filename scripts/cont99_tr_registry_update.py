#!/usr/bin/env python3
"""cont99_tr_registry_update.py — CONT-99 T2 registry append (F-NEW-408..411).

Four generic roots from the transforms/density/insets track, each proven by
the fixtures/cont99_tr_probe paired A/B battery (PRE 3b89722589ff5af7 →
POST 8251d80a117a7afe). Mirrors root_registry.json →
canonical/root_cause_registry.json.
"""
import json
import shutil

BASE = "/home/z/my-project"
REG = f"{BASE}/root_registry.json"
MIRROR = f"{BASE}/canonical/root_cause_registry.json"

WAVE = "CONT-99"
DIRECTIVE = ("#364 CONT-99 T2 (comment 6248236077) — Parent/child "
             "coordinate transforms, density and window insets")
FIXTURE = ("fixtures/cont99_tr_probe (real aapt2/ECJ/D8; apk "
           "run/cont99/c99tr.apk sha16 f9ce4ff645d84f69, V1-C99TR; "
           "5 deterministic harness runs: control --tap 150,75 / "
           "translation --tap 110,340 / scale --tap 120,650 / "
           "scroll --tap 100,930 / notap)")
AB = ("PRE binary 3b89722589ff5af7: translation tap D=0 (missed), scale tap "
      "F=0 (missed), scroll tap H=1 (stale-region hit on the scrolled-away "
      "clipped control), childD getTop=300 (absolute), childH "
      "getLocationOnScreen=(0,1800) (double-count), getX=0.0, "
      "setScrollY no-op. POST binary 8251d80a117a7afe: D=1, F=1, H=0, "
      "getTop=0, onScreen=(0,900), getX=30.0/getY=20.0, scrollY=150 — all "
      "AOSP-law matched; control B=1 both binaries.")
REGRESSION = ("wall 12/12 MATCH byte-identical (dooz 31ddd4d5b8e6d18e, "
              "opencalc f25b754c4565c38b, unote 90a67cc1ddda57b7, microtimer "
              "bbd350b6c14fbd52, x3 — includes the F-NEW-409 getLeft "
              "frame change: opencalc anchor UNCHANGED); goldens 4/4; "
              "negatives 19/19; reinstall 8/8 identity ALL PASS; MG-310 "
              "7/7; MG-150 3/3 under the law-correct fence (the old fence "
              "locked the pre-fix hit-test blindness as 'current law' — "
              "updated honestly, frontier consumed by F-NEW-408); "
              "selftests 13/13; F-NEW-376 70/70; anchors c74esc "
              "containment OK, clock1 OK, clinit1 onDraw law-correct (ops=6), "
              "swipe1 setup OK (ops=7); sax1/perf1 probe rows silent on "
              "BOTH binaries (A/B on pristine 3b89722589ff5af7 — container "
              "runnable-pacing artifact, not drift)")
HONEST = ("hit == draw holds for the axis-aligned subset: translation "
          "node+ancestors, scale about lazy-center pivot (F-NEW-359 "
          "GeoGuard formula), ancestor scroll threading. Rotation-about-"
          "pivot and scaled-subtree re-transform remain the recorded "
          "F-NEW-359 draw frontier — the hit rect deliberately does not "
          "rotate (hit never exceeds what the raster paints). Insets: "
          "getRootWindowInsets() answers null (fullscreen window, no "
          "system bars) — report-only residual. Density 2.625/420dpi with "
          "applyDimension consistency proven (probe [C99-DENS] OK) — "
          "self-consistent default, no violation. MG-150 fence "
          "tap-A row flipped from 'hit at stale layout position' (the "
          "pre-fix blindness, honestly re-graded) to 'silent at stale "
          "position, hit at translated visual position'.")

ROOTS = [
    {
        "id": "F-NEW-408",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P0",
        "title": ("Touch hit-test ignored view transforms: translation "
                  "(node+ancestors), scale-about-pivot and ancestor scroll "
                  "were invisible to the DOWN claim, delegate-fallback and "
                  "MOVE-slop frames (hit != raster)"),
        "layer": "runtime/touch-dispatch",
        "directive": DIRECTIVE,
        "root_cause": (
            "touch_dispatcher.cpp node_at() tested the RAW laid-out bounds "
            "(x/y/width/height) with no transform mapping; the claim walk "
            "and consult_fallback_delegates_ threaded no ancestor offsets "
            "either. AOSP ViewGroup.dispatchTouchEvent transforms the DOWN "
            "point with the parent scroll offset and the child's inverse "
            "matrix (transformMotionEventToLocal) before the containment "
            "test. Probe PRE: tap (110,340) inside the TRANSLATED rect of "
            "childD (30..130, 320..370) hit nothing; tap (120,650) inside "
            "the SCALED rect of childF (-50..150, 575..675) hit nothing; "
            "tap (100,930) HIT childH through the stale laid-out region of "
            "a control scrolled 150px away and clipped to invisibility "
            "(draw walk applies translation/scale/scroll; hit-test did "
            "not — the two frames had diverged)."),
        "fix": (
            "touch_dispatcher.cpp: (1) eff_rect_of() — the node's hit rect "
            "moves with its own translation and scales about its pivot "
            "(EXACT F-NEW-359 GeoGuard formula incl. the lazy-center pivot "
            "law) applied in node_at for both the raw and the sentinel-fill "
            "paths; (2) the DOWN claim and the delegate-fallback walk "
            "thread (ax, ay) = Σ(ancestor scroll) − Σ(ancestor translation) "
            "and test every node at (ev + offset); (3) the MOVE slop frame "
            "uses the transformed rect so a translated/scaled target keeps "
            "its gesture alive. POST: D=1, F=1, H=0 — hit == raster."),
        "evidence": {
            "wave": WAVE, "fixture": FIXTURE, "paired_ab": AB,
            "regression": REGRESSION, "honest_notes": HONEST,
        },
        "issue": "#364",
    },
    {
        "id": "F-NEW-409",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P0",
        "title": ("View.getLeft/getTop/getRight/getBottom answered ABSOLUTE "
                  "window coordinates; AOSP mLeft/mTop are PARENT-RELATIVE"),
        "layer": "runtime/view-geometry-getters",
        "directive": DIRECTIVE,
        "root_cause": (
            "android_shadows.cpp getLeft/getTop/getRight/getBottom (the "
            "R-NEW-441 identity fix) answered measured_* directly, which "
            "the engine's layout phase fills with ABSOLUTE window-space "
            "geometry (layout_inflater top-down task stack). AOSP View.java "
            "defines mLeft/mTop as the position RELATIVE TO THE PARENT; "
            "every library that does parent-relative geometry math reads "
            "garbage offsets once the parent is not at the window origin. "
            "Probe PRE: childD inside rowC@(0,300) answered getTop=300 "
            "(AOSP: 0); childH inside rowG@(0,900) answered getTop=900 "
            "(AOSP: 0)."),
        "fix": (
            "getLeft/getTop/getRight/getBottom subtract the parent's "
            "measured_left/top when a materialized (laid_out) parent "
            "exists; the root view answers its absolute window position "
            "(AOSP root mLeft). Un-materialized appcompat wrapper parents "
            "(sentinel geometry, F-NEW-373 lever) contribute nothing — "
            "their chains keep the raw laid-out state. R-NEW-441 keeps its "
            "identity property (the getters answer the REAL layout state, "
            "not the generic 0 stub); only the frame is corrected. "
            "opencalc wall anchor byte-identical ×3 after the change."),
        "evidence": {
            "wave": WAVE, "fixture": FIXTURE, "paired_ab": AB,
            "regression": REGRESSION, "honest_notes": HONEST,
        },
        "issue": "#364",
    },
    {
        "id": "F-NEW-410",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P0",
        "title": ("getLocationOnScreen/getLocationInWindow (and "
                  "transformMatrixToGlobal/ToLocal) chain-summed ABSOLUTE "
                  "x/y — double-counting every non-origin ancestor hop"),
        "layer": "runtime/view-geometry-getters",
        "directive": DIRECTIVE,
        "root_cause": (
            "The shadow summed each hop's ABSOLUTE stored x/y to compute "
            "the 'parent-chain sum'. AOSP getLocationInWindow = Σ of the "
            "PARENT-RELATIVE mLeft/mTop hops == the view's absolute window "
            "position; summing absolute values double-counts every "
            "ancestor not at the origin. Probe PRE: childH (absolute "
            "(0,900), parent rowG@(0,900)) answered (0,1800); childD "
            "answered (0,600) instead of (0,300)."),
        "fix": (
            "getLocationOnScreen/getLocationInWindow answer (x, y) "
            "directly (the engine stores absolute laid-out geometry — that "
            "IS the chain sum of parent-relative hops); "
            "transformMatrixToGlobal/ToLocal accumulate the same absolute "
            "translate. [TOUCHWIN-LOC] diagnostics retained."),
        "evidence": {
            "wave": WAVE, "fixture": FIXTURE, "paired_ab": AB,
            "regression": REGRESSION, "honest_notes": HONEST,
        },
        "issue": "#364",
    },
    {
        "id": "F-NEW-411",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P0",
        "title": ("View.setScrollX/setScrollY were silent no-ops (generic "
                  "stub) and View.getX()/getY() answered 0 instead of "
                  "left+translation"),
        "layer": "runtime/view-property-shadows",
        "directive": DIRECTIVE,
        "root_cause": (
            "scrollTo/scrollBy/getScrollX/getScrollY had shadow laws but "
            "the single-axis setScrollX/setScrollY arms fell to the "
            "generic silent stub — probe PRE: setScrollY(150) left "
            "scrollY=0. getX()/getY() (AOSP: mLeft + mTranslationX) were "
            "absent, answering the type default 0.0 while the translation "
            "properties themselves stored correctly (tx=30.0)."),
        "fix": (
            "setScrollX/setScrollY implemented as single-axis scrollTo "
            "arms with the R-NEW-428 onScrollChanged hook; getX()/getY() "
            "answer parent-relative left/top (F-NEW-409 frame) plus the "
            "own translation. Probe POST: scrollY=150, getX=30.0, "
            "getY=20.0."),
        "evidence": {
            "wave": WAVE, "fixture": FIXTURE, "paired_ab": AB,
            "regression": REGRESSION, "honest_notes": HONEST,
        },
        "issue": "#364",
    },
]

with open(REG) as f:
    reg = json.load(f)

existing = {r["id"] for r in reg}
added = 0
for root in ROOTS:
    if root["id"] not in existing:
        reg.append(root)
        added += 1

with open(REG, "w") as f:
    json.dump(reg, f, indent=1, ensure_ascii=False)
shutil.copyfile(REG, MIRROR)
print(f"registry: {len(reg) - added} -> {len(reg)} roots (+{added})")
