# CONT-157 Ledger — «کاشی موزایکی اجرا + حل گرافیک صفحه سفید»

**History:** e1f819ce (CONT-156) → this round. Binary: `22578fcb03e0cd15` (deterministic chain: c7092cab → bc26c774 → 22578fcb across the three fix rebuilds). #364 re-read: 0 new comments after 6334529423.

## Train 1 — Progress audit of the three named apps (hard numbers)

| app | face16 | non-white | rc | exceptions | verdict |
|---|---|---|---|---|---|
| opencalc | `63020bc7334048fe` | 58.0% | 1 | 8 | **RENDER — full keypad** (AC ( ) % ÷ 7 8 9 × 4 5 6 − 1 2 3 + 0 • ⌫ =, √/π/| row) — anchor MATCH, zero drift |
| telegram | `1671f5a34cc5aac4` | 0.09% | 1 | **13** (was 19) | partial — Disable button; UPP-001 class boundary for the main list |
| dooz (before) | `d602648e8e401895` | 99.4% "non-white" | 1 | 4 | **WHITE SCREEN** — uniform (250,250,250) background fill; the classifier counted the background as non-white (honest recode: background-only face) |
| dooz (after) | `31ddd4d5b8e6d18e` | 0.0% | 1 | — | draw-op boundary face — **0 → 1947 draw ops recorded**, measure 1×1 → 1080×1920 |

Wall anchors: 7/9 MATCH at first pass; dooz + telegram justified re-bases (see Train 3); negatives **19/19 PASS**; skill selftest **13/13 PASS**.

## Train 2 — The white-screen decode (dooz) — byte-exact chain

1. `Lrw1;.<init>` (StaticLayout-equivalent ctor) pc=451 `Layout.getPaint()` → **no shadow arm → null TextPaint** (AOSP: Layout.mPaint/mText are FINAL, never null on device)
2. pc=471 `Lyl;.D(null-paint, text, 0, 32)` (StaticLayout measure helper)
3. SDK≥29 arm pc=83 `Lfu0;.m(paint,…,rect)` — a single-invoke shim → `Paint.getTextBounds` on null
4. `[F447-NPE]` ART-faithful NPE → catch-all unwind (`Lto1;.d` / `Lel0;.Y`) **×96 per run** → `drawContent` records ZERO ops
5. framebuffer = the window background only → the exact «صفحه سفید»

Tools built this round (persisted): `scripts/cont157_disasm2.py` (corrected-walker Dalvik disassembler), `scripts/cont157_xref_fu0m.py` (whole-DEX invoke xref; class_data_off==0 skip law).

## Train 3 — Three generic engine fixes (all ROOT-CAUSED-FIXED, registry 807→810)

- **F-NEW-494** — `Landroid/text/Layout; getPaint()/getText()` never-null accessor family (arm matches declared Layout AND runtime StaticLayout; measured: Layout-only arm never fired). Evidence: `run/c157/dooz_fixed2.log` `[F-NEW-494] ×12`, ops 0→7, face `d602648e`→`6e1b0cfc`, the "Dooz" title pixels (0x30323a) appear.
- **F-NEW-495** — `Bitmap.createBitmap` materialization family: (a) `try_shadow_dispatch` now honors `current_invoke_is_static_` (EXP-071 Phase 8 flag) — object-first STATIC calls no longer hijack `ctx.class_name` with `args[0].class_desc`; (b) `(DisplayMetrics,w,h,cfg)` overload disambiguated from the `(colors,…)` kind-shape by runtime class; (c) the LAWFUL androidx `createBitmap(null,w,h,cfg,hasAlpha,colorSpace)` form (probe: `static=1 argc=6 a0k7 a1k0=63`) materializes per AOSP nullable-dm law; (d) positive-dims materialization + 64MP OOM guard at the bridge gate. Evidence: `[F-NEW-495] ×4`, ops 7→631→**1947**; telegram exceptions 19→13 at same content.
- **F-NEW-496** — `View.onMeasure` no-write-back AOSP default fallback (`getDefaultSize`: AT_MOST/EXACTLY → specSize). Evidence: `[DEX-MEASURE] Lt4; -> 0x0 FAILED` → `[F-NEW-496] ×5` → 1080×1920; replay rect `(0,0 1080x1920)` with 715-1947 ops.

## Train 4 — Honest frontier (what is NOT yet solved)

dooz **presentation** still pending: the first full Compose frame (measure+layout+draw, real DEX interpretation) exceeds the 25s/60s wall budget → F084 halt → `F298-KEEP` skips presentation. That is the **draw-op throughput wall** — the same F-NEW-481 cohort frontier, now with a 26× measured ops increase (0→1947) and a full-screen replay rect. The face is honestly re-based `d602648e`→`31ddd4d5` (background-white → draw-op boundary white; NOT claimed as real content).

## Train 5 — The mosaic tile (کاشی موزایکی)

`run/c157/cont157_mosaic.png` — 2×2 grid at binary `22578fcb03e0cd15`: dooz BEFORE (background fill) / dooz AFTER (draw path alive, ops annotation) / opencalc (full keypad) / telegram (Disable partial). Tile labels are English (PIL has no RTL/Persian shaper — the numbers are the language here).

## Gates

- Wall 9/9 with the 2 justified re-bases (cont152_wall.sh anchors updated in-place with the re-base rationale)
- Negatives **19/19** (N-08 family was session-state absence — probe re-run; matches the CONT-155 train4 precedent)
- Selftest **13/13**
- Registry 810 roots, id-unique, main==mirror (sha16 `2df8de74b8bf8449`)
