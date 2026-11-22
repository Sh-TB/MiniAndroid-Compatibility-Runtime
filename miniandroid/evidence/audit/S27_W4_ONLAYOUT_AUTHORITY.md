# S27-W4 — THE ONLAYOUT AUTHORITY LAW (THE R-NEW-438 LAYOUT ARM)

**Base: S27-W3 (`f70c6c29`). The W3 report named the candidate "root measure
law — root 0x0 starves the draw clip". Measurement REFINED it: the root was
already self-healed by the existing R-NEW-438 measure-side takeover from
frame 2; the ACTUAL killer is the layout arm of the same incomplete-emulation
surface — measured, with per-frame receipts.**

## 1. Root cause — the measured chain

1. **The DEX measure surface**: `[DEX-MEASURE]
   androidx.ConstraintLayout.onMeasure spec AT_MOST(1080)xAT_MOST(1920) ->
   0x0` — the real DEX override produces no captured write-back (the
   F-NEW-496 fallback correctly answers the specSize; the R-NEW-438 arm-1
   takeover then correctly hands the subtree to the native F-148 law).
   Result: the ROOT's census rect heals from frame 2 (`census 406
   1080x1920`) — w4_diag evidence.
2. **The canonical layout pass is CORRECT**: the F-148 CL law resolves and
   caches EXACT edges (`[U007-CLL] parent=406 child=569 box=(374,794 331x331)
   edges=1 cached=(l374 r705 t794 b1125)` — the bias law centering the coin
   ImageView; w4_diag3 instrumentation).
3. **THE POISON**: the R-NEW-466/R445 relayout law re-runs the REAL DEX
   `ConstraintLayout.onLayout` after every re-measure (`[R445-RELAYOUT]
   view=406 rect=(0,0 1080x1920) dispatched=YES` every frame). The real
   androidx bytecode — the SAME incomplete-emulation surface — calls
   `child.layout(0,0,0,0)` for EVERY child, EVERY frame:
   `[T58-FRAME] view=569 ImageView layout(0,0,0,0)
   caller=ConstraintLayout.onLayout pc=70` (w4_diag4). The faithful
   `View.layout/setFrame` shadow writes those 0s over the canonical frames
   (`measured_left=0, measured_width=0, laid_out=1`), and the draw walk's
   measured-path push then reads 0s → the census shows the children at
   `(0,0) 0x0` while the layout walk had just assigned `(374,794) 331x331`
   → the S27-W1-rasterized coin face is clipped out of the draw walk.
4. The measure store has the R-NEW-438/F-NEW-453 protection; the LAYOUT
   store had NONE — the poison landed between the layout pass and the draw.

## 2. The law (3 pieces, the R-NEW-438 doctrine extended to layout)

- **(A) The takeover flag** (`android_shadows.h`, `layout_inflater.cpp`):
  the R-NEW-438 measure-side takeover branch marks the node
  (`dex_measure_takeover`) — "the DEX chain for this node was judged an
  incomplete emulation THIS pass". A genuine DEX measure write-back clears
  it (the chain proved itself).
- **(B) The relayout gate** (`dalvik_engine_invoke.cpp`
  `dispatch_view_relayout`): the paired DEX onLayout re-dispatch is skipped
  for a node whose measure was takeover-judged and whose canonical native
  frame is non-degenerate — the native container law is authoritative (same
  doctrine as the measure arm). A degenerate canonical frame keeps the DEX
  onLayout (its only placement hope). Receipt:
  `[S27-W4-RELAYOUT-SKIP]`.
- **(C) The setFrame authority defense net** (`android_shadows.cpp`
  `layout/setFrame`): a DEGENERATE layout write over a NON-degenerate
  canonical frame of a visible, already-laid-out node is the poison
  signature — rejected loudly (`[S27-W4-FRAME-REJECT]`). AOSP never produces
  this shape from a healthy container (onLayout geometry descends from
  onMeasure state); GONE nodes stay exempt (a collapsing write is lawful
  there).
- **Instruments** (env-gated, render-neutral): the U007-LAYOUT dump now
  carries the CL anchor names + cached edges; `[U007-CLL]` names every CL
  layout-branch child box. These produced the receipts.

## 3. Measured (production binary, canonical flags)

- **flip ×3: rc=0 ×3, face `b492ee85799fb2cb` → `6808aa29ff941dae`
  deterministic ×3.** Census `node=569 ImageView pos=(374,794) size=(331x331)`
  — the EXACT F-148 resolved rect. **Face region 84,324 non-white pixels**
  (was 0 — the coin face painted); full frame 113,430 (was 234).
  `trace_summary` verdict `REAL_APP_CONTENT`, `first_divergence=None`.
- **Regression wall (canonical flags)**: np `31ddd4d5` / dice `0de952bf` /
  guess `87fe2676` / ttt `d55056a8` / minos `b5a7a35d` / hw `acdd9f05` /
  chess `d602648e` — **7/7 canonical hashes IDENTICAL**.
  **randomix: `31ddd4d5` → `5fef8090` — adjudicated PROGRESS, not a
  regression**: the canonical face was a BLANK frame (0 non-white pixels) —
  the real DEX `AppIntroViewPager.onLayout` was collapsing the full-screen
  pager to 0x0 every frame; the law rejected the poison
  (`[S27-W4-FRAME-REJECT] view=1065 rejected over canonical (0,0 1080x1920)`,
  `view=1160 Button rejected over (32,1762 231x126)`) and the new face
  carries the real AppIntro pager chrome (1,080 px, buttons at real
  positions). pz: unchanged (`35c4e53b` — the S27-W3 bisect-attributed
  pre-existing delta; 0 S27-W4 markers — the law is inert there).
- **Gates: law battery 53/53 PASS**, **test-core rc=0**, **test-hostile
  rc=0**, **source-parity OK (88 core sources manifest-parity)**.
- Honest verdict-law note: the trace frame-truth verdict is frame- and
  env-sensitive (the same binary answers DEFAULT_BACKGROUND_ONLY on some
  frames and REAL_APP_CONTENT on others — recorded in the S27-W3 report);
  the decisive receipts here are the PIXELS (0 → 84,324 in the face region)
  and the census rects.

## 4. Next named blockers

- **pz** `Board.placeTilesRandom` NoSuchElementException (the S27-W3
  receipt — Iterator law surface, S24-W2 family).
- **randomix** AppIntro surface content: the pager now renders; its
  drawables/labels are the next layer.
- The compose family is deliberately SPARED by the law: Gate A only skips
  the DEX onLayout for nodes whose measure was takeover-judged; compose's
  authoritative DEX placement (the R-NEW-466 demand) keeps its path.

## 5. Files

`src/framework/android_shadows.h` (the `dex_measure_takeover` ViewNode flag),
`src/framework/android_shadows.cpp` (the setFrame authority defense net),
`src/resources/layout_inflater.cpp` (the flag set at the takeover branch +
the U007-LAYOUT/CLL instruments),
`src/dex/dalvik_engine_invoke.cpp` (the relayout gate + the genuine
write-back clear).

## 6. Evidence

`evidence/s27/` — w4_diag..w4_diag4 (the forensics chain: [DEX-MEASURE],
[U007-CLL], [R445-RELAYOUT], [T58-FRAME] receipts), w4_law_r1 (the law run),
w4_flip_r1..r3 (determinism ×3), w4_rnd (the adjudicated progress face),
w4_wall.log, w3_law_battery.log (the battery harness path), w4_test_core.log,
w4_test_hostile.log, w4_parity.log, build logs w4_build_*.log,
`s27w4_matrix.tsv` (16 rows). Harness: `scripts/s27_w4_matrix.py` (+ the
committed S27-W3 wall/battery harnesses, reused unchanged).

Labels: ONLAYOUT_AUTHORITY LAW CLOSED (flip REAL_APP_CONTENT, face
deterministic ×3, coin face 84,324 px at the exact resolved rect);
REGRESSION_WALL 7/7 IDENTICAL + randomix BLANK→REAL-UI adjudicated PROGRESS;
PZ unchanged (pre-existing, bisect-attributed); NEXT: pz placeTilesRandom
Iterator, randomix AppIntro content.
