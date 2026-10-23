#!/usr/bin/env python3
"""CONT-14 batch-4 registry update — F-NEW-519 (id-unique append, no inflation).

F-NEW-519: TextView.getTextColors() had NO engine law -> NULL -> the
census-recurring (x2) face NPE 'ColorStateList.getDefaultColor on a null
object reference' at PagerTitleStrip.<init> pc=138 (DEX truth 0x114 bytes:
iget mCurrText -> TextView.getTextColors -> getDefaultColor -> iput
mTextColor). AOSP TextView.java: mTextColor field initializer
ColorStateList.valueOf(0xFF000000) => getTextColors NEVER null; the F-NEW-301
getter default law supplies the renderer-parity color.
"""
import json

REG = "/home/z/my-project/root_registry.json"
d = json.load(open(REG))
roots = d["roots"] if isinstance(d, dict) and "roots" in d else d
ids = {r["id"] for r in roots}
assert "F-NEW-519" not in ids, "F-NEW-519 already registered — no double-land"

entry = {
    "id": "F-NEW-519",
    "title":
    "TextView.getTextColors() had NO engine law -> answered NULL -> the "
    "census-recurring x2 face (batterymonitor + fossify_notes family) died "
    "with NPE \"Attempt to invoke virtual method "
    "'Landroid/content/res/ColorStateList;.getDefaultColor' on a null object "
    "reference\" at Landroidx/viewpager/widget/PagerTitleStrip;.<init> pc=138. "
    "DEX truth machine-verified from the APK bytes (androguard, "
    "scripts/cont14_pager_dex_truth.py): iget-object mCurrText -> "
    "invoke-virtual TextView.getTextColors() @0x10c -> move-result-object -> "
    "invoke-virtual ColorStateList.getDefaultColor() @0x114 -> iput mTextColor "
    "(0x114 bytes = 138 16-bit code units — the census pc is EXACT). AOSP "
    "TextView.java law (source-first): `private ColorStateList mTextColor = "
    "ColorStateList.valueOf(0xFF000000);` FIELD INITIALIZER guarantees "
    "getTextColors() NEVER returns null for a live TextView; setTextColor(int) "
    "replaces mTextColor with valueOf(color); setTextColor(ColorStateList) "
    "stores the object. FIX (read-side only, no setter change, zero renderer "
    "coupling, dalvik_engine.cpp bridge_to_api): (1) captured CSL object "
    "(ViewNode.text_color_state_object, the setTextColor(ColorStateList) arm) "
    "still a live ColorStateList -> return THAT object (identity contract); "
    "(2) else valueOf arm: recorded text_color (explicit runtime OR "
    "style-resolved) -> csl_wrap_single(recorded color) — renderer parity with "
    "the F-NEW-301 getCurrentTextColor law; UNSET -> the field-initializer "
    "black / Button-family white. VERIFY (binary feee06117f0e7c3c, head "
    "717e0058 + this law): batterymonitor PagerTitleStrip NPE face GONE — the "
    "app materializes its REAL UI tree (LinearLayout -> ViewPager -> "
    "PagerTitleStrip children=3: HISTORY/CURRENT STATE/ALARMS TextViews, "
    "PARTIAL SUCCESS, non-killing F-016 provider faces ledgered: Shizuku/Sui "
    "provider init + AppLocalesMetadataHolderService getServiceInfo "
    "NameNotFoundException — CAUGHT by the F-NEW-518 chain (androidx logs "
    "'Service not found') and rethrown as the AOSP IllegalStateException); "
    "fossify_notes 0 uncaught (was: census CSL face + F084 budget halts), "
    "stable past splash into MainActivity (next face = the corpus-wide "
    "APP_DRAW_OPS draw-path frontier); pre-fix anchor battery at the rebuilt "
    "HEAD binary 5/5 EXACT (chess a0319686/opencalc 63020bc7/microtimer "
    "bbd350b6/unote 7481e9b4/tower3d 11a38a5a — byte-SHA drift of the fresh "
    "container rebuild honestly flagged, anchor-PROVEN semantically "
    "faithful); post-fix anchors re-run in evidence/cont14/.",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P0",
    "layer": "framework-textview",
}
roots.append(entry)
if isinstance(d, dict) and "roots" in d:
    d["roots"] = roots
json.dump(d, open(REG, "w"), indent=1, ensure_ascii=False)
ids2 = [r["id"] for r in roots]
print(f"registry: {len(roots)} roots, unique={len(set(ids2))}, "
      f"ID_UNIQUE={len(ids2)==len(set(ids2))}")
