#!/usr/bin/env python3
"""S38: register R-NEW-336 (ScrollView-child post-click setText renders empty)."""
import json

REG = "/home/z/my-project/root_registry.json"
reg = json.load(open(REG))
if any(r.get("id") == "R-NEW-336" for r in reg["roots"]):
    print("R-NEW-336 already present")
    raise SystemExit(0)

entry = {
    "id": "R-NEW-336",
    "status": "OBSERVED-FAIL",
    "priority": "P1",
    "fg": True,
    "evidence": ("S38 OBSERVED (hello_widgets advanced fixture, aapt2-linked APK "
                 "461436b1d7282ab2108ac29eb9b1c03b737e12258887fdaf0aac811ccb764185): "
                 "probe-click (phase_b, EXP088) hits the only clickable Button; "
                 "MainActivity.onClick executes END-TO-END as real DEX ([TRY-ENTRY] chain in "
                 "s38 hw_diag run log): EditText.getText -> String.length -> "
                 "StringBuilder.<init>/append/toString -> TextView.setText -> TextView.invalidate. "
                 "RESULT: the target TextView's line renders EMPTY in the final frame — its "
                 "pre-click default text (AXML @string) ALSO vanishes (pixel-scan: rows 855-930 "
                 "uniform background in baseline; the same line visible pre-click in the --tap run "
                 "where the probe is skipped and the scripted tap misses the button). ISOLATION: "
                 "(1) not the concat — static setText(\"ECHO-STATIC\") clears too (run hw_static); "
                 "(2) not getText().toString() — removed, still clears (run hw_nogettext); "
                 "(3) not invalidate() — removed, still clears (run hw_noinv). CONTRAST: the "
                 "IDENTICAL chain under a LinearLayout root renders (hello_smoke probe click -> "
                 "counter/box/storageEcho all visibly updated, count=1/pref_now=1/box#1 on screen, "
                 "SHA f7502490def40523). Structural delta = ScrollView root (AXML-inflated) vs "
                 "LinearLayout root. FAMILY: ScrollView-child invalidation/redraw after "
                 "click-dispatch (draw pass reads the node in a state where text glyphs are gone). "
                 "NEXT: (1) trace ViewLayer/software_renderer glyph path for the echo node at draw "
                 "time (is node->text empty or is the draw skipped); (2) compare "
                 "ViewShadow::set_text caller ids — verify the setText receiver id equals the "
                 "inflated echo node id; (3) minimal repro: ScrollView>LinearLayout>TextView + "
                 "Button probe-click fixture (no EditText, no ImageView, no Table). FIX LAW "
                 "CANDIDATE: ScrollView re-measure of invalidated child before final draw."),
    "commit": "S38-NEW",
}
reg["roots"].append(entry)
json.dump(reg, open(REG, "w"), indent=1, ensure_ascii=False)
print("R-NEW-336 registered; total roots =", len(reg["roots"]))
