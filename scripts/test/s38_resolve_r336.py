#!/usr/bin/env python3
"""S38: upgrade R-NEW-336 OBSERVED-FAIL -> ROOT-CAUSED+FIXED with the
GREY_200-mask law evidence chain (VSTACK re-measure + pixel forensics)."""
import json, sys

REG = "/home/z/my-project/root_registry.json"
d = json.load(open(REG))
roots = d if isinstance(d, list) else d.get("roots", d)
target = None
for r in roots:
    if r.get("id") == "R-NEW-336":
        target = r
        break
if target is None:
    sys.exit("R-NEW-336 not found")

target["status"] = "ROOT-CAUSED-FIXED"
target["severity"] = "P1"
target["resolved_session"] = "S38"
target["root_cause"] = (
    "NOT a text-loss or click bug. The full DEX click chain works end-to-end "
    "(probe-click -> ViewShadow dispatch -> real DEX onClick -> getText '(empty)' "
    "-> setText('echo: (empty)') -> re-render). Proof: [U007_LAYOUT_DEBUG=4] "
    "VSTACK shows echo TextView id=14 re-measured 533x44 -> 254x44 between pass 1 "
    "and pass 2 = the POST-CLICK string was laid out from real app state; "
    "pixel forensics of the pre-fix frame: echo-row glyph pixels are exactly "
    "RGB(224,224,224)=#FFE0E0E0 (the app-requested w_text_c, byte-perfect "
    "rendering) over the EXP-092 synthetic container fill RGB(225,225,225) "
    "=GREY_200 — a delta of 1 per channel, human-invisible. The reported "
    "'blank echo row' was this contrast casualty. The deeper AOSP deviation: "
    "EXP-092 filled GREY_200 over every non-full-screen bg-less container, "
    "which MASKED the ScrollView's own android:background=@color/w_bg "
    "#FF101418 (the dark band 1560..1920 = exactly the region below the "
    "LinearLayout's content bottom 1493+padding). AOSP View.java law: a View "
    "with no background is TRANSPARENT; the ancestor background shows through."
)
target["fix"] = (
    "execution_engine.cpp stage_render_frame draw loop: before the EXP-092 "
    "GREY_200 container fill, walk node->parent_id chain; if ANY ancestor "
    "carries bg_color!=0 or bg_drawable_path or bg_shape_valid, skip the "
    "synthetic fill (transparent-container AOSP law; ancestor pixels already "
    "cover the area). Regression gate: fresh full battery 92 stages, ALL "
    "pixel goldens + interaction/determinism goldens re-run PASS "
    "(helloworld §28, tictactoe §29, G06/G07/G08, F-020/024/025/026/027/028/"
    "030/040/044/050/074, GATE H); only 2 fails = the documented missing "
    "external fixture HelloWorldSelfAware APK environment gap (S37-known, "
    "not code). hello_smoke + scroll_min byte-stable behavior (no bg "
    "ancestor -> GREY_200 visibility fill retained)."
)
target["evidence"] = target.get("evidence", "")
if "S38-RESOLUTION" not in target["evidence"]:
    target["evidence"] += (
        " || S38-RESOLUTION: minimal repro scroll_min (ScrollView>LinearLayout>"
        "TextView+Button, APK sha256 b9afb40738c4608ef5e3137ebc29119a49f91f5953d29b771638120f61173aa9) "
        "DID NOT reproduce the blank — 'clicked 1' renders (faint, same contrast "
        "family); hello_widgets re-run at HEAD shows faint 'echo: (empty)' "
        "pre-fix, fully readable post-fix; post-fix screenshot proves the "
        "single most complete View-world frame in the archive (8 widget kinds, "
        "all readable on the app's own dark background). Fixture hello_widgets "
        "rebuilt APK sha256 d3b89184c6bf238e(rebuild; original registration "
        "cited 461436b1... from the pre-restore source tree)."
    )

json.dump(d, open(REG, "w"), indent=2, ensure_ascii=False)
print("R-NEW-336 -> ROOT-CAUSED-FIXED; total roots =", len(roots))
