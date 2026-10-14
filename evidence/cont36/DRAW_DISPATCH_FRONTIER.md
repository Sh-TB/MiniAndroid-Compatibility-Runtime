# CONT-36 — Independent Verification of CONT-35 + the Compose Draw Root:
# F-NEW-297 (draw-dispatch identity + Layout.draw text law) ROOT_CAUSED_FIXED

Wave: CONT-36 (user directive: independent verification of the CONT-35
report, then the actual current frontier; "ادامه"). Predecessor:
evidence/cont35/TEXT_PIPELINE_FRONTIER.md. This wave: (0) verified remote
state and reproduced EVERY CONT-35 claim from the verified source, (1)
verified the friend's Fragment/Preference report line-by-line against the
actual source (claims CONFIRMED-as-gaps / FALSE / NOT-PRESENT — §9), (2)
traced the Compose draw path with op-level caller attribution and
ROOT_CAUSED the draw-subtree starvation to the re-entry identity cap, (3)
fixed it together with the Layout.draw text law, the TextPaint shadow gate
and the layout paint-identity carry — FOUR coordinated generic points, one
semantic family — (4) probe-proven ×3 in BOTH directions, (5) target:
stubs 125→1, nested-subtree ops 64→236, frame zero-drift ×3, dooz anchor
byte-stable ×3, (6) full regression ZERO DRIFT, (7) registry 605→606.

## 0. RESUMABLE STATE BLOCK

| item | value |
|---|---|
| HEAD at wave start | 1cc38daa (CONT-35 pushed; local == origin/main, 0/0 ahead-behind) |
| pre-wave binary | 6508a51d01b54280 (rebuild from HEAD BYTE-EXACT == the CONT-35 record; clean-tree SHA match) |
| post-wave binary | **054b9bd52fa695fc** (diag instrument + F-NEW-297's four points) |
| intermediates | e25bfb0409822a92 / 11776f63dd6956cb (pre-gate-alignment builds, superseded) |
| target APK | tmp/cont35_apks/composeStopwatch_1009011.apk (sha256 dbf937ebbe7c0b3d…, SHA-exact carry) |
| Track B control | tmp/cont35_apks/simplecalc_8.apk (68da25fd9fdf54b4…) |
| compose anchor | upload/canonical_apks/io.github.yamin8000.dooz_23.apk (d602648e8e401895) |
| probe | fixtures/fnew297_probe (real aapt2/ECJ/D8; wired into w4 + cont35_regression) |
| regression | run/cont36/regression (scripts/cont35_regression.sh, OUT retargeted; fnew297 row added) |

## 1. PHASE 1 — REMOTE STATE + CONT-35 CLAIM VERIFICATION (all reproduced)

- `git fetch origin`: local == origin/main at 1cc38daa (0/0). Working tree:
  only the `tmp/flappycow` submodule dirty flag (run artifact, not source).
- F-NEW-294/295/296: present in source (dalvik_engine.cpp Typeface sget
  synthesis ~:19102, bridge law ~:25243; Alignment kOrdinals rows
  :23330-23332; LineBreakConfig$Builder law :25175-25237 +
  StaticLayout$Builder.setLineBreakConfig whitelist :31863/:31948),
  registry (605 roots, three entries ROOT_CAUSED_FIXED), standing battery
  (w4_build_probes.sh), evidence (cont35/TEXT_PIPELINE_FRONTIER.md). No
  duplicated/unreachable/nested patch found; each fix is a table row or a
  platform-class-keyed law at a top-level dispatch site.
- Phase 2 reproduction (run/cont36, binary 6508a51d01b54280):
  fnew294 ×3 **77/0**, fnew295 ×3 **49/0**, fnew296 ×3 **42/0** —
  == the CONT-35 records EXACTLY; composeStopwatch ×3 frame
  **9afb2bd2606f303e** ×3 with pc409/Ljd1/Lb1 faces **0 per run**;
  SimpleCalc ×3 rc=0 **7960bce447ac6d8f**. **EVERY CONT-35 claim
  reproduced; no discrepancy found.**

## 2. THE DRAW-PATH TRACE (op-level, caller-attributed)

Instruments: MINIANDROID_CANVAS_OP_TRACE (existing per-op record),
MINIANDROID_DRAW_WINDOW_TRACE (existing S26 method-entry attribution), NEW
env-gated MINIANDROID_CANVAS_DRAW_WIN_TRACE (bounded 400; logs every Canvas
draw-primitive bridge call INSIDE the custom-view draw window with the
EXECUTING DEX caller — the same env-gated bounded pattern as LAWCEF).

Facts (composeStopwatch, binary 6508a51d01b54280, run/cont36/csw_attr):

| # | fact | evidence |
|---|---|---|
| F1 | The FIRST draw dispatch records **ops=64** (the pre-F294 baseline recorded ops=0 — the CONT-35 text laws MOVED the frontier; the recorded "ops=0" claim is now historical) | `[C013-ONDRAW] view=1069 class=Lh4; dispatched=YES ops=64`; baseline run/cont35/csw_baseline/r1 ops=0 |
| F2 | ALL draw-window canvas ops come from **Ln3** (the Compose Canvas wrapper — implements Ltf;, field a=android Canvas; decode: .d clipRect, .e translate, .h drawRoundRect, .n drawRect, .q clipPath): 131 drawRoundRect + 10 clipRect + 7 clipPath + 3 drawRect. **ZERO drawText/drawArc/drawPath** | [CDW-OP] attribution ×151 |
| F3 | The APK DEX contains **NO reachable drawText call**: only Lkd1 (a canvas wrapper whose draw* never execute), Lsh1 (a ReplacementSpan — draws only inside Layout.draw), Lm3.m (no callers). Static scan with corrected class-extraction (61,113 invoke instructions) | scripts/cont36_find_textpainter2.py, cont36_scan_sanity.py |
| F4 | The ONLY site that invokes a draw block is **Loc0.c pc=106** (`invoke-interface v14, v9, Luv;->I(Loc0;)V`): decode = `Loc0.c(Ltf;JLmo0;Luv;Lt40;)V`: save → **block.I(this)** → restore — the CanvasDrawScope dispatch; the WHOLE subtree draws inside block.I | scripts/cont36_disasm_loc0.py |
| F5 | `[M3-19-CYCLE]` stubs fired **INTERLEAVED with the draws** at depth 109-111 on `Loc0.c#976#…` keys, lifetime_calls=32/2 — the nested subtree draws were stubbed mid-dispatch | run/cont36/csw_drawwin (125 stubs/run) |
| F6 | The M3-19/F-098/S122 identity key appends receiver + **first 2 object args** only; for Loc0.c the cap fills on (canvas, transform) — both INVARIANT per frame — so the draw block never enters the key | dalvik_engine.cpp key construction |
| F7 | The text-paint chain exists in the DEX but NEVER runs: Lg6.d decodes as save→clip→translate→**Layout.draw(native)**→restore (scripts/cont36_disasm_lg6.py); Lg6/Lte1-paint/Lod1 appear **0 times** in the whole run log; the only Layout.draw call site is Lg6.d | scripts/cont36_lg6_callers_fixed.py |

**ROOT CAUSE (F-NEW-297a)**: the active-cycle stub treats the nested
subtree draws as "same computation" (same receiver/canvas/transform key)
and silently kills them — the outer subtree's shapes paint and every nested
subtree (text included) vanishes. Same failure family as F-098 (visitor
target payload) and F-NEW-286 (slot-table-internal state): an
argument-identity key cannot see upstream's structural nesting.

**ROOT CAUSE (F-NEW-297b)**: even un-stubbed, the paragraph paint funnels
into `android.text.Layout.draw(Canvas)` (AOSP AndroidParagraph.paint →
layout.paint(nativeCanvas) → Layout.draw; frameworks/base/…/Layout.java)
which had NO engine law — a silent void. Text could never reach the op
stream.

**ROOT CAUSE (F-NEW-297c/d)**: CanvasShadow::handles_class matched only
graphics/Paint — TextPaint never reached the paint-state shadow (black
text); ROOT-063's paint_size probe missed the F-NEW-226 `__text_size_px__`
storage (42px fallback metrics).

## 3. FIX — FOUR COORDINATED GENERIC POINTS (one semantic family)

1. **Re-entry identity cap 2 → 8** (dalvik_engine.cpp, the M3-19 key
   construction): object payloads beyond the old cap are still computation
   identity; keys strictly more specific; the guard only fires LESS often;
   MAX_RECURSION_DEPTH (80) remains the loud backstop. Universal — no name
   dispatch, no app branches.
2. **LAYOUT.draw(Canvas) TEXT LAW** (StaticLayout shadow block): reads the
   ROOT-063 text/lineHeight/textSize fields + the carried paintOid, records
   ONE DRAW_TEXT op per layout line at the canvas' current translate/clip
   state (first baseline 0.928em — the engine's FontMetrics model), honest
   no-op diag for text-less layouts. The build law now stores `paintOid` on
   the layout.
3. **CanvasShadow::handles_class** gains the generic `Paint;` suffix row —
   TextPaint reaches the paint-state shadow (the F-NEW-285 gate-vs-dispatch
   alignment family).
4. **ROOT-063 paint_size** probes `__text_size_px__` (F-NEW-226 storage).

Plus the env-gated draw-window op-attribution diagnostic (evidence
instrument, bounded, no behavior change).

## 4. PROBE — fixtures/fnew297_probe (real toolchain)

Reproduces the EXACT shape: a REUSED `Scope.draw(canvas, J, obj, obj,
Runnable)` dispatcher; outer block draws a roundrect and nests a second
dispatch with a DIFFERENT Runnable whose body draws text; then the POINT-2
shape: `StaticLayout.Builder.obtain("F297-LAYOUT-TEXT",…).build()` +
`layout.draw(canvas)`. Rows: OUTER-EXEC (guard), **NESTED-EXEC (THE
identity row)**, TEXT-CALLED, SL-BUILD (guard), SL-DRAW-VOID (guard; the op
itself asserted harness-side via the canvas op trace — the cont30w
discriminator pattern).

| run | binary | result |
|---|---|---|
| PRE ×3 | 6508a51d01b54280 | **SUMMARY FAIL** ×3 — `outerRan=1 nestedRan=0` in-log; NESTED-EXEC/TEXT-CALLED FAIL; op trace: 6 COLOR + 6 ROUNDRECT, **0 TEXT** |
| POST ×3 | 054b9bd52fa695fc | **SUMMARY PASS 42/0** ×3 — all six rows PASS ×7 draws; op trace carries **`F297-TEXT` ffcc3333 @(60,320)** (point 1) and **`F297-LAYOUT-TEXT` ff2244cc @0,66.8=72×0.928** (points 2-4: the app's TRUE color AND size) |

## 5. TARGET — composeStopwatch ×3 + dooz ×3 (binary 054b9bd52fa695fc)

| run | M3-19 stubs | Loc0.c stubs | first-frame ops | frame | text ops |
|---|---|---|---|---|---|
| csw_post297_r1 | 1 (was 125) | **0** | **236** (was 64) | 9afb2bd2606f303e | 0 |
| csw_post297_r2 | 1 | 0 | 236 | 9afb2bd2606f303e | 0 |
| csw_post297_r3 | 1 | 0 | 236 | 9afb2bd2606f303e | 0 |
| dooz_post297_r1..3 | — | — | 154/151/161 (was 111) | **d602648e8e401895** ×3 (anchor) | 0 |

- The starvation is DEAD (stubs 125→1; the surviving one is not Loc0.c);
  the nested subtrees paint (64→236 csw, 111→~155 dooz).
- Frame byte-stable ×3 both apps — the newly-painted ops are the app's own
  dark-on-dark shapes (composeStopwatch is a dark theme): **zero render
  drift**, honestly recorded. dooz first-frame op counts now vary
  (154/151/161) with the frame byte-stable — the exposed schedule-dependent
  subtrees draw invisible pixels only.
- **TEXT still not visible — the honest remaining frontier**: the
  paragraph-paint chain (R8-renamed DrawScope.drawText → Lte1.I/Lod1.I →
  Lg6.e/f → Lg6.d → Layout.draw) is STILL never entered; the dispatch
  lives behind another interface rename. Lte1.e0 RUNS during composition
  (the class is alive) — its paint entry never fires. Layout.draw's law is
  in place and probe-proven — the next wave decodes the paragraph-node
  draw dispatch and re-checks the layer composite (drawRenderNode's only
  live caller chain is the layer-draw lambda Lr40.I, itself a draw block).

## 6. THE DOOZ WHITE-FRAME DECODE (recorded, NOT patched — §8)

The dooz "anchor" d602648e8e401895 is **RGB(250,250,250) — the app's own
theme background, NOT content**: the boot render paints the first frame
(111 ops), the boot composition burns the ENTIRE 15 s wall-clock budget
(render_frame ms=15347), and every per-frame render's dispatchDraw halts at
pc=2 (F084) — the decor/window background repaint wins and the Compose
view contributes nothing. The engine's EXP092 "non-white" census counts
(250,250,250) as non-white — the census metric masked the wipe. This is a
harness frame-honesty gap (on ART an un-rendered frame KEEPS the previous
buffer — the P1-6 law already encodes this for render FAILURES but an
in-draw F084 halt still counts as render_ok=true). **PENDING** — a
frame-persistence law needs its own probe + anchor-movement analysis (the
dooz anchor would legitimately move to the boot-content frame).

## 7. REGRESSION GATE — ZERO DRIFT at 054b9bd52fa695fc

| gate | result |
|---|---|
| anchors ×3 ×8 apps | dooz d602648e8e401895, microtimer da73010a37dd0189, unote 4f1a9e4e8f64fae8, gmdice f3b483fe7b7cf51b, opencalc a976d2f9fb675cb3, tttdeluxe af6094295ecb50e3, flappycow 13cf47464d9787f4, g2048 59ca1526611c4622 — **24/24 BYTE-IDENTICAL MATCH** |
| probe battery | fcol 140/0, f259 49/0, f259g 84/7-known, f266 42/0, f268 96/0, fnew253 147/0, fnew286 10/0, fnew289 28/0, fnew252 56/0, fnew290 56/0, fnew291 56/0, fnew292 70/0, fnew293 56/0, fnew294 77/0, fnew295 49/0, fnew296 42/0 — **== CONT-28..35 records EXACTLY** |
| new probe | fnew297 **42/0** |
| Track B control | Simple Calculator ×3 rc=0 `7960bce447ac6d8f` — FULL SUCCESS retained |

## 8. STATUS WORDS

- **F-NEW-297: ROOT_CAUSED_FIXED / TESTED / OBSERVED** (probe PRE ×3 FAIL →
  POST ×3 PASS both directions with true color/size; target stub
  elimination + nested-subtree ops ×3; full zero-drift gate).
- composeStopwatch: **PARTIAL SUCCESS — draw-subtree starvation fixed;
  text still not visible** (the paragraph-paint dispatch is the recorded
  next divergence; frame zero-drift ×3).
- dooz white-frame (theme-background) face: **ROOT_CAUSED / PENDING**
  (§6 — harness frame-honesty law, own probe + anchor movement).
- Friend's Fragment/Preference report: **VERIFIED** (§9) — gaps CONFIRMED
  in source, patches NOT present in this lineage, one claim FALSE.
- STREAM-OPEN message spelling: **PENDING** (unchanged, no failing
  consumer).
- Registry: 605 → **606** (F-NEW-297; dedup-checked).

## 9. FRIEND-REPORT VERIFICATION (directive A-G)

| # | claim | verdict | evidence |
|---|---|---|---|
| 1 | FragmentTransaction.commit/commitAllowingStateLoss returns int without draining pending ops or dispatching lifecycle | **CONFIRMED (gap real, in source)** — `android_shadows.cpp:3376-3379` answers `handled_int(0)`; add/replace/etc. absorb with no op queue; executePendingTransactions → handled_bool(true) | read at HEAD |
| 2 | PreferenceFragment.addPreferencesFromResource passes through bridge as no-op | **CONFIRMED (gap real)** — zero handling anywhere in src/ (grep); falls to the typed-default stub; no widget tree | grep across miniandroid/src |
| 3 | Friend added pending-resource recording/inflation + Preference XML→widget mapping (Screen→ListView, Category→TextView, Switch→LinearLayout) | **NOT PRESENT in this lineage** — no such code at HEAD; the only preference-XML law is F-NEW-234's setDefaultValues defaults walk (dalvik_engine.cpp:41446+) | grep + read |
| 4 | Inflated root linked to Activity render content | **NOT PRESENT** (depends on #3) | — |
| 5 | Reported 2-node→6-node ViewTree, #FAFAFA frame, 3/3, empty preference text | **NOT REPRODUCIBLE here** — the patches do not exist on this lineage; no probe/assertions shipped with the report | — |
| 6 | F-NEW-253 accidentally nested inside an AudioAttributes branch, unreachable | **FALSE for this repo** — F-NEW-253 = the SaveableStateRegistry Parcelable-family law: TOP-LEVEL rows in view_ancestry.h framework_direct_interfaces()/framework_iface_supers() (:331-355, :411-413); reachability proven continuously by the standing battery (fnew253 147/0 every wave) | view_ancestry.h + battery |
| 7 | A persistent patch script exists | **NOT FOUND** in scripts/ (no fragment/preference re-apply script); even if it exists in the friend's workspace, its patches are not in this history | ls + grep |

Directives: (B) reuse — the F-NEW-234 defaults-walk is the existing
preference-XML machinery; any future PreferenceFragment law must build on
it, not duplicate it. (C/D/E) — a Fragment/Preference fix requires its own
deterministic probe (commit-drain + lifecycle + @string resolution +
measure/layout/draw evidence + 3 runs) per the CONT-36 directive; NOT
speculatively patched this wave (no failing consumer in the anchor/battery
set). (F) CONT-31's main-thread identity fix (F-NEW-289) intact — battery
fnew289 28/0.

## 10. NEXT RESUMABLE CHECKPOINT

1. **The paragraph-paint dispatch** (composeStopwatch/dooz text
   visibility): decode the R8-renamed DrawScope.drawText interface dispatch
   → Lte1.I/Lod1.I (the TextPainter entries; Lte1.e0 RUNS during
   composition — the class is alive, its paint entry never fires) →
   Lg6.e/f → Lg6.d → Layout.draw (the law awaits). Then re-check the
   GraphicsLayer composite (the layer-draw lambda Lr40.I is itself a draw
   block; with the identity fix it becomes reachable if the layer draw
   dispatches through Loc0.c).
2. **The frame-honesty law** (§6): in-draw F084 halt → keep-previous-frame
   (P1-6 extension), probe + dooz anchor movement analysis.
3. Standing: STREAM-OPEN message spelling (probe row first); F-NEW-288
   (Track A TextUnit spin); Simple Calculator input-pump (Track B);
   Fragment/Preference family (own probe cycle; build on F-NEW-234).
