#!/usr/bin/env python3
"""CONT-107 registry update: F-NEW-447 FIXED, F-NEW-450 new FIXED,
F-NEW-451 new OPEN_GAP, F-NEW-452 new FIXED, F-NEW-448/449 honest refreshes.
764 -> 768 roots. main == mirror."""
import json, shutil

MAIN = "root_registry.json"
MIRROR = "canonical/root_cause_registry.json"

reg = json.load(open(MAIN))
roots = reg if isinstance(reg, list) else reg["roots"]
ids = {r.get("id") for r in roots}
assert len(ids) == len(roots), "id-unique violated pre-update"

def find(rid):
    for r in roots:
        if r.get("id") == rid:
            return r
    return None

# ── 1. F-NEW-447 → ROOT-CAUSED-FIXED ──────────────────────────────────
r = find("F-NEW-447")
assert r, "F-NEW-447 missing"
r["status"] = "ROOT-CAUSED-FIXED"
r["fix"] = ("FIXED (CONT-107): CALLER-DOMAIN GATE on the ROOT-059 route — the "
            "null-recv shadow routing applies only when the CURRENT FRAME is "
            "framework-owned (f141_is_framework_class(current_class_); unknown/"
            "empty caller frames keep the legacy route). App-DEX caller sites "
            "get the ART-faithful NPE (bounded [F447-NPE] marker). Probe POST "
            "(binary 3b5ca178710c171f): [C106-INVOKE2] NO-EXC -> NPE, all other "
            "c106a rows unchanged. Real-app: telegram face — the gate EXPOSED "
            "F-NEW-452 (Configuration.locale null) as an ART-faithful NPE at "
            "c41.run pc=66; after F-NEW-452 the telegram PNG is byte-identical "
            "to the pre-107 baseline (20ac8cbbbb692e63) with the marker silent. "
            "opencalc: zero [F447-NPE] rows (proof of zero changed calls). "
            "Full battery zero-drift on 1e3efdb4209764a9 (opencalc WANT "
            "re-pinned under F-NEW-450 adjudication).")
r["evidence"] = ("run/c107/pre2/c106a.stderr + run/c107/post/c106a.stderr + "
                 "run/c107/tg_post2.stderr + evidence/cont107/evidence.json")
r["closed_wave"] = "CONT-107"

# ── 2. F-NEW-448 honest refresh: the static root is REFUTED ──────────
r = find("F-NEW-448")
assert r
r["status"] = "CONFIRMED_OPEN_GAP"
r["root_cause"] = ("REFRESH (CONT-107) — the CONT-106 'theme-dimension static "
                   "never populated' root cause is REFUTED by androguard decode "
                   "(scripts/cont107_scan_m3_v2.py, run/c107/m3_scan2.txt): "
                   "Toolbar.onMeasure opens with sget-boolean Ll/m3;->a:Z whose "
                   "result register is immediately overwritten by "
                   "getLayoutDirection's move-result (a DEAD class-init trigger); "
                   "the field has ZERO writers in the entire APK (a:Z unwritten, "
                   "b:Method unwritten; <clinit> writes only c:Z = SDK_INT>=27); "
                   "the dead trigger is the ONLY static read in onMeasure. The "
                   "height-0 face therefore lives in the toolbar content/"
                   "min-height chain (children measure + theme minHeight attrs), "
                   "not in any static. Chess POST on 1e3efdb4209764a9: Toolbar "
                   "still 1080x0 (C013 row) — unchanged, as the refuted root "
                   "predicts.")
r["title"] = ("Chess (jwtc 298) appcompat Toolbar measures 1080x0: CONT-106's "
              "static Ll/m3;.a theory REFUTED by decode (dead class-init "
              "trigger sget-boolean, result register overwritten, zero writers "
              "APK-wide, only static read in onMeasure) — the real root is the "
              "toolbar content/min-height measure chain (issue #364 CONT-107 "
              "refresh).")
r["evidence"] = ("run/c107/m3_scan2.txt + run/c107/chess_post.stderr + "
                 "scripts/cont107_scan_m3_v2.py")

# ── 3. F-NEW-449 honest refresh: probe = green negative-control ──────
r = find("F-NEW-449")
assert r
r["root_cause"] = ("REFRESH (CONT-107): the c106b minimization probe "
                   "(fixtures/cont107_reflectcount — 11 mixed static/instance "
                   "fields, Unsafe theUnsafe acquisition, objectFieldOffset/"
                   "staticFieldOffset per field, two-pass order stability) is "
                   "GREEN on the engine: count=11, offsets 11/11 zero throws, "
                   "mods 3 statics/8 instances, order stable. The engine "
                   "reflection-count law is CONSISTENT at this minimization, so "
                   "the n2.r OOB involves protobuf's compiled MessageInfo "
                   "metadata vs the walk count (a source the probe does not "
                   "exercise). Remains CONFIRMED_OPEN_GAP with the probe as the "
                   "registered negative control; fixture-first continuation "
                   "needs a MessageInfo-metadata-side probe.")
r["evidence"] = "run/c107/post/c106b.stderr + fixtures/cont107_reflectcount"

# ── 4. F-NEW-450 new → ROOT-CAUSED-FIXED ─────────────────────────────
roots.append({
    "id": "F-NEW-450",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P1",
    "title": "TypedArray dimension slots carried RAW complex data through the "
             "getDimensionPixelSize/getDimensionPixelOffset/getLayoutDimension "
             "readers (no complexToDimensionPixelSize): theme/XML stages stored "
             "the raw word and the def-style stage was the ONLY converter — a "
             "cross-stage inconsistency; AOSP law is slots hold the TypedValue "
             "and the dimension READERS convert (issue #364 CONT-107).",
    "layer": "framework (TypedArray TypedValue type+data vs reader conversion)",
    "root_cause": "Probe fixtures/cont107_toolbarmeasure (c106b2, real "
        "aapt2/ECJ/D8, apk 1d510ff643cec4d2): theme attr probeBarSize=56dp — "
        "resolveAttribute ok=true, TypedValue.type=5 (DIMENSION, correct), but "
        "getDimensionPixelSize answered 14337 = 0x3801 = (56<<8)|DIP = the RAW "
        "complex word (AOSP at device density 2.625: 147px). The reader gate "
        "(getDimensionPixelSize/getDimensionPixelOffset/getLayoutDimension) "
        "answered the slot verbatim; the F-NEW-327 def-style stage converted at "
        "produce while the XML/theme stages did not.",
    "fix": "FIXED (CONT-107): producers (ContextShadow F-093/F-NEW-175 + engine "
        "F-093b site) now record the slot's TypedValue type per slot in "
        "array_type[i] (written UNCONDITIONALLY per slot — F-NEW-197 recycled-"
        "singleton staleness law) and store RAW data for all stages (the 327 "
        "produce-time px conversion moved away); the reader converts "
        "DIMENSION-typed slots at read (complex_to_dimension_pixel_size for "
        "getDimensionPixelSize/getLayoutDimension, complex_to_dimension_px "
        "truncation for getDimensionPixelOffset). Untyped (legacy) slots keep "
        "the exact old semantics. Probe POST (binary 3b5ca178710c171f): dim="
        "147 = 56dp x 2.625 density = AOSP-true; static round-trip and "
        "onMeasure chain unchanged.",
    "evidence": "run/c107/pre2/c106b2.stderr + run/c107/post/c106b2.stderr + "
                "evidence/cont107/evidence.json",
    "registered_wave": "CONT-107",
    "registered_date": "2026-10-19",
    "closed_wave": "CONT-107",
})

# ── 5. F-NEW-451 new → CONFIRMED_OPEN_GAP ────────────────────────────
roots.append({
    "id": "F-NEW-451",
    "status": "CONFIRMED_OPEN_GAP",
    "priority": "P1",
    "title": "opencalc renders a keypad-only face under AOSP-true dimension "
             "values: with F-NEW-450 the SlidingUpPanelLayout umanoPanelHeight "
             "reads 108px (41dp x 2.625, AOSP-true) instead of the historical "
             "raw word 10497, and the calculator content chain degrades "
             "(display digits + keypad labels missing; 3-color face) — the "
             "correct law exposed the next gap in the layout/draw chain "
             "(issue #364 CONT-107).",
    "layer": "framework (layout/draw chain under correct TypedArray dims)",
    "root_cause": "A/B isolation: pre-107 binary reproduces the old face "
        "f25b754c4565c38b byte-identically; the fixed binary drifts "
        "deterministically x3 to 13d2d6d836f75e7f. Zero [F447-NPE] rows "
        "(F-NEW-447 provably uninvolved). The 17 [F-NEW-327-READ] gated reads "
        "are identical between binaries — the divergence enters through the "
        "converted return value of SlidingUpPanelLayout.<init>'s "
        "getDimensionPixelSize (umanoPanelHeight 10497 -> 108px) and cascades "
        "into the inflate/draw chain (first visible divergence: "
        "MainActivity.getDrawable 0x7f08007f res/MB.xml not reached; object "
        "ids shift by one). The downstream root (which view/text law collapses "
        "under correct dims) is NOT yet decoded — recorded honestly.",
    "fix": "PENDING fixture-first next wave: minimal probe = layout with a "
        "SlidingUpPanelLayout-height-dependent content chain under a correct "
        "dim; then decode which view loses its text/drawable. The wall anchor "
        "was re-pinned to the AOSP-true-dims face 13d2d6d836f75e7f x3 with "
        "this adjudication (CONT-105 dooz F-NEW-443 precedent).",
    "evidence": "run/c107/oc_base + run/c107/oc_r1 + "
                "run/cont70/regression/opencalc_r1 + evidence/cont107/",
    "registered_wave": "CONT-107",
    "registered_date": "2026-10-19",
})

# ── 6. F-NEW-452 new → ROOT-CAUSED-FIXED ─────────────────────────────
roots.append({
    "id": "F-NEW-452",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P1",
    "title": "Resources.getConfiguration() singleton answered a Configuration "
             "whose locale field was null: AOSP Configuration.setToDefaults "
             "seeds locale = Locale.getDefault() — never null. Exposed by the "
             "F-NEW-447 caller-domain NPE parity: telegram c41.run pc=65-66 "
             "iget-object Configuration;->locale answered null -> ART-faithful "
             "NPE at Locale;.getLanguage unwound the chain ROOT-059 previously "
             "masked (issue #364 CONT-107).",
    "layer": "framework (Configuration materialization law)",
    "root_cause": "Androguard decode (scripts/cont107_scan_c41.py, "
        "run/c107/c41_scan.txt): Lorg/telegram/ui/c41;.run pc=65 `iget-object "
        "v1, v1, Landroid/content/res/Configuration;->locale` then pc=66 "
        "invoke-virtual Locale;->getLanguage — the receiver came from the "
        "engine's Resources.getConfiguration() singleton (dalvik_engine.cpp "
        "get_or_create_singleton), which seeded only densityDpi (F-NEW-431), "
        "never locale.",
    "fix": "FIXED (CONT-107): the getConfiguration law now seeds the "
        "singleton's locale field once with a default Locale object "
        "(__locale_tag__=\"en_US\", mirroring the Locale.getDefault() law's "
        "tag identity). Binary 1e3efdb4209764a9: telegram F447-NPE rows 0; "
        "telegram PNG byte-identical to the pre-107 baseline "
        "(20ac8cbbbb692e63) at the 60s profile — the masked gap is healed "
        "with zero visible drift.",
    "evidence": "run/c107/tg_post.stderr (the exposed NPE face) + "
                "run/c107/tg_post2.stderr + run/c107/c41_scan.txt",
    "registered_wave": "CONT-107",
    "registered_date": "2026-10-19",
    "closed_wave": "CONT-107",
})

ids2 = {r.get("id") for r in roots}
assert len(ids2) == len(roots), "id-unique violated post-update"
out = roots if isinstance(reg, list) else {**reg, "roots": roots}
json.dump(out, open(MAIN, "w"), ensure_ascii=False, indent=1)
shutil.copy(MAIN, MIRROR)
print(f"registry: {len(roots)} roots, mirror synced")
