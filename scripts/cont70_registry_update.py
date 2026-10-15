#!/usr/bin/env python3
"""cont70 registry update — ant-army wave ledger.

Changes (no id collisions, metadata recomputed):
  F-NEW-368  CLASSIFIED      -> CLASSIFIED (title gains the delivery-chain
                               decode: the subtype-table miss + the proven
                               in-frame handler + the F-NEW-370 activation
                               blocker)
  F-NEW-276  CLASSIFIED      -> SUPERSEDED-BY-EVIDENCE (doubling gone at HEAD;
                               honest first-run DataStore ENOENT, app-caught;
                               the source bug was F-NEW-293, fixed)
  F-NEW-161  OBSERVED-FAIL   -> SUPERSEDED-BY-EVIDENCE (closed by F-NEW-363's
                               Settings static-Uri law; live proof 0 SGET-MISS,
                               face == CONT-67 record fe3ae1167c9e968c)
  R-NEW-228  OBSERVED-FAIL   -> ROOT-CAUSED-FIXED (Window.setDecorFitsSystem
                               Windows accept+record law; dooz face unchanged)
  F-NEW-370  (NEW, CLASSIFIED, P1) CoordinatorLayout DEX-measure chain
  F-NEW-372  (NEW, ROOT-CAUSED-FIXED, P2) canvas drawText real-size + face
                               carry (F-NEW-226 state read + setTypeface +
                               Typeface.createFromAsset family)
"""
import json
from collections import Counter

PATH = "/home/z/my-project/root_registry.json"
r = json.load(open(PATH))
roots = r["roots"]
by_id = {x["id"]: x for x in roots}
assert len(by_id) == len(roots), "duplicate ids in registry"

def set_fields(x, **kw):
    for k, v in kw.items():
        x[k] = v

# ── F-NEW-368: keep CLASSIFIED, record the delivery-chain decode ──────
x = by_id["F-NEW-368"]
x["title"] = (
    "Deferred synthesized exceptions do not deliver to the SAME-FRAME catch "
    "(cont70 decode COMPLETE): the miss was is_exception_subtype's builtin "
    "parent table — NoSuchMethodException (and the whole reflective family) "
    "was unwalkable, so the typed catch(Ljava/lang/Exception;) at "
    "CoordinatorLayout.getResolvedLayoutParams pc=67 (try [0x3c..0x52) "
    "CONFIRMED covering the throw pc via DEX try-table decode) never matched "
    "and the F106 took the deferred frame unwind. The delivery LAW itself is "
    "proven working: with the table entries added, the row reads 'deferred "
    "handler @0x53 type=Ljava/lang/Exception;' and the app's own catch runs "
    "(rows 42->2, mBehaviorResolved=true path). ACTIVATION BLOCKED by "
    "F-NEW-370: with in-frame delivery live, the DEX CoordinatorLayout."
    "onMeasure completes and its MATCH_PARENT child measure answers the "
    "AppBar height (105px) -> zero-height ViewPager/rows -> memory face "
    "regresses to blank dark. Fix pair owed: subtype table + F-NEW-370; "
    "reverted for this wave (zero drift held).")
x["verified_current"] = True
x["evidence"] = (
    "run/cont70/baseline/mem_f106.err (42 uncaught rows, pc=67); "
    "run/cont70/accept/mem_1.err (delivery proven: handler @0x53 type="
    "Ljava/lang/Exception;, face 6da289aab14d2256 = the F-NEW-370 face); "
    "run/cont70/accept/v2_mem/screenshot.png (record face c559b630dd8f0f0f "
    "restored after revert); scripts/cont70_ant1_decode.py + "
    "cont70_ant1_decode2.py (DEX try-table decode)")

# ── F-NEW-276: SUPERSEDED-BY-EVIDENCE ─────────────────────────────────
x = by_id["F-NEW-276"]
x["status"] = "SUPERSEDED-BY-EVIDENCE"
x["title"] = (
    "SUPERSEDED-BY-EVIDENCE (cont70): the data-path duplication face no "
    "longer reproduces at HEAD — dooz 90s cold + warm runs show ZERO doubled "
    "prefixes (was 'runtime/data/data/data/<pkg>/runtime/data/...' x15); the "
    "source bug was the F-NEW-293 relative-host-spelling minting (fixed). "
    "The residual single-anchored ENOENT on first run (settings.preferences_"
    "pb) is the HONEST DataStore first-launch read, app-caught (deferred "
    "handler @0x54 FileNotFoundException); the write side is owned by the "
    "app's later machinery (F-NEW-277 recomposition-scheduling territory).")
x["evidence"] = (
    "run/cont70/baseline/dooz_ant2.err + dooz_ant2_warm.err (doubled=0 both, "
    "1 honest app-caught ENOENT each)")

# ── F-NEW-161: SUPERSEDED-BY-EVIDENCE (closed by F-NEW-363) ──────────
x = by_id["F-NEW-161"]
x["status"] = "SUPERSEDED-BY-EVIDENCE"
x["title"] = (
    "SUPERSEDED-BY-EVIDENCE (cont70 ledger ant): the null-Uri producer was "
    "Settings$System.DEFAULT_RINGTONE_URI SGET-MISS — closed by F-NEW-363's "
    "Settings default-sound static law (CONT-67). Live re-proof at the cont70 "
    "binary: chessclock 0 SGET-MISS, 0 Uri NPE rows, face fe3ae1167c9e968c == "
    "the CONT-67 recorded REAL chess-clock face (rc=0, zero uncaught).")

# ── R-NEW-228: ROOT-CAUSED-FIXED ──────────────────────────────────────
x = by_id["R-NEW-228"]
x["status"] = "ROOT-CAUSED-FIXED"
x["title"] = (
    "R-NEW-228 FIXED (cont70 ANT-5): Window.setDecorFitsSystemWindows(boolean)"
    " — AOSP API 30 PhoneWindow law implemented as accept+record (the runtime "
    "has no system-bar inset dispatch; the window IS the whole display "
    "surface) in the Window attribute law family (getAttributes/setAttributes/"
    "requestFeature block). The residual [REC-MISS] diagnostic row is the "
    "standard framework-class DEX-lookup noise — the law answers beneath it "
    "(proven: the sibling getDecorView law prints [F023-PARENTLINK] under the "
    "same REC-MISS row shape). dooz face unchanged (31ddd4d5b8e6d18e == "
    "record, x3).")
x["evidence"] = (
    "run/cont70/accept/v2_dooz.err (face == record; F023 proof under the "
    "same-row shape); miniandroid/src/dex/dalvik_engine.cpp Window block")

# ── F-NEW-370: NEW frontier ───────────────────────────────────────────
roots.append({
    "id": "F-NEW-370",
    "status": "CLASSIFIED",
    "priority": "P1",
    "layer": "dex/view-measure (CoordinatorLayout child spec law)",
    "title": (
        "CoordinatorLayout.onMeasure DEX-COMPLETION measure chain (exposed by "
        "the F-NEW-368 in-frame delivery, cont70): when the app's own catch "
        "handles the F106 NoSuchMethodException in-frame, the DEX "
        "CoordinatorLayout.onMeasure runs to COMPLETION (in the deferred era "
        "every F106 aborted it -> [DEX-MEASURE] FAILED(no write-back) -> the "
        "engine default measure law produced correct sizes). The completed "
        "DEX onMeasure measures its MATCH_PARENT child (LinearLayout) at the "
        "AppBarLayout height (105px, not 1920-105) -> RelativeLayout/"
        "ViewPager/rows collapse to 0 height -> memory renders a blank dark "
        "face (6da289aab14d2256; real face c559b630dd8f0f0f). The child "
        "measure-spec law inside the DEX-executed onMeasure (getChildMeasure"
        "Spec semantics for MATCH_PARENT under CoordinatorLayout) is the "
        "named lever; closing it un-blocks the F-NEW-368 subtype-table "
        "activation (the pair must land together)."),
    "evidence": (
        "run/cont70/accept/mem_1.err ([EXP092-RENDER] Toolbar 0x147, ViewPager"
        " 1080x0, 'Easy' 0x0, 'New Game' 922x0); run/cont70/baseline/mem_f106."
        "err ([DEX-MEASURE] ... FAILED(no write-back) rows = the deferred-era "
        "abort that masked this chain); screenshot hashes in both paths"),
    "probe": "upload/canonical_apks/org.secuso.privacyfriendlymemory_100.apk",
    "date": "2026-10-15",
})

# ── F-NEW-372: NEW fixed law family ───────────────────────────────────
roots.append({
    "id": "F-NEW-372",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P2",
    "layer": "graphics/canvas-text + fonts/Typeface family",
    "title": (
        "CANVAS TEXT REAL-SIZE + APP-FACE FAMILY (cont70 ANT-3/6): three "
        "generic laws. (1) org.json JSONObject.keys() — AOSP insertion-"
        "ordered Iterator<String> via the F-237 legacy box (keys ride "
        "array[i] + __array_length__ on the box); was null -> bouncy "
        "JSONUtils.mapFromJSONObject hasNext NPE at pc=9 -> field layout "
        "never loaded. Post-fix bouncy renders its COMPLETE menu face "
        "(1b87e9efa9c32198, was dd0c14257fa1f2af without the top "
        "'Touch to start' bar; uncaught rows 11->3; deterministic x3). "
        "(2) Typeface.createFromAsset/createFromFile — resolves the startup-"
        "registered app face by APK-entry name (FIX-4/F-NEW-315 scan) into a "
        "real Typeface heap object (__font_face_idx__); missing asset throws "
        "RuntimeException('Font asset not found') per AOSP. Paint.setTypeface "
        "carries the face into the paint state; Canvas replay passes it to "
        "TextShaper.draw. (3) Canvas drawText REAL SIZE — the F-NEW-226 law "
        "handles Paint.setTextSize BEFORE the shadow layer (heap field "
        "__text_size_px__) so paint_text_size_ stayed empty and every "
        "canvas-drawn text fell to the tiny legacy bitmap font; the drawText "
        "recorder now reads the F-NEW-226 state first-class. App-visible "
        "improvements with deterministic x3 before/after: g2048 "
        "59ca1526611c4622 -> f43face08299ffc6 (real SCORE header + tile "
        "digits + button labels), tttdeluxe af6094295ecb50e3 -> db1d633d77b58"
        "19a (real score chips + YOUR MOVE + numpad + buttons). Probe: "
        "fixtures/font_probe (aapt2+ECJ+D8; same-string two-face draw: ink "
        "geometries differ 336x58 vs 412x62; 'NOFACE' absent = factory law "
        "live; tiny-text before-face preserved)."),
    "evidence": (
        "evidence/cont70/ (before faces + font probe rows); "
        "run/cont70/accept/font_probe5; run/cont70/wall_sweep/{g2048,tttdeluxe}"
        "_r1..r3; run/cont70/accept/v2_bouncy; fixtures/font_probe; "
        "scripts/cont70_build_font.sh"),
    "date": "2026-10-15",
})

# metadata recompute
r["total_roots"] = len(roots)
r["count"] = len(roots)
cnt = Counter(x["status"] for x in roots)
r["status_counts"] = dict(cnt)
r["generated"] = "2026-10-16T00:00:00Z"

ids = [x["id"] for x in roots]
assert len(set(ids)) == len(ids), "collision after append"
json.dump(r, open(PATH, "w"), indent=1, ensure_ascii=False)
print("registry roots:", len(roots))
print("new:", [i for i in ids if i in ("F-NEW-370", "F-NEW-372")])
print("statuses:", by_id["F-NEW-368"]["status"], by_id["F-NEW-276"]["status"],
      by_id["F-NEW-161"]["status"], by_id["R-NEW-228"]["status"])
