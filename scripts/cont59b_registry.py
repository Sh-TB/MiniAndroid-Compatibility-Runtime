#!/usr/bin/env python3
"""cont59b_registry.py — CONT-59 registry update (649 -> 650).

F-NEW-338: ROOT-CAUSED-FIXED — the transparent-container law. The EXP-092
GREY_200 visibility fill painted (225,225,225) behind every background-less
non-fullscreen container, overriding the theme windowBackground that the
EXT01 law had already painted on the framebuffer. Under a dark theme the
fill produced a LIGHT slab: BMI's themed WHITE spinner text (F-NEW-337/
337b chain — correct AOSP color per the app's dark Material base theme)
was invisible white-on-light. AOSP law (View.java draw, completing
R-NEW-336): a View with NO background is TRANSPARENT — the window
background shows through; a container is never an opaque grey slab.
"""
import json

REG = "/home/z/my-project/root_registry.json"

with open(REG) as f:
    reg = json.load(f)
roots = reg["roots"] if isinstance(reg, dict) and "roots" in reg else reg

existing_ids = {r["id"] for r in roots}
assert "F-NEW-338" not in existing_ids, "ID collision — check upstream first"
assert len(roots) == 649, f"expected 649 roots, got {len(roots)}"

entry = {
    "id": "F-NEW-338",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P0",
    "layer": "renderer/container-transparency",
    "title": "The EXP-092 GREY_200 visibility fill painted (225,225,225) behind every background-less non-fullscreen CONTAINER, overriding the theme windowBackground the EXT01 law had already painted — under a dark theme the content area became a LIGHT slab (BMI: themed WHITE spinner text from the F-NEW-337/337b chain sat on the light fill and was invisible; the ancestor_has_bg exception never saw the WINDOW bg because the window is not a ViewNode). AOSP law (View.java, completing R-NEW-336): a View with NO background is TRANSPARENT — the window background shows through. The fill's visibility purpose remains for LEAF views (C013 diagnostic law).",
    "root_cause": "Evidence chain (binary c0162daeaee55a10 → 90e0112c1face89b): (a) BMI post-F-NEW-337/337b spinner regions were uniform (225,225,225) with zero dark/light glyph pixels although the draw pass painted 'Kilograms'/'Centimetres' white every frame — the white glyphs blended INTO the light fill; (b) the fill fired in the execution_engine draw walk's container branch (is_container && !is_full_screen && !ancestor_has_bg → GREY_200); (c) pixel census of the whole anchor corpus measured the fill's blast radius BEFORE the fix: tanana 1.9M px, simplecalc 614k, opencalc 272k, unote 166k, microtimer 124k, flappycow 24. FIX (one site): the container branch no longer paints — a bg-less container is transparent and the theme windowBackground (EXT01 fb.clear) shows through.",
    "next_wave": "Per-face RAW-DIFF audits (old binary re-built via stash to the byte-exact c0162daeaee55a10; all five recorded faces reproduced byte-exactly first): microtimer da73010a→55343bbe (region y=951-1076: fill 225 → winbg 255,255,255; zero content px lost), unote 4f1a9e4e→90a67cc1 (top band y=0-153: 225 → default dark 48,48,48; band empty both sides), opencalc 0ae271c4→b7a7fe8e (content y=499+: 225 → 48,48,48 = the app's dark Material window; the pad's own blue cells + white glyphs unchanged; the previously hidden empty pad cell now honest), tanana 601e0219→afe0bd8d (1.94M px: 225 → 250,250,250 = the app's 0xfffafafa window; text re-blended (29→32) — all five preference rows visible), simplecalc 950b955c→341b9cec (225 → 250; display + pad unchanged). BMI spinner labels 'Kilograms'/'Centimetres' now VISIBLE (white themed text on the app's real dark window). Gate: 33/33 MATCH at 90e0112c1face89b (5 faces re-pinned with rationale in cont37_regression.sh); probes == records.",
    "evidence": [
        "evidence/cont59/f338_faces_review.png (six-face review grid)",
        "evidence/cont59/unote_f338_topband.png (band empty both sides — no content lost)",
        "evidence/cont59/bmi_f337_before_after.png + run/cont59_bmi_338/screenshot.png (BMI visible spinner labels)",
        "run/cont59_338audit/ (all ten audit faces old/new + logs)",
        "scripts/cont59b_registry.py (this update: 649 -> 650)",
    ],
}

roots.append(entry)
if isinstance(reg, dict):
    reg["total_roots"] = len(roots)

with open(REG, "w") as f:
    json.dump(reg, f, indent=1, ensure_ascii=False)
print(f"registry updated: {len(roots)} roots (649 -> 650); F-NEW-338 appended")
