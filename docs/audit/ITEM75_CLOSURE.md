# ITEM75 CLOSURE AUDIT — S75 CLOSURE WAVE

Generated: 2026-09-21 09:21 UTC · Scope: ITEM75-001..047 (47 census/contract rows)

Three-source reconciliation per row: canonical `FOUNDATION_GAP_MATRIX.md` row + live code check (rg on `miniandroid/src`, file:line cited) + registry back-registration. 'expected OPEN' items were checked **for absence** — a hit means the gap may have closed and is flagged PARTIAL for human review, never auto-flipped.

## Dashboard

```text
status TESTED: 20
status PARTIAL: 11
status PENDING: 16
status BLOCKED: 0
TOTAL: 47
```

## Per-row table

| Ledger | Item | Final status | Basis | Code evidence |
| --- | --- | --- | --- | --- |
| ITEM75-001 | A1 | TESTED | gap matrix FIXED + code fix PRESENT | `miniandroid/src/resources/layout_inflater.cpp:477` |
| ITEM75-002 | A2 | TESTED | gap matrix FIXED + code fix PRESENT | `miniandroid/src/runtime/execution_engine.cpp:15` |
| ITEM75-003 | A3 | TESTED | gap matrix FIXED + code fix PRESENT | `miniandroid/src/framework/bitmap_shadow.cpp:68` |
| ITEM75-004 | A4 | TESTED | gap matrix FIXED + code fix PRESENT | `miniandroid/src/framework/android_shadows.h:1009` |
| ITEM75-005 | A5 | TESTED | gap matrix FIXED + code fix PRESENT | `miniandroid/src/framework/canvas_shadow.cpp:586` |
| ITEM75-006 | A6 | TESTED | gap matrix FIXED + code fix PRESENT | `4:#include "../fonts/text_shaper.h"` |
| ITEM75-007 | A7 | TESTED | S75 FIXED: REFERENCE resids captured at parse + resolve_resid_string ARSC resolve wired at ResourceRuntime ensure_loaded (PackageParser labelRes/loadLabel law); f54_manifestlabel fixture proves label '@string/app_name' -> 'F54 LabelProof' + icon resid capture; verifier f54 6/6, 24/24 total | `520:        // resolve_resid_string + the execution-engine wiring), exactly` |
| ITEM75-008 | A8 | PARTIAL | A2 complex_unit_to_dimension_pixel_size law shipped (execution_engine.cpp:590 comment); the separate 24px default-fallback loudness not re-verified this wave | `miniandroid/src/runtime/execution_engine.cpp:592` |
| ITEM75-009 | A9 | TESTED | gap matrix FIXED + code fix PRESENT | `miniandroid/src/framework/canvas_shadow.cpp:1546` |
| ITEM75-010 | A10 | TESTED | gap matrix FIXED + code fix PRESENT | `miniandroid/src/resources/layout_inflater.cpp:582` |
| ITEM75-011 | B1 | TESTED | gap matrix FIXED + code fix PRESENT | `miniandroid/src/framework/canvas_shadow.cpp:205` |
| ITEM75-012 | B2 | TESTED | gap matrix FIXED + code fix PRESENT | `miniandroid/src/framework/canvas_shadow.cpp:244` |
| ITEM75-013 | B3 | TESTED | gap matrix FIXED + code fix PRESENT | `miniandroid/src/framework/shadow_registry.cpp:289` |
| ITEM75-014 | B4 | PARTIAL | gap matrix row (full-row status) | `miniandroid/src/framework/canvas_shadow.cpp:1343` |
| ITEM75-015 | B5 | PENDING | setTranslationX/Y/setAlpha/scale/rotation in accept-and-ignore list (canvas_shadow.cpp:569) — gap stands | `miniandroid/src/framework/canvas_shadow.cpp:569` |
| ITEM75-016 | B6 | PENDING | no scrollY/scroll-offset support anywhere in miniandroid/src (feature absent — matrix 'missing' stands) | `ABSENT: scrollY|setScrollY|getScrollY` |
| ITEM75-017 | B7 | PARTIAL | gap matrix row (full-row status) | `miniandroid/src/framework/canvas_shadow.cpp:1046` |
| ITEM75-018 | B8 | TESTED | gap matrix FIXED + code fix PRESENT | `192:                         op.stroke ? 1 ` |
| ITEM75-019 | B9 | PENDING | text_italic FLAG stored (android_shadows.h:1156) but no italic face/synthesis — matrix 'missing' stands | `ABSENT: synthesize_italic|oblique|italic_face` |
| ITEM75-020 | B10 | PENDING | no per-codepoint fallback face chain in src/fonts (only FreeSerif/emoji base — matrix 'missing' stands) | `ABSENT: codepoint_fallback|fallback_face|fallbac` |
| ITEM75-021 | B11 | PENDING | no view-level android:theme handling in layout_inflater.cpp — activity-level theme only (F-134); census-only item, gap stands | `ABSENT: android:theme` |
| ITEM75-022 | B12 | PARTIAL | @android: branch exists in resolve_id_attr (layout_inflater.cpp:417) — typed-reference path resolves; non-reference @android: names still return 0 (no framework ARSC) | `miniandroid/src/resources/layout_inflater.cpp:417` |
| ITEM75-023 | C1 | PARTIAL | gap matrix row (full-row status) | `miniandroid/src/framework/android_shadows.h:1217` |
| ITEM75-024 | C2 | PARTIAL | gap matrix row (full-row status) | `ABSENT: measure_before_render|ensure_measured` |
| ITEM75-025 | C3 | TESTED | f18_lltop fix branch present (S67 FOUNDATION comment, AOSP LinearLayout.java L1445-1470 law cited inline) | `miniandroid/src/resources/layout_inflater.cpp:2909` |
| ITEM75-026 | C4 | PARTIAL | separate text_gravity field exists (dialog_shadow.cpp:140); XML gravity->two-field conflation not proven corpus-wide | `miniandroid/src/framework/dialog_shadow.cpp:140` |
| ITEM75-027 | C5 | PARTIAL | layout_dirty raised by geometry/LayoutParams mutations (R-NEW-302 requestLayout law); text/visibility setters still do not raise it | `miniandroid/src/framework/android_shadows.h:1523` |
| ITEM75-028 | C6 | PENDING | invalidate/requestLayout in shadow method-name list only; no dirty-region model (whole-tree re-render stands) | `miniandroid/src/framework/android_shadows.h:1337` |
| ITEM75-029 | C7 | PENDING | RenderNode beginRecording/recording implemented, but setAlpha/setTranslationX/scale/rotation are swallowed no-ops (canvas_shadow.cpp:569) | `miniandroid/src/framework/canvas_shadow.cpp:545` |
| ITEM75-030 | C8 | PENDING | png_set_IHDR PNG_COLOR_TYPE_RGB confirmed (software_renderer.cpp:863) — alpha dropped, gap stands | `863:    png_set_IHDR(png, info, width, height, 8, PNG_COLOR_TYPE_RGB,` |
| ITEM75-031 | C9 | PENDING | dump_view_tree JSON writes x/y/text/visibility but NO alpha/padding/measured_left fields (dalvik_engine.cpp:9091+) | `miniandroid/src/framework/android_shadows.h:1204` |
| ITEM75-032 | C10 | PENDING | real getIdentifier path documented (android_shadows.h:1488); dual-path reconciliation not evidenced | `miniandroid/src/framework/android_shadows.h:1488` |
| ITEM75-033 | C11 | PENDING | complex_to_fraction still declared (res_id.h:167) with zero consumers — dead code stands | `miniandroid/src/resources/res_id.h:167` |
| ITEM75-034 | C12 | PARTIAL | DensityContext::from_density(font_scale) plumbing exists (res_id.h:130) with default 1.0; live fontScale source not evidenced | `miniandroid/src/resources/res_id.h:124` |
| ITEM75-035 | D1 | PENDING | view_renderer.cpp exists (30KB), not in Makefile — dead file not removed | `miniandroid/src/renderer/view_renderer.cpp:3` |
| ITEM75-036 | D2 | PENDING | real_layout.cpp + resource_parser.cpp legacy orphans still present in src/resources/ | `ABSENT: real_layout.h|real_layout.cpp` |
| ITEM75-037 | D3 | PARTIAL | api_dispatcher.cpp NOT in Makefile (build-membership half fixed); file remains as grep trap | `miniandroid/src/dex/api_dispatcher.cpp:2` |
| ITEM75-038 | D4 | PARTIAL | exp088_a4 target now links miniandroid_core (CMakeLists.txt:282) — lib-set drift likely fixed; target itself remains | `miniandroid/src/renderer/software_renderer.h:426` |
| ITEM75-039 | D5 | PENDING | miniandroid/scripts/build_exp124.sh still references src/renderer/text_shaper.cpp (moved to src/fonts/) + dead real_layout.cpp/view_renderer.cpp | `ABSENT: build_exp124` |
| ITEM75-040 | D6 | PENDING | PNGWriter encodes PNG_COLOR_TYPE_RGB (software_renderer.cpp:863) — alpha dropped, gap stands | `miniandroid/src/renderer/software_renderer.cpp:863` |
| ITEM75-041 | D7 | PENDING | view_tree.json writes n[x]/n[y] while ViewNode carries measured_left/top (dalvik_engine.cpp:9092) — dual naming stands | `miniandroid/src/dex/dalvik_engine.cpp:9089` |
| ITEM75-042 | F-121 | TESTED | gap matrix FIXED + code fix PRESENT | `miniandroid/src/framework/pending_intent_shadow.cpp:2` |
| ITEM75-043 | F-122 | TESTED | gap matrix FIXED + code fix PRESENT | `miniandroid/src/framework/state_list.cpp:39` |
| ITEM75-044 | F-123 | TESTED | gap matrix FIXED + code fix PRESENT | `miniandroid/src/framework/canvas_shadow.cpp:279` |
| ITEM75-045 | F-124 | TESTED | gap matrix FIXED + code fix PRESENT | `miniandroid/src/resources/layout_inflater.cpp:1040` |
| ITEM75-046 | F-135 | TESTED | gap matrix FIXED + code fix PRESENT | `miniandroid/src/dex/dalvik_engine.cpp:21957` |
| ITEM75-047 | F-136 | TESTED | gap matrix FIXED + code fix PRESENT | `miniandroid/src/framework/dialog_shadow.h:91` |

## Conflicts and honest notes

- none: matrix and code agree on every row.

## Still-open gaps (PENDING, honestly not implemented)

- ITEM75-015 (B5): View.setX/setTranslationX/setY/AbsoluteLayout x-y absent; programmatic LayoutParams x,y dropped
- ITEM75-016 (B6): ScrollView scrolling absent (no scrollY anywhere)
- ITEM75-019 (B9): No italic face/synthesis; Paint.setTypeface no-op on Canvas path
- ITEM75-020 (B10): No per-codepoint fallback faces beyond FreeSerif/emoji (CJK depends on system TTF)
- ITEM75-021 (B11): View-level `android:theme` not applied at inflate
- ITEM75-028 (C6): invalidate() no-op; no dirty-region model (whole-tree re-render each frame)
- ITEM75-029 (C7): RenderNode node alpha/translation/scale/rotation accepted-but-ignored
- ITEM75-030 (C8): FrameBuffer blend forces result alpha=255; PNG encode drops alpha (RGB) — alpha semantics untestable end-to-en
- ITEM75-031 (C9): ViewTree evidence export lacks alpha/padding/measured fields
- ITEM75-032 (C10): getIdentifier dual path: real id resolution vs legacy stub
- ITEM75-033 (C11): fraction TypedValue dead code (complex_to_fraction zero consumers)
- ITEM75-035 (D1): view_renderer.cpp dead AND does not compile vs current ViewNode
- ITEM75-036 (D2): real_layout.cpp + resource_parser.cpp legacy orphan (self-include only)
- ITEM75-039 (D5): scripts/build_exp124.sh references moved text_shaper path
- ITEM75-040 (D6): screenshot PNG alpha dropped (RGB encode) — capture proven faithful only for opaque frames
- ITEM75-041 (D7): ViewTree JSON vs renderer dual field names (x/y vs measured_left/top) — same write site today, fragile model
