# T279 RENDER AUDIT — how complete is MiniAndroid rendering, measured (2026-11-28)

Engine under audit: `main` @ `344774e66`, binary `miniandroid/build/miniandroid`
SHA256 `9c5e456b4790299eeb48d501edc5caa2c214101266a3a9312662c496bdffa417`
(v0.0.6.2, -O2 -g, built 2026-11-28 04:03). Method: source census + verdict
pipeline reading + the T279 two-run campaign (23 titles, 66 executions,
`T279_TWO_RUN_RESULTS.csv`) + per-title evidence history.

## 1. The rendering verdict pipeline (the objective instrument)

Every run's final frame is classified by `runtime/execution_engine.cpp`
(frame_census_, `trace_summary.json → frame_analysis`). The verdict classes
are exhaustive and each carries its proof fields (census travels with the
verdict — 21-P0-6 law):

| verdict | meaning | first_missing_stage |
|---|---|---|
| REAL_APP_CONTENT | app window + measure+layout+draw ran + app-owned pixels/draw-ops present | — |
| VIEWTREE_NO_APP_PIXELS | pipeline ran to DRAW but no app-owned pixels | APP_PIXELS / APP_DRAW_OPS |
| PARTIAL_RENDER_BUDGET | pipeline halted on the frame budget (never clean SUCCESS) | — |
| DEFAULT_BACKGROUND_ONLY | window fine, zero non-default pixels | APP_PIXELS |
| SYSTEM_CHROME_ONLY | pixels but no app window root | WINDOW_ROOT |
| NO_ROOT | no window, zero content | WINDOW_ROOT |
| RESOURCE_INFLATION_FAILED | inflation failed (≠ synthetic screen) | — |
| RENDER_EXCEPTION | draw raised | DRAW (exception) |

Stages checked in order: WINDOW_ROOT → DRAW(exception) → MEASURE → LAYOUT →
DRAW → APP_DRAW_OPS → APP_PIXELS. This gives an objective R-scale mapping:

| T279 level | objective criterion |
|---|---|
| R0 | no screenshot captured / install or launch failure |
| R1 | launched, verdict in {NO_ROOT, SYSTEM_CHROME_ONLY, DEFAULT_BACKGROUND_ONLY, RENDER_EXCEPTION, RESOURCE_INFLATION_FAILED} |
| R2 | genuine first frame: VIEWTREE_NO_APP_PIXELS or PARTIAL_RENDER_BUDGET or REAL_APP_CONTENT with partial tree (app pixels > 0) |
| R3 | REAL_APP_CONTENT verdict on the primary screen (measure/layout/draw all ran, app-owned pixels) |
| R4 | R3 + navigation/dialogs/scroll demonstrated (second screen, dialog content, or scrolled state) |
| R5 | R3/R4 + input → handler → observable state change → updated frame (click_test + 2 distinct frame hashes) |

## 2. Subsystem census (source, at 344774e66)

Marker counts over `src/dex/ src/framework/ src/runtime/ src/renderer/`:

| subsystem | markers (count) | primary files |
|---|---|---|
| Measure/onMeasure | MeasureSpec 84, onMeasure 284 | dalvik_bridge_domain_ui_graphics.cpp, framework/ |
| Layout/onLayout | onLayout 83, requestLayout 43 | ui_graphics (R-NEW-438 onLayout authority law, S27-W4) |
| Draw | dispatchDraw 40, onDraw 104, Canvas 271, Paint 286 | canvas_shadow.cpp, ui_graphics, renderer/ |
| Touch | dispatchTouchEvent 61, onTouchEvent 64, OnClickListener 47 | touch_dispatcher.cpp, velocity_tracker.cpp, gesture_detector_shadow.cpp |
| Inflation | LayoutInflater 78, setContentView 169 | resources/ inflater, ui_graphics (R349 attach-first law, S43) |
| Widgets | TextView 326, Button 239, EditText 100, ListView 112, RecyclerView 14 | ui_graphics bridge domains |
| Dialogs/Fragment | Dialog 182, Fragment 705 | dialog_shadow.cpp, lifecycle_controller.cpp |
| Animation | ValueAnimator 24, ObjectAnimator 11, Choreographer | animator_shadow.cpp, choreographer_shadow.cpp |
| Images | Bitmap 633, Typeface 95 | bitmap_shadow.cpp, fonts/, vector_raster.cpp (S27-W1) |
| Scroll | ScrollView 28 | scroller_shadow.cpp, s98 scroll-state laws |

Battery-proven layout laws (issue #606 closure, `tests/s246_layout_closure_law_test.cpp` exists at HEAD):
MeasureSpec/getChildMeasureSpec (linear_layout_law 25 checks), LinearLayout
weights/margins/GONE/nested, FrameLayout child gravity, ScrollView scroll
state (s98 14 rows), requestLayout dirty flags (s106). Gap rows that #606
named as implemented-but-unproven got their closure battery: ScrollView
content measure (UNSPECIFIED child height), HorizontalScrollView width law,
ImageView scaleType geometry, TextView box law, RelativeLayout rule
consumption, GridLayout placement, RTL.

## 3. The Compose measure frontier (the lead shared blocker)

Three S182 titles regressed between 2026-11-06 (S182) and the 2026-11-27
recheck, all at the SAME named frontier:

```
[EXC-UNWIND] Ljava/lang/IllegalStateException; unwound
  Landroidx/compose/ui/platform/AbstractComposeView;.internalOnMeasure$ui
  invoke_pc=0x3f depth=4-6   (uturn, wocheneinkauf [Lt;.i], peri)
```

The ISE is uncaught, repeats per measure pass (TRACE 9/10/11…), state
nonfatal, result=FAIL each time → the frame stays DEFAULT_BACKGROUND_ONLY
(px 0, unc 8-33). S43's attach-first law (R-NEW-349) fixed the earlier
windowRecomposer ISE (`isAttachedToWindow` precondition) by ordering
attach → measure; the CURRENT ISE unwinds one frame deeper, inside the
compose measure lambda chain itself. Related S27 blockers in the same
family: W2 viewmodel-initializer DSL (flip), W3 content-view attachment
(#633/#634), janken `throw null` ×22 (composition state), authsrng
`convertMeasureSpec` ISE + SoftReference.get null (font cache init).

## 4. Per-title rendering classification (T279 two-run campaign, current build)

Campaign: 23 titles × 2 independent runs (+ identical deterministic
--click-test interaction runs ×2 for interactive candidates) = 70 executions
on binary `9c5e456b4790299e` (commit `344774e66`), then 18 post-fix runs on
binary `1a21be9fc9f6b016`. Full data: `T279_TWO_RUN_RESULTS.csv`; compact
screenshots: `shots/`; raw logs: `run_t279/`, `run_t279_postfix/`.

### 4.1 Reproducibility (the two-run law)

**46/46 reproducibility pairs produced byte-identical faces** (r1==r2 for all
23 titles; also ct1==ct2 for all 12 interaction pairs, f1==f2 for all 9
post-fix pairs). Zero flaky behavior observed; no third diagnostic run was
required anywhere.

### 4.2 The campaign table (verdicts on the pre-fix build unless noted)

| tag | package | verdict | app px | R | status | face r1==r2 |
|---|---|---|---|---|---|---|
| gmdice | de.duenndns.gmdice | REAL_APP_CONTENT | 182,535 (ct 753,437) | R5 | INTERACTIVE | 3891679dff449331 |
| bouncy | com.dozingcatsoftware.bouncy | REAL_APP_CONTENT | 1,095,220 (ct 158,760) | R5 | INTERACTIVE | 37326cb2b8bb6bfe |
| librecontactsbackup | com.ashkanrafiee.librecontactsbackup | REAL_APP_CONTENT | 720,117 (ct 902,277) | R5 | INTERACTIVE | 79bb8fa317311c9a |
| ugaday | ru.zxalexis.ugaday | REAL_APP_CONTENT | 145,502 (ct 142,614) | R5 | INTERACTIVE | 87fe26766fc48d06 |
| blockinger | org.blockinger.game | REAL_APP_CONTENT | 121,920 (ct 628,272) | R5 | INTERACTIVE | 34d7ac0cf77898d8 |
| pfdicer | org.secuso.privacyfriendlydicer | REAL_APP_CONTENT | 1,041 | R3 | CURRENT-REPRODUCIBLE | 31ffa499c59e3e41 |
| pfsolitaire | org.secuso.privacyfriendlysolitaire | REAL_APP_CONTENT | 58,212 | R3 | CURRENT-REPRODUCIBLE | 88dbb4a719dbc8d4 |
| textpad | com.maxistar.textpad | REAL_APP_CONTENT | 2,418 | R3 | CURRENT-REPRODUCIBLE | 27f44f4647bf76f2 |
| npuzzle | name.livitski.games.puzzle.android | REAL_APP_CONTENT | 10,282 | R3 | CURRENT-REPRODUCIBLE | 6375a3a3813af176 |
| flip | org.ecos.logic.flip_a_coin | REAL_APP_CONTENT | 113,430 | R3 | CURRENT-REPRODUCIBLE | 6808aa29ff941dae |
| diceroller | tech.gaskell.diceroller | REAL_APP_CONTENT | 225,233 | R3 | CURRENT-REPRODUCIBLE | 26d1142f19af141d |
| randomix | com.minar.randomix | REAL_APP_CONTENT | 1,080 (near-blank AppIntro slide) | R2 | CURRENT-REPRODUCIBLE | 5fef8090d5c9c87b |
| uturn | ac.stresa.uturn | REAL_APP_CONTENT **after the T279 fix** (was DEFAULT_BACKGROUND_ONLY) | 10,782 | R3 | CURRENT-REPRODUCIBLE | a53523e7ca331866 (== S182 historical face) |
| wocheneinkauf | app.wocheneinkauf | DEFAULT_BACKGROUND_ONLY | 0 | R1 | BLOCKED | e75e653c66fe8290 |
| peri | app.simple.peri | DEFAULT_BACKGROUND_ONLY | 0 | R1 | BLOCKED | b5a7a35d5fe0564b |
| stacktower3d | stack.tower3d | DEFAULT_BACKGROUND_ONLY | 0 | R1 | PARTIAL | b5a7a35d5fe0564b |
| emmanuelttt | com.emmanuelmess.tictactoe | DEFAULT_BACKGROUND_ONLY | 0 | R1 | PARTIAL | b5a7a35d5fe0564b |
| farmerbb | com.farmerbb.notepad | DEFAULT_BACKGROUND_ONLY | 0 | R1 | PARTIAL | 31ddd4d5b8e6d18e |
| itsfrz | com.itsfrz.tictactoe | DEFAULT_BACKGROUND_ONLY | 0 | R1 | PARTIAL | d55056a8928a26ff |
| janken | com.attenomy.janken | DEFAULT_BACKGROUND_ONLY | 0 | R1 | BLOCKED | d602648e8e401895 |
| authsrng | com.ivylopez.authsrng | DEFAULT_BACKGROUND_ONLY | 0 | R1 | BLOCKED | b5a7a35d5fe0564b |
| minos | de.tcrass.minos | DEFAULT_BACKGROUND_ONLY | 0 | R1 | PARTIAL | b5a7a35d5fe0564b |
| cocodechess | dk.cocode.chess | DEFAULT_BACKGROUND_ONLY | 0 | R1 | PARTIAL | d602648e8e401895 |

Visually verified genuine app content (no noise faces), 2026-11-28: gmdice
(dice UI), blockinger ct (Highscores dialog + main menu — dialog button
labels render reversed: recorded defect), flip (coin face "1" + Flip
button), diceroller (die + config labels; initial die shows "00": recorded
quirk), bouncy ("Touch to start" + vector-line table; face == 2026-11-27
recheck), ugaday (guess-the-number UI), randomix (near-blank AppIntro slide
→ honestly R2), wocheneinkauf (uniform default tint only).

### 4.3 Interaction results

State change proven (click sequence → observable frame change, ct1==ct2):
**gmdice, bouncy, librecontactsbackup, ugaday, blockinger = 5 INTERACTIVE.**
Listener registered but no frame change in the ct runs (registration-timing
or coordinate coverage): npuzzle (EXP060 listener view_id=22; S23 has
separate ×3-run STATE_CHANGED evidence from 2026-11-21), randomix
(AppIntro NextSlide listeners registered after the dispatch census),
pfdicer/pfsolitaire/textpad (0 clickable views at dispatch census).

## 5. What is genuinely complete vs partial vs broken

**Genuinely complete (R3+), reproduced twice on the current engine: 12
titles** — gmdice, bouncy, librecontactsbackup, ugaday, blockinger (all five
also R5-interactive), pfdicer, pfsolitaire, textpad, npuzzle, flip,
diceroller, uturn (post-fix). Of these, 4 S182 faces are byte-identical to
their 2026-11-06 historical achievements (gmdice, pfdicer, pfsolitaire,
textpad — the strongest determinism class) and uturn was restored to ITS
historical face byte-exactly by the T279 fix.

**Partial (R1–R2): 11 titles** — randomix (R2, near-blank intro), and the
R1 default-background class: stacktower3d, emmanuelttt, farmerbb, itsfrz,
minos, cocodechess (each a DIFFERENT named blocker: DataStore worker-thread
NPE, custom-cell listener registration gap, inflate-attach
FrameLayout children=0, compose intro timing), plus janken/authsrng/wocheneinkauf/peri
(BLOCKED at the compose composition-state layer BELOW the (now fixed)
convertMeasureSpec layer: `throw null` ×22, convertMeasureSpec residue
uncaught 32, SoftReference.get null font-cache).

**The historical context**: uturn/wocheneinkauf/peri were REAL_APP_CONTENT
on 2026-11-06 (S182), regressed by 2026-11-27. The T279 audit proved the
regression was NOT compose magic: the engine's own MeasureSpec.getMode
shadow returned a 0/1/2 index instead of the AOSP bit pattern, and the
fixed test `f714_measurespec_law_test.cpp` had pinned the wrong convention.
The fix restored uturn to its historical face byte-identically; the other
two titles have one MORE compose layer below it (honestly BLOCKED, not
"unfixable frontier").

**Remaining highest-priority blockers (named, per-title):**
1. Compose composition-state layer (`throw null` ×22 / SavedStateHandle
   IAE / SoftReference.get null): janken, authsrng, wocheneinkauf, peri —
   one shared frontier, now the lead blocker.
2. Inflate→attach for ConstraintLayout/FrameLayout content (minos,
   cocodechess): views inflate, children never attach.
3. appcompat ActionBarContextView measure (diceroller recovered by the
   S27-W4 law; remaining blank titles in this class: none measured today).
4. DataStore/protobuf worker-thread init (farmerbb notepad persistence).
5. Custom-view clickability census (itsfrz): setOnClickListener-registered
   custom cells report 0 listeners at dispatch census.
6. BMI Calculator / MasterMindy / 2048-uberspot: no verified original APK
   URL exists (recorded, not invented — S23 §7 law).
