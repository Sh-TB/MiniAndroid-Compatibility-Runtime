#!/usr/bin/env python3
"""cont55_registry.py — CONT-55 registry update (637 -> 638).

F-NEW-327: ROOT-CAUSED-FIXED — the AOSP AttributeResolution DEF-STYLE
stages. The TypedArray producers (ContextShadow F-093 + the S101
Resources$Theme producer) walked only XML (1) + theme (5); the style
stages — (2) the tag's xml style= reference, (3) the defStyleAttr (the
theme's style reference), (4) the explicit defStyleRes — never ran, so
Widget.Design.NavigationView's android:maxWidth (the ONLY source of the
drawer width law) never resolved: NavigationView mMaxWidth answered the
caller default while the AT_MOST drawer spec took min(912, mMaxWidth)=0 →
the drawer measured 0x0 → the menu content never rendered.
"""
import json

REG = "/home/z/my-project/root_registry.json"

with open(REG) as f:
    reg = json.load(f)
roots = reg["roots"] if isinstance(reg, dict) and "roots" in reg else reg

existing_ids = {r["id"] for r in roots}
assert "F-NEW-327" not in existing_ids, "ID collision — check upstream first"
assert len(roots) == 637, f"expected 637 roots, got {len(roots)}"

roots.append({
    "id": "F-NEW-327",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P1",
    "title": "The AOSP AttributeResolution DEF-STYLE stages were missing from both TypedArray producers: the chain walked only XML (1) + theme (5); the style stages — (2) the tag's xml style= reference, (3) the defStyleAttr (the theme's style reference), (4) the explicit defStyleRes — never ran. Solitaire face: NavigationView.<init> mMaxWidth = getDimensionPixelSize(NavigationView_android_maxWidth, -1) via TintTypedArray → Context.obtainStyledAttributes(set, styleable, 0, R.style.Widget_Design_NavigationView) — the style (0x7f100180) carries the drawer android:maxWidth law; the style-stage miss answered the -1 default → onMeasure AT_MOST → min(912, mMaxWidth) = min(912, -1-style/0-runtime) = 0 → EXACTLY|0 → the drawer measured 0 wide → the menu content never rendered (the CONT-54 frontier).",
    "root_cause": "Three stacked gaps, all class-agnostic: (1) STAGES — no xmlStyle/defStyleAttr/defStyleRes resolution anywhere (the AOSP ApplyStyle order is XML → xmlStyle → defStyleAttr → defStyleRes → theme); the style-bag machinery existed (ArscParser::bag_value with the ResTable_map_entry parent chain) but no caller wired it. (2) ROUTING — the NavigationView ctor's TypedArray rides the S101 Resources$Theme producer (the appcompat ContextThemeWrapper chain), which had NO defStyle stages either. (3) ARG-CONVERSION — the bridge maps a literal-0 int arg to NULL_REF (kind 7), so the def-style pair extraction gated on Kind::INT dropped BOTH args (a2:k7=0 / a3:k0=0x7f100180 live evidence). FIX: resolve_def_style_attr_value(apk, attr, dSA, dSR, xmlStyle) on ResourceRuntime (style_probe = bag_value + REFERENCE deref, package-routed; DIMENSION → device px via complex_unit_to_dimension_pixel_size — the AOSP TypedArray getDimensionPixelSize contract), wired into BOTH producers with positional (INT-or-NULL_REF) extraction; the AOSP order XML → xmlStyle → defStyleAttr → defStyleRes → theme (the theme path kept verbatim as stage 5).",
    "next_wave": "Probe fnew327_probe.apk 57ec5cdf6806255c (real aapt2/ECJ/D8; res carries boxMax/boxMin attrs + F327_BoxStyle 280dp/48dp + a theme WITHOUT them — the style stage is the only source): PRE x3 on the CONT-54 binary ff261b1bc2940bc2 = P1 got=-1 FAIL / P2 got=-1 FAIL (the def channel survived, the style value lost); POST x3 on 6014ae17af2ecd60 = 3/0 (P1 got=735 = 280dp px-decoded, P2 got=126 = 48dp). Solitaire runtime: [SGET] NavigationView.<init> pc=24 Widget_Design_NavigationView=0x7f100180 (the DEX dSR value); the CS-PRODUCER array probe pinned the 10-attr NavigationView styleable call (attrs=[0x10100d4,0x10100dd,0x101011f(maxWidth),...]); POST [R347-MEASURE] view=298 NavigationView wspec=0x80000390 hspec=0x40000780 -> 735x1920 (was 0x0) and NavigationMenuView.setMeasuredDimension(735, 1920) — the FULL drawer measure chain is AOSP-faithful. Zero-drift gate on 6014ae17af2ecd60: 15 canonical anchors/controls x3 byte-identical (45/45 MATCH incl. dooz 31ddd4d5, BMI b52252c2, sol ba50a4d2); probe battery == records (fnew309 8/0, fnew320 7/0, fnew322 5/0, fnew323 6/0, fnew324 3/0, fnew325 4/0, fnew326 13/0). NEW frontier: the menu-content DRAW pipeline (the drawer layout/layers — NavigationMenuView at 735x1920 now lays out; the visible frame is unchanged because the closed drawer's pixels sit off-screen — the open-drawer flow is the next decode).",
    "evidence": "evidence/cont55/CONT55_RESULT.md",
})

for r in roots:
    if r["id"] == "F-NEW-309":
        prev = r.get("evidence", "")
        r["evidence"] = (prev.rstrip() + "; evidence/cont55/CONT55_RESULT.md"
                         if prev else "evidence/cont55/CONT55_RESULT.md")

with open(REG, "w") as f:
    json.dump(reg, f, indent=1, ensure_ascii=False)

from collections import Counter
reg["count"] = len(roots)
reg["total"] = len(roots)
reg["status_counts"] = dict(Counter(x.get("status", "UNKNOWN") for x in roots))
reg["meta"] = reg.get("meta", {})
reg["meta"]["last_update"] = ("CONT-55 session 2026-10-12: the AOSP AttributeResolution "
    "DEF-STYLE stages (F-NEW-327) — xmlStyle/defStyleAttr/defStyleRes wired into BOTH "
    "TypedArray producers (ContextShadow F-093 + S101 theme producer) with the "
    "NULL_REF positional-arg law; DIMENSION slots answer device px. Probe fnew327 "
    "PRE got=-1 x3 -> POST 3/0 x3 (280dp->735px). Solitaire: NavigationView 0x0 -> "
    "735x1920, menu view 735x1920 — the drawer measure chain is AOSP-faithful end to "
    "end. Zero-drift 15 anchors x3 + probe battery == records. Registry 637->638.")
reg["meta"]["last_updated"] = "2026-10-12 F-NEW-327 ROOT-CAUSED-FIXED at binary 6014ae17af2ecd60"
json.dump(reg, open(REG, "w"), indent=1, ensure_ascii=False)
print("registry updated: 637 -> 638 (F-NEW-327 appended ROOT-CAUSED-FIXED)")
