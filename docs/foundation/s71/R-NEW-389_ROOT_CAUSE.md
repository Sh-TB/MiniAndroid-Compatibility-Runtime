# R-NEW-389 ROOT CAUSE — FIRST PIXEL DIVERGENCE (S71)

Verdict: **ROOT-CAUSED → SEMANTIC (F-136 collateral, correct direction).**
The S70 hypothesis "cross-build nondeterminism / paint-path layout
sensitivity" is **DISPROVED**. Status change: OPEN/P1 → ROOT-CAUSED-SEMANTIC.

## Method (mandate control protocol, all steps executed)

| control | required | executed | result |
|---|---|---|---|
| current-source determinism | ×3 | s71_live + r389/cur_notrace + r389/cur_trace | `4f41dda2…` ×3 (byte-identical) |
| golden-source build (S69 commit b88e09d9, git worktree) | 1 | r389/gold_trace | `53177d4a…` (exact S69 golden sha) |
| golden determinism | ×3 | gold_trace + gold_run2 + gold_run3 | `53177d4a…` ×3 |
| comment-only probe | ×1 | S70 (already executed) | `53177d4a…` |
| instrumentation neutrality | both builds | traced vs untraced | shas unchanged (op trace is render-neutral) |

Instrumentation: `MINIANDROID_CANVAS_OP_TRACE=<path>` env gate added to
`canvas_shadow.cpp` (`CanvasShadow::push_op`) — one line per recorded DrawOp
(kind, geometry, resolved paint color/stroke/width/text-size/bold, clip,
record-time affine, text). Same instrumentation bytes in both builds
(copied verbatim). No second system.

## FIRST PIXEL DIVERGENCE (op level, not pixel level)

Every bouncy frame records exactly 2 ops:

```
0 COLOR 0,0 1080x1920  ff181818          (background fill)
1 TEXT  0,0           ffffff00 "…"       (ScoreView hint, yellow, bitmap font)
```

Diff of op traces (gold_trace/ops.txt vs cur_trace/ops.txt):

- golden  : `1 TEXT ... ffffff00 ""`                ← EMPTY STRING
- current : `1 TEXT ... ffffff00 "Touch to start"`  ← RESOLVED STRING

Geometry/color/clip/matrix/ all other ops: IDENTICAL. The ONLY divergence in
the entire op stream is the TEXT CONTENT of op #1.

## Causal chain (all links pinned)

1. bouncy upstream `ScoreView.java:226`:
   `return getContext().getString(R.string.touch_to_start_message);`
   (docs/upstream/apps/bouncy/java/com/dozingcatsoftware/bouncy/ScoreView.java)
2. S69 build: Context/Resources string resolution used the legacy name-map
   as PRIMARY → `touch_to_start_message` not found → `""` → drawText("")
   rasterizes 0 glyphs → top band stays background (`ff181818`).
3. F-136 build (S70 fix): ARSC-first law (AOSP Context.java:945-978 +
   Resources.java:464-592, pinned in docs/upstream/aosp/CONTEXT_STRING_LAW.md)
   → string resolves → drawText("Touch to start") → yellow `ffffff00` glyph
   pixels appear in band (3,0)-(93,4) → 81 px dark→yellow.
4. Why S70 could not see it: (a) api_calls.json records REGISTER NAMES as
   arguments (`api_trace.arguments = arg_names`, dalvik_engine.cpp:14451) —
   the empty-vs-resolved string was invisible in dispatch traces;
   (b) ViewTree texts identical because ScoreView draws via Canvas on the
   game view, not via TextViews; (c) EXP088 getString markers did not cover
   this call site.

## Impact classification

- The 81-px delta is the CORRECT rendering of a resource string that AOSP
  would also show. Direction: toward fidelity. NOT a regression.
- Bounds F-136's collateral claim precisely: 1 string draw site in bouncy's
  ScoreView HUD.
- Remaining follow-up (LOW): ScoreView hint is drawn at (0,0) with the
  legacy bitmap font path (text_size=0) — on-device it would be positioned
  per ScoreView layout; the runtime's ScoreView geometry is a separate
  cosmetic matter, recorded as-is.

Evidence files: run/s71_r389/{gold_trace,cur_trace,cur_notrace,gold_run2,
gold_run3}/ ; instrumentation diff in miniandroid/src/framework/canvas_shadow.{h,cpp}.
