#!/usr/bin/env python3
"""S72-W2 registry update: F-142 ROOT-CAUSED-FIXED (with honest evidence chain),
new F-145 capture-surface law OPEN. Machine-readable, single source of truth."""
import json

PATH = "/home/z/my-project/root_registry.json"
doc = json.load(open(PATH))
roots = doc["roots"] if isinstance(doc, dict) and "roots" in doc else doc

f142 = next(x for x in roots if x.get("id") == "F-142")
f142["status"] = "ROOT-CAUSED-FIXED"
f142["supersede_note"] = (
    "Wave-1 hypothesis 'src->bitmap resolution never happens' DISPROVEN by fresh "
    "evidence (constitution #155/#156): current binary resolved mipmap resids and "
    "painted ONE fish at (0,0) + logo pre-fix (frame_008 = 2,068,844 px). Real roots "
    "were the layout laws below — both FIXED this wave."
)
f142["roots"] = [
    {
        "id": "F-142a",
        "root": "RelativeLayout final-layout fixpoint drops MarginLayoutParams in "
                "alignParentLeft/Top + center + flow branches (x=cl / y=ct) and "
                "overrides the margin-correct measure-time cached edges",
        "upstream_law": "AOSP RelativeLayout.java applyHorizontalSizeRules/"
                        "applyVerticalSizeRules: mLeft = paddingLeft + leftMargin; "
                        "flow default = same; center offsets by leftMargin-rightMargin",
        "fix": "resources/layout_inflater.cpp RL fixed-point: alignParentTop/flow "
               "y=ct+lp_margin_top; alignParentLeft/flow x=cl+lp_margin_left; center "
               "branches add margin offsets (same law as LinearLayout/FrameLayout branches)",
        "evidence": "fishrings 41 fish/arrow views parsed m=184,184 px but painted "
                    "stacked at (0,0); only bottom/right-anchored views landed "
                    "([U007-LAYOUT] dump + [EXP092-RENDER] pos pre/post)",
    },
    {
        "id": "F-142b",
        "root": "android:maxWidth/maxHeight/adjustViewBounds never parsed; ImageView "
                "wrap measure used raw density-scaled intrinsic clamped only by "
                "parent AT_MOST spec (300x300 mdpi fish measured 788x788 / 896x1113)",
        "upstream_law": "AOSP ImageView.java onMeasure L1141+: desired = intrinsic, "
                        "then widthFit/heightFit caps with aspect-true opposite-axis "
                        "rescale (adjustViewBounds), applied before spec clamp",
        "fix": "ViewNode/Attrs max_w/max_h/adjust_view_bounds + canonical dim/bool "
               "parse + aspect-fit cap law in the ImageView wrap measure block",
        "evidence": "pre: 896x1113 vs post: 110x78 for topaclockwise 600x424 under "
                    "maxWidth=42dip/maxHeight=60dip — exact AOSP fit result",
    },
]
f142["fan_out"] = (
    "RelativeLayout margin family = corpus-wide layout law (every alignParent*/"
    "flow child with margins); ImageView measure caps = every XML-maxWidth app. "
    "Regression: 9/9 previously-rendering corpus apps byte-identical pixel counts "
    "(bouncy/gmdice/microtimer/opmt/unote/stopwatch/dooz/tripeaks/tictactoe pre=equal post=equal); "
    "fishrings frame_008 2,068,844 -> 2,072,819 px + full game board (4 fish groups, "
    "rings, arrows); determinism x3 BYTE-IDENTICAL (sha a341e3ad9092f640); "
    "battery: all fixture stages PASS incl. M3 6/6 (checker regex updated for the "
    "extended [U007-LAYOUT] margin dump; no behavioral regression)"
)
f142["real_app_proof"] = (
    "fishrings_v1.23_vc6 real-Dalvik 9-frame pump: frames/frame_008.png shows the "
    "real game board (was: single fish at (0,0) + logo); wave-1 dashboard's 0.0% "
    "measured the SPLASH-window screenshot.ppm — see F-145 capture-surface law"
)

if not any(x.get("id") == "F-145" for x in roots):
    roots.append({
        "id": "F-145",
        "status": "OPEN",
        "priority": "P1",
        "title": "Final screenshot capture surface does not follow the top-of-stack "
                 "window (multi-activity apps capture the splash/first window)",
        "evidence": "fishrings post-fix: frame_008 (active window pump) = 2,072,819 "
                    "px real game board; screenshot.ppm (final capture) = 0 px white "
                    "splash surface. Same pattern tripeaks (205,273 vs 0) and dooz "
                    "(197 vs 92). Wave-1 dashboard values for multi-window apps were "
                    "splash-surface measurements — measurement-surface flaw, not "
                    "render truth.",
        "upstream_law": "AOSP SurfaceControl/WindowManager: screenshots capture the "
                        "focused/top-of-stack window of the default display",
        "next_action": "capture stage must follow the active/focused window "
                       "(content_view switch) instead of the first window",
        "impact": "KPI-2 (stable screenshots) misreported for every multi-activity "
                  "app; dashboard honesty depends on it",
    })

json.dump(doc, open(PATH, "w"), indent=1, ensure_ascii=False)
print("registry updated:", len(roots), "entries; F-142 ->", f142["status"], "; F-145 OPEN")
