# CONT-37 — The Paint/Present Contract:
# F-NEW-298 (getClipBounds gate + Builder prefix-conflation + FRAME-HONESTY)
# ROOT_CAUSED_FIXED — composeStopwatch presents its OWN first frame (text
# ops included); the dooz wiped-frame lie is dead

Wave: CONT-37 (user directive: "ادامه بده اصلا دستاورد دوستم چی بوده اون
میگه ماشین حساب لود میشه" — continue; report the friend's actual
achievement, he says the calculator loads; the standing checkpoint from
CONT-36 §10: the paragraph-paint dispatch). Predecessor:
evidence/cont36/DRAW_DISPATCH_FRONTIER.md. This wave: (0) verified the
environment (binary 054b9bd52fa695fc == the CONT-36 record, worktree
clean), (1) answered the friend-report question from the ALREADY-RECORDED
CONT-36 §9 verdicts (no new patching — the friend's calculator claim is
addressed with the verified numbers), (2) decoded the paragraph-paint
dispatch OP-LEVEL end-to-end (the painter IS dispatched; the body runs;
two silent gates inside it), (3) fixed THREE coordinated generic roots in
one semantic family — the getClipBounds paint gate, the Builder
setText/setTextDirection prefix-conflation, and the FRAME-HONESTY
presentation law (the P1-6 extension recorded PENDING in CONT-36 §6) —
(4) probe-proven ×3 in BOTH directions (fnew298: PRE green-wiped FAIL ×3
→ POST green-kept PASS ×3), (5) target: composeStopwatch frame
9afb2bd2606f303e → bbaf8f76308dc267 ×3 (the app's OWN first frame finally
presented, text ops included), (6) full regression: 7/8 anchors ×3
byte-identical; dooz LEGITIMATELY moved (×3) to the honest keep-empty
state; battery == CONT-28..36 records EXACTLY; simplecalc FULL SUCCESS
retained, (7) registry 606 → 607.

## 0. RESUMABLE STATE BLOCK

| item | value |
|---|---|
| HEAD at wave start | 36d5a6c5 (a tmp/-artifacts auto-commit above the CONT-36 push 99b4f468; origin/main == 99b4f468) |
| pre-wave binary | 054b9bd52fa695fc (byte-exact CONT-36 record, verified) |
| post-wave binary | **a181d7b317e015c8** (three laws + the evidence diags) |
| PRE-probe binary | ddc37884601ca802 (the wave engine changes stashed; Makefile -g0 kept) |
| build config change | miniandroid/Makefile: per-file rule — dalvik_engine.cpp built **-O2 -g0** (the TU outgrew the -g cc1plus peak on the 4 GB host; repeated OOM kills; SAME optimizer, debug sections dropped; recorded in the Makefile comment) |
| target APK | tmp/cont35_apks/composeStopwatch_1009011.apk (dbf937ebbe7c0b3d…, SHA-exact carry) |
| Track B control | tmp/cont35_apks/simplecalc_8.apk (68da25fd9fdf54b4…) |
| dooz anchor | upload/canonical_apks/io.github.yamin8000.dooz_23.apk |
| probe | fixtures/fnew298_probe (real aapt2/ECJ/D8; wired into w4_build_probes.sh + cont37_regression.sh; runner-side KEEP-CORNER pixel row) |
| regression | run/cont37/regression (scripts/cont37_regression.sh) |

## 1. THE FRIEND'S ACHIEVEMENT — ANSWERED FROM THE RECORDED VERDICTS

The question ("what did my friend actually achieve? he says the
calculator loads") is answered from the CONT-36 §9 independent
verification (evidence/cont36/DRAW_DISPATCH_FRONTIER.md §9) — no new
patching, the verdicts stand:

| friend claim | verified verdict |
|---|---|
| FragmentTransaction.commit/commitAllowingStateLoss returns int, no drain, no lifecycle dispatch | CONFIRMED as a REAL GAP in source (android_shadows.cpp:3376-3379) — but NO failing consumer in the anchor/battery set → not patched (speculative-patch discipline) |
| addPreferencesFromResource passes through as no-op | CONFIRMED as a REAL GAP (zero handling in src/) — same no-failing-consumer bound |
| friend added pending-resource inflation + Preference XML→widget mapping (Screen→ListView, Category→TextView, Switch→LinearLayout) | **NOT PRESENT in this lineage** — no such code at HEAD |
| inflated root linked to the Activity render content | **NOT PRESENT** (depends on the above) |
| 6-node ViewTree / #FAFAFA frame ×3 / empty preference text | **NOT REPRODUCIBLE** here — the patches do not exist on this lineage; no probe/assertions shipped with the report |
| F-NEW-253 nested inside an AudioAttributes branch, unreachable | **FALSE for this repo** — F-NEW-253 = top-level Parcelable-family rows (view_ancestry.h:331/411), reachability proven continuously by the standing battery (147/0 every wave) |
| a persistent patch script exists | **NOT FOUND** in scripts/ |

**The calculator claim**: the Simple Calculator app (the Track B control,
com.simplemobiletools.calculator vc8 68da25fd9fdf54b4) DOES load and
render — rc=0, frame 7960bce447ac6d8f, byte-identical ×3 through every
wave since CONT-30W — but on THIS lineage that is OUR work (the
CONT-28..36 law chain), not the friend's patches (which are not in this
history). The friend's #FAFAFA/6-node claim describes an artifact of
their own workspace that this repo cannot reproduce, and a uniform
#FAFAFA frame with EMPTY preference text would not meet the frame-truth
gate anyway (no visible app-owned text/controls). Nothing from the friend
report was adopted; the two CONFIRMED gaps remain recorded with the
reuse guidance (any future Fragment/Preference law builds on the
existing F-NEW-234 defaults-walk machinery, probe-first).

## 2. THE PARAGRAPH-PAINT DISPATCH — OP-LEVEL DECODE (Phase 1-3)

Instruments: env-gated bounded engine diags in the CONT-36 pattern —
[K0-RET] (K0's return class), [UV-DISPATCH] (the Luv;->I receiver +
attached-flag dump), [ATTACH-WATCH] (Lok0.u0/v0 receivers), [UV-F281C]
(the runtime-first gate result), [LTE1-SEL] (the candidate pool +
selection), [F280/R019] (existing), [F298-GCB] (the clip gate),
[F298-OBTAIN]/[F298-BUILD]/[F298-SETTER]/[F298-SLDRAW] (the builder/paint
payload chain), [F298-SETCOLOR] (paint color writes).

| # | fact | evidence |
|---|---|---|
| F1 | The APK's SINGLE Luv;->I dispatch site = Loc0.c pc=106; the text painters Lte1/Lod1 implement Luv; (the draw-block interface) and are created ONLY by the ModifierNodeElement factories Lqe1.d/Lld1.d through the base-class virtual Ltk0;->d() called from Lio0.b | scripts/cont37_luv_sites.py, cont37_new_scan.py, cont37_iface_dispatch.py, cont37_factory_flow.py |
| F2 | Lte1.I IS dispatched (×15 first sight; r=1, coordinator l set — the attach-gate theory DEAD) and the resolution SUCCEEDS (best=(Loc0;)V, cands=9) — the body RUNS (≥40 real executions) | run/cont37/csw_rflag, csw_f281c2, csw_lte1sel |
| F3 | The body's paint funnel: Lte1.I → (ParagraphLayoutCache fetch) → Lg6.f/e → Lg6.d → Layout.draw. Lg6.d gates on `Canvas.getClipBounds(Rect)`: unhandled → typed-default FALSE → **silent abort before Layout.draw** ([F298-GCB] clip_active=0 → the law answers true; AOSP: the initial clip is the whole surface) | scripts/cont37_disasm_lg6def.py; run/cont37/csw_gcb |
| F4 | The StaticLayout$Builder setter law's "setText" PREFIX match conflated setTextDirection(TextDirectionHeuristic) with setText(CharSequence, start, end): Compose's chain calls setTextDirection FIRST — its heuristic argument (NULL_REF constant) OVERWROTE the obtain-stored source; build() laid out an EMPTY string ([F298-BUILD] source_len=0, chars=0) while obtain had text.len=17/2/2 ([F298-OBTAIN]) | run/cont37/csw_obtain, csw_build2, csw_setter |
| F5 | FRAME WIPE: composeStopwatch frame 1 = [C013-ONDRAW] ops=265 REPLAYED (rp=265) with the TEXT ops interleaved in the op stream (58-63 etc.) and [S109-DRAWTEXT] replay rows present — then frames 2-6 halt in-window (F084) → the unconditional fb.clear(win_bg) + presentation erased frame 1: the visible frame was the (13,15,18) theme fill + the permission dialog, the cards/text GONE | run/cont37/csw_fix1, csw_s109, csw_honest (timeline grep) |
| F6 | The colors carried by the layout TextPaints are the pipeline's own setColor calls: 13148/13242/13282 ← setColor(0xff000000) — the app-visible white/gray text colors flow through the Compose DRAW BRUSH (Lbo1), whose application point in the R8 DEX is NOT yet decoded — the text REACHES the framebuffer black-on-black | run/cont37/csw_color ([F298-SETCOLOR]) |

ROOT CAUSES (three, one family): (a) the getClipBounds gate (silent
paint abort), (b) the Builder prefix-conflation (empty text payload),
(c) the presentation contract (an unfinished frame presented, wiping the
last complete one).

## 3. FIX — THREE COORDINATED GENERIC POINTS

1. **CanvasShadow getClipBounds law** (canvas_shadow.cpp): AOSP
   Canvas.getClipBounds — the CURRENT clip bounds in device coords, true
   when non-empty; the tracked clip_ state when active, else the device
   bounds (canvas_w_/canvas_h_); int fields via set_object_int_field.
   Empty clip → false (AOSP-honest).
2. **Builder setter exact-match** (dalvik_engine.cpp): the source store
   keys on the EXACT "setText" name; setTextDirection/setTextLocale store
   their own fields (textDir opaque) — never the text payload.
3. **FRAME-HONESTY law** (dalvik_engine.cpp/h + execution_engine.cpp):
   the engine sets draw_window_budget_halted_ when ANY halt unwinds
   through the draw window (the callee-halt unwind site — wall-clock,
   loop-guard, stack overflow — all mean the frame never completed); the
   compositor re-arms frame_honesty_begin() at each frame entry and
   SKIPS the fb→framebuffer_ presentation when frame_honesty_keep_prev()
   ([F298-KEEP] row). P1-6 extension: P1-6 covered render FAILURES; this
   covers in-draw halts. ART/SurfaceFlinger contract: an unfinished frame
   is never presented.

## 4. PROBE — fixtures/fnew298_probe (real toolchain)

Shape: a custom View whose FIRST onDraw paints the whole canvas GREEN
(the marker frame) and completes; whose SECOND onDraw enters a DEX busy
loop the interpreter's loop guard halts mid-draw (visited-50001 spin
guard → the draw window unwinds with 0 extra ops). In-log rows
F1-DRAWN/F2-ENTERED/SUMMARY; the PIXEL verdict is runner-side (the
cont30w_probe_pkg.sh precedent): the final screenshot's top-left 8×8
block must be 0xFF00FF00.

| run | binary | result |
|---|---|---|
| PRE ×3 | ddc37884601ca802 (wave changes stashed) | corner=(48,48,48) — the green WIPED — KEEP-CORNER FAIL ×3 (in-log guards 18/0: both frames entered; only the presentation was wrong) |
| POST ×3 | a181d7b317e015c8 | corner=(0,255,0) ×3, KEEP=5/frame, **19/0 PASS** ×3 |

## 5. TARGET — composeStopwatch ×3 + the anchor movement

| run | frame | KEEP rows | text ops |
|---|---|---|---|
| csw_target_r1..3 | **bbaf8f76308dc267** ×3 | 5/frame | 45/run (Layout.draw law ×45) |

- The frame MOVED from 9afb2bd2606f303e (the theme-fill + dialog face)
  to bbaf8f76308dc267 = **the app's OWN first frame finally presented**:
  the 265-op draw (black surface, the cards, the three StaticLayout
  texts at the app's own positions/sizes: title "Compose Stopwatch"
  (1025,80.976) size 60.375, "0." (753,974.976) size 236.25, "00"
  (753,1092.98) size 157.5).
- dooz: d602648e8e401895 → **31ddd4d5b8e6d18e** ×3 — the honest
  keep-empty state. The CONT-36 §6 decode stands: the boot composition
  needs ~15.3 s of engine time, the 15 s budget halts the draw mid-way,
  the frame never completes — the old 250-gray anchor was the DISHONEST
  presentation of that unfinished frame (and EXP092's 250-counts-as-
  non-white census masked it). The white keep-empty frame is the
  truthful one. The dooz boot-cost face is recorded PENDING (a
  composition-cost wave).

## 6. REGRESSION GATE — a181d7b317e015c8

| gate | result |
|---|---|
| anchors ×3 ×8 apps | 7/8 BYTE-IDENTICAL MATCH ×3: microtimer da73010a37dd0189, unote 4f1a9e4e8f64fae8, gmdice f3b483fe7b7cf51b, opencalc a976d2f9fb675cb3, tttdeluxe af6094295ecb50e3, flappycow 13cf47464d9787f4, g2048 59ca1526611c4622 (KEEP=0 each — the law never fires for completing apps — ZERO drift). dooz MATCH at the NEW recorded 31ddd4d5b8e6d18e ×3 (the legitimate movement, analyzed above) |
| probe battery | fcol 140/0, f259 49/0, f259g 84/7-known, f266 42/0, f268 96/0, fnew253 147/0, fnew286 10/0, fnew289 28/0, fnew252 56/0, fnew290 56/0, fnew291 56/0, fnew292 70/0, fnew293 56/0, fnew294 77/0, fnew295 49/0, fnew296 42/0, fnew297 42/0 — **== CONT-28..36 records EXACTLY** |
| new probe | fnew298 **19/0** (KEEP-CORNER PASS ×3) |
| target | composeStopwatch ×3 bbaf8f76308dc267 MATCH |
| Track B control | Simple Calculator ×3 rc=0 7960bce447ac6d8f — FULL SUCCESS retained |

## 7. STATUS WORDS

- **F-NEW-298: ROOT_CAUSED_FIXED / TESTED / OBSERVED** (probe PRE ×3
  FAIL → POST ×3 PASS both directions; target ×3; full gate with the
  analyzed anchor movement).
- composeStopwatch: **PARTIAL SUCCESS — the app's own frame (cards +
  text ops) is finally PRESENTED; the text COLOR is the next divergence**
  (black-on-black — the Compose draw-brush application point, §2 F6).
- dooz: **honest keep-empty presented; boot-budget face PENDING** (the
  composition cost is the recorded next root — NOT patched speculatively).
- STREAM-OPEN message spelling: **PENDING** (unchanged).
- Friend's Fragment/Preference report: verdicts stand (§1); gaps remain
  recorded, not patched (no failing consumer).
- Registry: 606 → **607** (F-NEW-298; dedup-checked).

## 8. NEXT RESUMABLE CHECKPOINT

1. **The Compose draw-brush color application** (composeStopwatch text
   visibility, last leg): decode where the R8'd paragraph paint applies
   the Lbo1 brush to the layout TextPaint before Layout.draw
   ([F298-SETCOLOR] shows the TextPaints carrying 0xff000000; the
   app-visible white/gray must arrive through the draw brush). Probe
   first; one semantic law expected (brush→paint color at the
   AndroidParagraph.paint equivalent).
2. **The dooz boot-budget face**: the first composition needs ~15.3 s
   engine time; the 15 s budget cannot complete it (honest keep-empty
   white). Either a composition-cost reduction wave or a budget-aware
   boot design — analyze before any patch.
3. Standing: STREAM-OPEN message spelling (probe row first); F-NEW-288
   (Track A TextUnit spin); SimpleCalc input-pump (Track B);
   Fragment/Preference family (own probe cycle; build on F-NEW-234).
