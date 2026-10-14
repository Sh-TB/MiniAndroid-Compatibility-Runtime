#!/usr/bin/env python3
"""cont59_registry.py — CONT-59 registry update (647 -> 649).

F-NEW-337: ROOT-CAUSED-FIXED — the declarative Spinner (android:entries)
law. A Spinner whose adapter comes from the XML entries attribute (AOSP
AbsSpinner constructor builds the ArrayAdapter internally — NO DEX call)
rendered zero content: the engine never parsed the entries attr, so the
selected item (default index 0) never reached the node's visible text and
the generic text pipeline had nothing to paint (measured face: BMI v402's
weight/height spinners text='' at 817x105, left half of the form empty).

F-NEW-337b: ROOT-CAUSED-FIXED — the theme-attribute ColorStateList item
law. A <selector> item whose android:color is a THEME ATTRIBUTE reference
(?attr/colorForeground — TypedValue TYPE_ATTRIBUTE, id 0x0101xxxx; the
AOSP framework text_color_primary.xml default item) was dereferenced as a
RESOURCE id through the ARSc table: resolve_full read the attr-DEFINITION
row (an INT format byte) and its data painted as ARGB → RGBA(0,0,16,0) —
alpha-0, every glyph blended away (gmdice 'Push buttons to roll!' hint
line + the BMI spinner text color). AOSP law: ColorStateList item colors
that are theme attrs resolve through the theme service, never the table.
"""
import json

REG = "/home/z/my-project/root_registry.json"

with open(REG) as f:
    reg = json.load(f)
roots = reg["roots"] if isinstance(reg, dict) and "roots" in reg else reg

existing_ids = {r["id"] for r in roots}
assert "F-NEW-337" not in existing_ids and "F-NEW-337b" not in existing_ids, \
    "ID collision — check upstream first"
assert len(roots) == 647, f"expected 647 roots, got {len(roots)}"

e337 = {
    "id": "F-NEW-337",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P0",
    "layer": "resources/inflater-spinner-entries",
    "title": "Declarative Spinner content (android:entries) was never parsed: a Spinner whose adapter is built by the WIDGET CONSTRUCTOR from the XML entries array (AOSP AbsSpinner ctor -> ArrayAdapter.createFromResource -> setAdapter — no DEX call, no [ARRAY-ADAPTER] trace) rendered zero content. The engine's attr dispatcher had no entries branch, the array never resolved, the selected item (AOSP default index 0) never reached node.text, and the generic text pipeline painted nothing (BMI v402: weightSpinner/heightSpinner 817x105 at (0,315)/(0,470), text='', left half of the form empty while the right-half EditTexts rendered).",
    "root_cause": "Evidence chain (com.zola.bmi v402, binary 06a08f7aadb3d402 at a212cbad): (a) U007_LAYOUT_DEBUG=2 — view 260/261 Landroid/widget/Spinner; measured=817x105, children=0, text=''; (b) the fragment inflates res/layout/fragment_bmimain.xml whose <Spinner> elements carry ONLY entries/id/layout_* attrs — no DEX adapter code exists (BMIMain$PlaceholderFragment.onCreateView is inflate-only); (c) AXML decode: entries REF 0x7f020001/0x7f020000 (R.array.weight_units/height_units); (d) the arrays exist ONLY as compiled ARSc complex entries ('Kilograms'/'Pounds', 'Centimetres'/'Inches' — no res/values files in the APK); (e) the canonical getStringArray law resolve_string_array (F-NEW-319) already resolves them. FIX (one generic site, zero app knowledge): layout_inflater.cpp attr dispatcher — entries branch: on a REFERENCE value call arsc_.resolve_string_array(ref_id) and write the SELECTED item (index 0, the AOSP default face) into a.text, which flows through the existing node.text -> layout_text -> TextShaper pipeline unchanged.",
    "next_wave": "BMI spinner nodes now carry the real selected items (U007: text='Kilograms' / text='Centimetres'). The remaining BMI spinner-visibility blocker moved downstream and is its own root: the resolved item color is the themed ?attr/colorForeground chain (F-NEW-337b) = themed white for this app's dark Material base theme, which paints over the engine's GREY_200 container fill — invisible white-on-light. Named next root: the EXP-092 GREY_200 visibility fill vs the AOSP transparent-container law (window background shows through) — blast-radius measured on the anchor corpus (tanana/simplecalc/opencalc/microtimer/unote faces contain 124k-1.9M fill pixels each) so it ships as its own wave with per-anchor raw-diff audits.",
    "evidence": [
        "evidence/cont59/bmi_f337_before_after.png (b52252c2 vs fe190527 faces)",
        "run/cont59_bmi_f337b.log (U007 spinner text='Kilograms'/'Centimetres')",
        "run/cont59_axml_dump.txt (fragment_bmimain.xml element/attr decode)",
        "scripts/cont59_axml.py (binary AXML element/attr dumper)",
        "scripts/cont59_registry.py (this update: 647 -> 649)",
    ],
}

e337b = {
    "id": "F-NEW-337b",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P0",
    "layer": "resources/theme-attr-csl-item-color",
    "title": "A ColorStateList <selector> item whose android:color is a THEME ATTRIBUTE reference (?attr/… — TypedValue TYPE_ATTRIBUTE, id 0x0101xxxx) was dereferenced as a RESOURCE id through the ARSc table: resolve_full() read the attr-DEFINITION row (an INT format byte) and its data was painted as ARGB → RGBA(0,0,16,0) — alpha-0, every glyph pixel src-over blended away. AOSP law: ResourcesImpl.loadColorStateList resolves item colors that are theme attributes through the THEME (obtainStyledAttributes), never the resource table. The measured framework file: text_color_primary.xml default item = android:color='?attr/colorForeground' (0x01010030) + android:alpha='?attr/primaryContentAlpha' (0x01010552) — byte-verified upstream AOSP 2017 selector.",
    "root_cause": "Evidence chain (binary c0162daeaee55a10): (a) gmdice v8 regressed from f3b483fe7b7cf51b after F-NEW-337 — raw-diff (old binary 06a08f7a re-built via stash) proved EXACTLY one changed region (62,1155)-(1020,1332), 18923 px, white glyphs appearing; (b) MINIANDROID_S109_BITMAP: draw 'Push buttons to roll!' color=(255,255,255,255) post-fix — the hint line was invisible pre-fix; (c) BMI spinner draw traced color=(0,0,16,0) — the alpha-0 smoking gun (S109-SHAPE on the pre-337b binary); (d) the consumed selector = framework_res/res/color/text_color_primary.xml with items color=?attr/0x01010030 (colorForeground), matching docs/upstream/aosp/res_color/text_color_primary.xml byte-for-byte in structure; (e) S124-ATTRRAW: attr=0x1010030 type=28 data=0xffffffff — the theme answers colorForeground (the old deref returned the attr-def INT 16 instead). FIX (two generic sites, zero app knowledge): resource_runtime.cpp resolve_framework_file_color() deref lambda + resolve_apk_file_color() item loop — when the item color ref is 0x0101xxxx (TYPE_ATTRIBUTE), resolve through resolve_theme_attr_typed() and accept int/color answers with the F-NEW-336 type law (a STRING res/color/… path recurses through the app-package file law; anything else is an honest nullopt → legacy fallback).",
    "next_wave": "gmdice healed: the hint line renders themed white (new gate face 3891679dff449331 x3, re-pinned in cont37_regression.sh from f3b483fe7b7cf51b; RAW-diff-proven single-region change = REAL_APP_CONTENT retained). BMI spinner text now carries the CORRECT themed color (white per the app's dark Material base theme) — visible-once the container-fill law lands. Named next roots: (1) EXP-092 GREY_200 container fill vs the AOSP transparent-container law (window background shows through) — makes BMI's white-on-light spinner text visible AND fixes dark-theme contrast corpus-wide (measured blast radius: tanana 1.9M, simplecalc 614k, opencalc 272k, microtimer 124k, unote 166k fill pixels); (2) BMI row-weight squeeze, (3) alex androidx-nav chain, (4) OpenCalc srcCompat vector-drawable decode (F-NEW-309 family), (5) dooz Compose draw path (F-NEW-256) + tap bridge (F-NEW-267).",
    "evidence": [
        "evidence/cont59/gmdice_f337b_before_after.png (hint line before/after)",
        "evidence/cont59/bmi_f337_before_after.png",
        "run/cont59_gmdice_trace.log (S109-SHAPE 'Push buttons to roll!' white post-fix)",
        "run/cont59_gmdice_old2.log + run/cont59_gmdice_old2/screenshot.png (base-binary face f3b483fe7b7cf51b)",
        "run/cont59_gmdice_new/screenshot.png (new face 3891679dff449331)",
        "docs/upstream/aosp/res_color/text_color_primary.xml (the upstream law)",
        "scripts/cont59_registry.py (this update: 647 -> 649)",
    ],
}

roots.append(e337)
roots.append(e337b)
if isinstance(reg, dict):
    reg["total_roots"] = len(roots)

with open(REG, "w") as f:
    json.dump(reg, f, indent=1, ensure_ascii=False)
print(f"registry updated: {len(roots)} roots (647 -> 649); F-NEW-337 + F-NEW-337b appended")
