#!/usr/bin/env python3
"""cont58_registry.py — CONT-58 registry update (646 -> 647).

F-NEW-336: ROOT-CAUSED-FIXED — the app-package file-backed ColorStateList
law. A theme COLOR attr (the measured case: android:textColorPrimary
0x01010036 in tananaev v1.10's appcompat theme) resolved through the base
Theme to a STRING value carrying a res/color/… file path of the APP
package (abc_primary_text_material_light.xml — an appcompat LIBRARY file).
The S127 file law only consults the FRAMEWORK router (find_id MISS — the
framework table legitimately has no abc_* row), so the raw value returned
untouched and the engine's textColorPrimary consumer cast the string-pool
INDEX (0x61 = 97) as ARGB → RGBA(0,0,97,0) → alpha-0 → every glyph pixel
blended away. This also refines F-NEW-308: the S57-B textSize hypothesis
is refuted at HEAD — the 14sp fallback measured 36.75px and shaped 20 real
glyphs; the invisible COLOR was the blocker.

F-NEW-308: DUPLICATE-SUPERSEDED — same symptom, real root = F-NEW-336.
"""
import json

REG = "/home/z/my-project/root_registry.json"

with open(REG) as f:
    reg = json.load(f)
roots = reg["roots"] if isinstance(reg, dict) and "roots" in reg else reg

existing_ids = {r["id"] for r in roots}
assert "F-NEW-336" not in existing_ids, "ID collision — check upstream first"
assert len(roots) == 646, f"expected 646 roots, got {len(roots)}"

superseded = 0
for r in roots:
    if r["id"] == "F-NEW-308":
        r["status"] = "DUPLICATE-SUPERSEDED"
        r["title"] = (
            r["title"]
            + " [CONT-58 REFINEMENT/SUPERSEDE: the textSize=0 hypothesis is"
            " REFUTED at HEAD — MINIANDROID_S109_BITMAP proved the rows"
            " shaped 20 real glyphs at 36.75px (14sp x 2.625 density"
            " fallback) and TextShaper::draw was called every pass; the"
            " blocker was the resolved text COLOR. Real root = F-NEW-336"
            " (app-package file-backed ColorStateList law).]"
        )
        superseded += 1
assert superseded == 1, f"expected exactly one F-NEW-308, touched {superseded}"

entry = {
    "id": "F-NEW-336",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P0",
    "layer": "resources/theme-attr-color-csl-app-package",
    "title": "The theme COLOR attr consumer law was missing two generic legs: (1) APP-PACKAGE FILE-BACKED COLORSTATELIST — a theme attr whose base-Theme answer is a STRING carrying a res/color/… path of the APP package (appcompat/Material library files: abc_primary_text_material_light.xml et al.) was only ever resolved through the FRAMEWORK router (S127 find_id — which legitimately has no abc_* row); the raw STRING returned untouched and (2) the ENGINE textColorPrimary consumer cast the value's data DIRECTLY as ARGB without a type check — for the measured case the string-pool INDEX 0x61 became RGBA(0,0,97,0): alpha-0, every glyph pixel src-over-blended away, rows painted nothing while the shape stage ran at full fidelity. AOSP law: ResourcesImpl.loadColorStateList is package-routed (app table first for 0x7f ids), and a TypedValue handed to a color consumer is always a terminal color/int — never a raw string index.",
    "root_cause": "Evidence chain (tananaev v1.10, binary c8b078ba88ca255d at bebb7cd4): (a) U007_LAYOUT_DEBUG=2 — the five preference rows are real TextViews at real geometry (1080x44 @ y=126/170/214/258/302) with real text ('Notification settings', 'Ongoing notification', 'Calculator Notification can not be dismissed', 'Lock screen notification', 'Show Calculator Notification on lock screen'); (b) pixel census: row band uniformly (225,225,225), dark_glyph_samples=0; (c) MINIANDROID_S109_BITMAP — draw 'Notification settings' glyphs=20 avail=1 size=36.75 color=(0,0,97,0) — the shape stage was FINE, the color was alpha-0 garbage; (d) MINIANDROID_THEME_DIAG — attr=0x1010036 -> BASE type=3 data=0x61 (STRING, string-pool index 97); the S127 branch fired and find_id color/abc_primary_text_material_light -> MISS (framework table has no appcompat rows); (e) ATTRRAW diag — str='res/color/abc_primary_text_material_light.xml' (the file IS in the app APK, 464-byte binary AXML <selector>); (f) RECT-TRACE — GREY_200 container fills painted UNDER the text; z-order was never the cause. FIX (three generic sites, zero app knowledge): resource_runtime.cpp resolve_apk_file_color() — extract the res/color/… entry from the APK itself, parse_state_list, default-state tri-match (window_focused=true, enabled=true, pressed/selected/checked/activated=false), in-item @color refs deref through the APP table (bounded depth 4); resolve_theme_attr_typed() S127 branch — on framework-router MISS, the app-package file law answers and the value is re-typed INT_HEX; execution_engine.cpp textColorPrimary consumer — TYPE LAW: only is_int()/is_color() answers paint as ARGB, any other type falls back to the legacy default (a string-pool index must never render as a color).",
    "next_wave": "tanana rows healed: dark_glyph_samples 0 -> 4420; all five preference rows render real text at (29,29,29) = the resolved abc_primary_text_material_light default-state color; new gate face 601e0219d4cab10b x3 deterministic (re-pinned in cont37_regression.sh from 5f7e0114c3bfd6b5). Fan-out measured: simplecalc display '0' gained (RAW-diff-proven: the ONLY changed pixels in the 1080x1920 face are the 0-glyph bbox (1059-1078, 481-507); face 950b955c6999d72a x3, re-pinned from e847ca0346708f07); BMI b52252c2de19b03a and alex c8d69f811b23f245 byte-identical (their text colors resolve through other paths). Zero-drift regression: anchors 27/27 (8 other faces byte-identical) + csw 3/3 (3442d9a9) + dooz180 3/3 (6841d52a); probe battery == records (21 probes incl. f259g 84/7 + fnew302 48/24 documented) + fnew322 5/0 + fnew326/326b 13/0 + fnew327 3/0 + fnew328 4/0 x3. Remaining named roots: BMI row-weight squeeze + Spinner content law, alex androidx-nav chain (ISE 'Fragment null has not been attached yet'), OpenCalc srcCompat vector-drawable decode (F-NEW-309 family), dooz Compose draw path (F-NEW-256 frontier) + Compose tap bridge (F-NEW-267).",
    "evidence": [
        "evidence/cont58/tanana_rows_before.png (blank-bar face, binary c8b078ba88ca255d)",
        "evidence/cont58/tanana_rows_fixed.png (post-fix: all five rows real text)",
        "evidence/cont58/simplecalc_old_new.png (raw faces; only the display 0 changed)",
        "evidence/cont58/CONT58_RESULT.md (full decode chain + regression ledger)",
        "run/cont58/trace1.log (RECT-TRACE: GREY_200 fills under text; z-order excluded)",
        "run/cont58/trace2.log (S109-SHAPE color=(0,0,97,0) — the alpha-0 smoking gun)",
        "run/cont58/trace3.log (S124-THEME attr=0x1010036 -> BASE type=3 data=0x61 + S127-CSL find_id MISS)",
        "run/cont58/trace4.log (S124-ATTRRAW str='res/color/abc_primary_text_material_light.xml')",
        "run/cont58/sc_base (raw old simplecalc face e847ca0346708f07 on the stashed base binary)",
        "scripts/cont58_registry.py (this update: 646 -> 647, F-NEW-308 superseded)",
    ],
}

roots.append(entry)
if isinstance(reg, dict):
    reg["total_roots"] = len(roots)

with open(REG, "w") as f:
    json.dump(reg, f, indent=1, ensure_ascii=False)
print(f"registry updated: {len(roots)} roots (646 -> 647); F-NEW-308 superseded; F-NEW-336 appended")
