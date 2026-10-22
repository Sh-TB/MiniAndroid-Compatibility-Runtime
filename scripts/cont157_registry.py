#!/usr/bin/env python3
"""cont157_registry.py — CONT-157 registry append: F-NEW-494/495/496
ROOT-CAUSED-FIXED rows + anchor re-base notes. Both files (main + mirror),
id-unique verified after append."""
import json, shutil, sys

MAIN = 'root_registry.json'
MIRROR = 'canonical/root_cause_registry.json'

ROWS = [
    {
        "id": "F-NEW-494",
        "title": "F-NEW-494 — Landroid/text/Layout; getPaint()/getText() never-null accessor family (AOSP Layout.mPaint/mText final law) — ROOT-CAUSED-FIXED: dooz ComposeView draw chain measured Layout.getPaint() null → StaticLayout ctor passed null TextPaint → Paint.getTextBounds(null) NPE ×96/run → 0 draw ops → white face d602648e",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "layer": "framework-text",
        "evidence": {
            "decode": "Byte-exact chain (cont157_disasm2 + cont157_xref_fu0m): Compose draw → Lrw1;.<init> pc=451 Layout.getPaint() (no shadow arm → null) → pc=471 Lyl;.D(null-paint,text,0,32) → SDK>=29 arm pc=83 Lfu0;.m(paint,…) single-invoke shim → [F447-NPE] ART-faithful NPE → catch-all unwind Lto1;.d/Lel0;.Y ×96 → drawContent never records an op → framebuffer = uniform (250,250,250) background (theclassifier counted it 99.4% 'non-white' — honest recode: background-only face).",
            "fix": "dalvik_engine.cpp: getPaint() returns the layout's recorded paintOid (the ROOT-063/F-NEW-297 build law already stores it), never-null fallback materializes a TextPaint at the documented 42px default and records it back (idempotent); getText() returns the recorded text payload (AOSP mText final). Arm matches BOTH Landroid/text/Layout; (declared) and Landroid/text/StaticLayout; (runtime class of the receiver — measured: Layout-only arm never fired, zero [F-NEW-494] lines while F298-BUILD ran).",
            "run": "run/c157/dooz_fixed2.log — [F-NEW-494] ×12; C013-ONDRAW ops 0→7; face d602648e→6e1b0cfc; 'Dooz' title text pixels (0x30323a) appear on the framebuffer",
            "wall": "7/9 at first pass (dooz + telegram justified re-bases, see rows); negatives 19/19; selftest 13/13"
        }
    },
    {
        "id": "F-NEW-495",
        "title": "F-NEW-495 — Bitmap.createBitmap materialization family + static-invoke shadow routing: (a) try_shadow_dispatch now honors current_invoke_is_static_ (EXP-071 flag) — object-first STATIC calls (createBitmap(dm,…) etc.) no longer hijack ctx.class_name with args[0].class_desc → REC-MISS null; (b) BitmapShadow createBitmap (DisplayMetrics,w,h,cfg) overload disambiguated from the (colors,w,h,cfg) kind-shape by runtime class; (c) the LAWFUL androidx null-dm form ImageBitmapKt.createBitmap(null,w,h,cfg,hasAlpha,colorSpace) materializes (AOSP Bitmap.java: dm nullable, density falls back to device profile); (d) positive-dims materialization with 64MP OOM guard at the bridge gate — ROOT-CAUSED-FIXED: dooz DrawCache bitmap null → getWidth/prepareToDraw NPE chain",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "layer": "framework-graphics",
        "evidence": {
            "decode": "Lf22;.e (drawWithCache, const-string 'drawCachedImage must be invoked first…') → Lpm;.h (SDK>=26 arm) → Ld1;.c → invoke-static/range createBitmap(null,63,63,ARGB_8888,false,SRGB) — probe [S109-BITMAP] createBitmap static=1 argc=6 a0k7(NULL) a1k0=63 a2k0=63. Pre-fix chain: static call ctx.class_name hijacked to args[0].class_desc → no shadow claims → REC-MISS null → Lv6;.a null → Bitmap.getWidth(null) NPE at Lf22;.e pc=245 → layer paint unwound → after F-NEW-494 only 7-11 ops survived.",
            "fix": "dalvik_engine.cpp try_shadow_dispatch: sctx_static = current_invoke_is_static_ (the EXP-071 Phase 8 flag, already maintained by execute_invoke_static) — static calls marshal ALL args and key the shadow lookup on the DECLARED class; bitmap_shadow.cpp createBitmap: (dm,w,h,cfg) branch disambiguated by args[0].object_class, NULL-dm branch per AOSP nullable-dm law, handled_object with BitmapStore.create zero-filled (transparent black ARGB_8888); dalvik_engine.cpp bridge gate: positive-dims materialization for (w,h,cfg) + (dm|NULL,w,h,…) shapes with 64MP OOM deferred throw.",
            "run": "run/c157/dooz_fixed6.log — [F-NEW-495] ×4; C013-ONDRAW ops 7→631; run/c157/dooz_60.log — ops 1947 (draw pipeline alive); telegram exceptions 19→13 at same visible content (face re-base 20ac8cbbbb→1671f5a3)",
            "wall": "7/9 at first pass; negatives 19/19; selftest 13/13"
        }
    },
    {
        "id": "F-NEW-496",
        "title": "F-NEW-496 — View.onMeasure no-write-back AOSP default fallback (View.onMeasure = setMeasuredDimension(getDefaultSize(suggested,spec)); getDefaultSize AT_MOST/EXACTLY → specSize) — ROOT-CAUSED-FIXED: dooz ComposeView Lt4; measured 1x1 (Compose-internal setMeasuredDimensionRaw not captured) → draw replay rect collapsed to 1x1 → 631-1947 recorded ops replayed invisibly",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "layer": "framework-view",
        "evidence": {
            "decode": "[DEX-MEASURE] Lt4;.onMeasure spec_w=AT_MOST(1080) spec_h=AT_MOST(1920) -> 0x0 FAILED(no write-back); C013-CUSTOMVIEW replay rect (0,0 1x1); UC009-DRAW contract expanded but the node stayed 1x1; [F-NEW-496] fallback then fills 1080x1920 and the replay runs at full rect ('onDraw replayed 715/1947 ops for Lt4; at (0,0 1080x1920)').",
            "fix": "dalvik_engine.cpp dispatch_custom_view_measure: when the app's onMeasure executed but no captured write-back, fill out_w/out_h per the AOSP View.onMeasure default (UNSPECIFIED → suggested(0); EXACTLY/AT_MOST → specSize) and return true — the measure CONTRACT completed; bounded [F-NEW-496] diag.",
            "run": "run/c157/dooz_fixed7.log — [F-NEW-496] ×5; replay rect (0,0 1080x1920) with 715 ops; run/c157/dooz_60.log — 1947 ops",
            "honest-frontier": "dooz presentation still pending: the first full Compose frame (measure+layout+draw real DEX) exceeds the 25s/60s wall budget → F084 halt → F298-KEEP skips presentation (the draw-op-throughput wall = the F-NEW-481 cohort frontier). dooz face honestly re-based d602648e→31ddd4d5 (background-white → draw-op boundary face; ops 0→1947 recorded)."
        }
    }
]

reg = json.load(open(MAIN))
ids = {r.get('id') for r in reg}
for row in ROWS:
    if row['id'] in ids:
        print(f"SKIP duplicate {row['id']}")
        continue
    reg.append(row)
    ids.add(row['id'])
print(f"appended → total {len(reg)}")

with open(MAIN, 'w') as f:
    json.dump(reg, f, ensure_ascii=False, indent=1)
shutil.copyfile(MAIN, MIRROR)

# verify id-unique + mirror identity
import hashlib
m = json.load(open(MAIN)); c = json.load(open(MIRROR))
all_ids = [r.get('id') for r in m]
assert len(all_ids) == len(set(all_ids)), 'DUPLICATE IDS'
assert m == c, 'MIRROR MISMATCH'
h1 = hashlib.sha256(open(MAIN,'rb').read()).hexdigest()[:16]
h2 = hashlib.sha256(open(MIRROR,'rb').read()).hexdigest()[:16]
print(f"id-unique OK; main==mirror OK; sha16 {h1}=={h2}; roots={len(m)}")
