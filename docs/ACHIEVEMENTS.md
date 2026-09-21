# ACHIEVEMENTS — Canonical Record of Real APK Executions

> **SINGLE SOURCE OF TRUTH.** Every real APK execution MiniAndroid has achieved,
> verified, or honestly failed is recorded HERE — one entry per application.
> Canonical by the S54 documentation law (README · ACHIEVEMENTS · ROADMAP_STATUS ·
> KNOWLEDGE_INDEX). Supersedes `docs/EXECUTION_ACHIEVEMENTS.md` (S52/S53 era),
> `SCREENSHOT_INDEX*.md`, and any per-app achievement files.
>
> Status vocabulary (canonical, unchanged): `VERIFIED / PARTIAL / BLOCKED /
> NOT_TESTED` over the four evidence states `LOCAL / REMOTE / REMOTE HISTORY /
> GITHUB ATTACHMENTS`. Nothing is upgraded without runtime evidence.

## 0. Reading this file

| Field | Meaning |
|---|---|
| App | application (corpus APK or in-repo fixture) |
| Version | APK version (versionName / vc) |
| APK SHA256 | full SHA256 of the exact artifact; `-16` = first 16 hex chars |
| Source | F-Droid / telegram.org / GitHub release / in-repo fixture |
| Runtime HEAD | commit the verdict was produced at |
| Result | SUCCESS / PARTIAL / BLOCKED / FAIL (+ honest one-line reason) |
| Ladder | L0 recognized → L1 manifest → L2 DEX → L3 lifecycle → L4 UI machinery → L5 meaningful frame → L6 real input → L7 input→state change → L8 multiple interactions → L9 app-specific behavior → L10 close/reopen persistence |
| Persistence | PERSISTENCE VERIFIED / NOT VERIFIED / PARTIAL / NOT TESTED |
| Screenshot | only real, recognizable UI; deterministic name, ≤100 KB JPG, SHA256 in `docs/evidence/s54_frames/SHA256SUMS` |
| ASC | what the ASC (Droid ASC, MG1937/ASC) reconnaissance added |
| Root cause | registry ID (R-NEW-xxx) or engine law ID (F-xxx) when known |
| Next action | the concrete next step |

Reproduce any run: `./build/miniandroid run <apk> -o <dir> [--click-test]` at the
recorded HEAD (battery gate: `bash scripts/test/run_test_battery.sh` →
"BATTERY GATE: ALL PASS (96 stages)").

**Screenshot gate law (S54 refinement, binding).** A frame is BLANK when
`(near-white ≥ 97% or near-black ≥ 97%) AND colors ≤ 8`, or when `colors ≤ 8`
(renderer artifact class). A near-black frame with `colors > 8` is
DARK-CONTENT — real dark-themed UI — and may be stored only with an
independent content check (e.g. the battery EXT-01 typography golden).
The refinement strictly narrows S53's false-reject class: every S53
rejection (chessclock 2 colors, notes 5 colors) remains a rejection; the
only rescued class is dark UI with rich palettes (helloworld_ext01, 256
colors). Blank/white/black frames are NEVER stored as images — they are
recorded as text, exactly as done in §3.2.

## 0e2. S62 Games Spotlight — first real-APK L6 (input → state → render)

| Achievement | Evidence | Class |
|---|---|---|
| **bouncy L6 PROVEN** (com.dozingcatsoftware.bouncy, source-backed F-Droid): --click-count 6 → 6/6 clicks dispatched into the app's REAL DEX XML-onClick handlers on BouncyActivity (scoreViewClicked, doPreviousTable, doQuit, hideHighScore); 7 frames recorded; render-state transition proven by frame SHA pair 4219c5116ea2 (frames 0-2) → 52e4ddacc8ac (frames 3-6) — two distinct UI states in one run. Honest: not claimed L7 (no multi-round game-loop interaction proof) | run/s62_bouncy_l6/; docs/evidence/s62_r381/bouncy_frame*.png + SHA256SUMS | EXECUTED+OBSERVED |
| Games blocked family measured: minesweeper + memory + 2048 all die at the SAME generic gate (R-NEW-331 FragmentManager.ensureExecReady ISE) with full first-engine androidx chain evidence — one fix, 3+ game consumers + Telegram | run/s62_game_mines, run/s62_probe_*; run/s62_mines_trace.log | OBSERVED |
| F-109a/c landed (register-write bitmap + strcmp arith dispatch; goldens 26/8, battery 96/96) with an HONEST marginal verdict (~9-10% rate) and the F-110 measured lever registered | docs/evidence/s62_r381/S62_REPORT.md | IMPLEMENTED+TESTED |

## 0e2. S62+ Open-Source APK Spotlight — 2 NEW source-first apps executed (breadth mission)

| Achievement | Evidence | Status |
|---|---|---|
| **anuto L5 PROVEN + input→state dispatched** (ch.logixisland.anuto, GPLv2, built FROM SOURCE aapt2/ECJ/D8, APK 8794573d…): real AnutoApplication bound (onCreate 14,751 insns), GameActivity.onCreate real chain, custom GameView constructed via G11 law, REAL GameView.onDraw dispatched (C013 dispatched=YES, app-driven 2,073,600 non-white px), --tap 540,960 → onTouch dispatched consumed=true (app's own DEX returns true) → screenToGame → TowerSelector.selectTowerAt. 3-run det 11a38a5aeeff45a6 ×3. Honest: sprites need the canvas bitmap family (recorded frontier) | docs/evidence/s62plus_spotlight/S62PLUS_REPORT.md §1a + anuto_frame0_after_onDraw.png | EXECUTED+OBSERVED (L5) |
| **OpenSudoku L5 PROVEN + input dispatched** (cz.romario.opensudoku, GPLv3, built FROM SOURCE, APK 712b4a41…): FolderListActivity real onCreate, visible text "Get more puzzles online" rendered, 2,029,440 non-white px, 0 errors; --click-count 3 → 3/3 CLICK dispatched to real FolderListActivity$1 DEX listener (handler = external http intent, honest no-op). 3-run det 11671b9c439b2e10 ×3 | docs/evidence/s62plus_spotlight/S62PLUS_REPORT.md §1b + opensudoku_frame0_folderlist.png | EXECUTED+OBSERVED (L5) |
| **F-110 lever IMPLEMENTED (a–e family)**: result-snapshot deferral (outermost-only; gprof root cause 387.6M pair<string,string> copies) → **57.8× instruction rate** A/B (128,076→7,400,000+ insns, same 25s anuto budget); thread-sleep yield law; ArrayList add(int,E)/remove(int)/remove(Object); currentThread drained-body identity; touch-target law + MotionEvent family + framework static-int table. Battery 96/96 + goldens + G06-G08 determinism ALL PASS after the changes | docs/evidence/s62plus_spotlight/S62PLUS_REPORT.md §2 | IMPLEMENTED+TESTED |
| F-111 `<view class=...>` namespace law + F-112 manifest Application buildClassName law (both ROOT-CAUSED-FIXED with first-hit evidence and cross-consumer reach) | docs/evidence/s62plus_spotlight/S62PLUS_REPORT.md §3 | ROOT-CAUSED-FIXED |

## 0e3. S63 Open-Source APK Spotlight 2 — first SOURCE-FIRST L6 (input→state→render), 2 NEW apps

| Achievement | Evidence | Status |
|---|---|---|
| **gmdice S10/L6 PROVEN source-first** (de.duenndns.gmdice, GPLv2, ge0rg/gamemasterdice @ 6353926f, APK ee9f7396…): first run rc=0 0 errors — real GameMasterDice (ListActivity) onCreate, visible "1d6/1d20/1d6+4/Push buttons to roll!", 1,744,539 non-white px; "…" click built + PAINTED the app's own selectDice AlertDialog (items=3); 5/5 CLICKs dispatched to the real handler; the app's roll chain (onClick → StandardDiceSet.roll → SecureRandom.nextInt → setText) executed in real DEX. Post-F-113: dice 6/5/3/2 (was all 1), frame SHA 5312266e→fa1d8612, pixel diff 1,584 px 100% inside the rollresult band, 3-run det fa1d8612 ×3 — **repeatable input→real handler→real state mutation→changed rendered frame from a source-first build** | docs/evidence/s63_spotlight/S63_REPORT.md §1 + gmdice_frame*.png | EXECUTED+OBSERVED (S10/L6) |
| **siggen S7** (org.billthefarmer.siggen, GPLv3, billthefarmer/sig-gen @ master, APK c83d21c6…): rc=0; plain-Activity Main onCreate; custom views Scale/Knob/Display INFLATED FROM FQCN TAGS (generic LayoutInflater path); 47,809 non-white px — byte-level match with the S61 prebuilt sweep count (source-vs-prebuilt cross-validation); 5/5 clicks dispatched, Main.onClick ran the R.id.sine case (View.getId switch + audio.waveform model mutation in real DEX). Honest: waveform = audio path (no pixel face), custom views measure 0x0 → S7 not S9; 3-run det 7e5e14a3 ×3 | docs/evidence/s63_spotlight/S63_REPORT.md §2 + siggen_frame0.png | EXECUTED+OBSERVED (S7/L5) |
| **F-113 SecureRandom IS-A Random bridge law (R-NEW-382 ROOT-CAUSED-FIXED)**: bridge_to_api dispatch receives the STATIC receiver class, so SecureRandom instances never reached the F-086 Random law → typed-zero dice; OpenJDK law (SecureRandom.java:157 extends Random, :828 next(int) override); fix = one law-family entry; battery ALL PASS (94 stages executed incl. goldens + G06-G08 + corpus) on the fixed binary. Candidate forensics: Blockinger surveyed and DEFERRED (support-v4 FragmentActivity + SurfaceView = two known heavy families) | docs/evidence/s63_spotlight/S63_REPORT.md §1 (searchlight chain) + §0 (fact matrix) | ROOT-CAUSED-FIXED |
| **zoekt large-file under-report ROOT CAUSE DIAGNOSED** (S61/S62 open question): default max_trigram_count silently excludes 1.2MB files; raised cap → complete results (F-113 lines found at 20878); csearch per-file limit reproduced 3rd time; zoekt/csearch rebuilt this session (Go 1.26.0, GOPROXY=direct) | docs/evidence/s63_spotlight/S63_REPORT.md §4 | OBSERVED (tool law) |

## 0e4. S64 Open-Source APK Spotlight 3 — breadth: 3 NEW source-first apps (S6 + S10 + S9), 4 law families

| Achievement | Evidence | Status |
|---|---|---|
| **pmk-android S6** (com.cax.pmk, GPLv3, xvadim/pmk-android @ 100eea1 v3.3.6, APK 0b3bfdc3…): МК-61 calculator emulator built FROM SOURCE; rc=0 SUCCESS 0 errors after F-114 — real MainActivity onCreate, 179 views inflated, 85 strings resolved; deterministic render c9a2a7035c75c9c8 ×3 — indicator "/ / / /" AutoScaleTextViews, "MK 61"/"ГРД" labels, E/F/K indicators (all real resources); clicks dispatched to real lambdas + xml_onClick onIndicatorTouched. Honest: interaction faces = table-measure-skin + seekbar-drag families (recorded, §6 of report) | docs/evidence/s64_spotlight/S64_REPORT.md §2 + pmk_frame0_indicator.png | EXECUTED+OBSERVED (S6) |
| **FreeKlondike S10 PROVEN source-first** (eu.veldsoft.free.klondike, GPLv3+, VelbazhdSoftwareLLC/FreeKlondike @ 789dba5 v2.0.1, APK 985afeb0…): full repeatable chain — launch → SplashActivity (WebView banner) → F-115 Timer 5000ms → real DEX SplashActivity$1.run → Class.forName(redirect) → startActivity(MenuActivity) → tap New Game (target=23) → MenuActivity.onClick → startActivity(GameActivity) → card-board render (green felt, ace slots, real drawables) → deck tap → the app's own "Deal!" response. Frames: menu 64bf2071f501b3c9 → game f3c81cfb97f59754 (2,073,600 px) → post-tap f9639e683ca736f6 (8,120 px); 3-run det ×3 | docs/evidence/s64_spotlight/S64_REPORT.md §3 + fk_*.png | EXECUTED+OBSERVED (S10) |
| **shopping-list-calc S9** (io.github.buildsbyben.shoppinglistcalc, MIT, buildsbyben/shopping-list-calc @ e1d3f74 v2.0, APK b51e6ecf…): rc=0 SUCCESS 0 errors FIRST RUN (no fixes needed); programmatic View tree (F-023 parent-link path), dark theme, totals row + blue EditText rows + tax-rate 1.00000; --click-test 7/7 real Buttons → real app lambdas (ExternalSyntheticLambda{23,16,15,24,25,9,8}), state_changed=TRUE per the app's own DEX; frame 2cd328b35622a2fa → 94e90357e4df2340 (8,348 px in tax-rate band); 3-run det ×3 | docs/evidence/s64_spotlight/S64_REPORT.md §4 + sc_*.png | EXECUTED+OBSERVED (S9) |
| **F-114 prefs law family (R-NEW-383 ROOT-CAUSED-FIXED)**: (a) SharedPreferences.getString @Nullable default returns as NULL reference (AOSP SharedPreferencesImpl.java:307-313) — was coerced to ""; (b) PreferenceManager.setDefaultValues contract (AOSP PreferenceManager.java:661-673 + :67 one-shot flag; defaults XML persisted, CheckBoxPreference→boolean else string); (c) getDefaultSharedPreferences = <pkg>_preferences (was NULL receiver). First face: pmk activateSettings NFE; second consumer: simplestopwatch (24 defaults) | docs/evidence/s64_spotlight/S64_REPORT.md §2 | ROOT-CAUSED-FIXED |
| **F-115 Timer + virtual-clock law family (R-NEW-384 part 1)**: java.util.Timer.schedule on the ONE MessageQueue (OpenJDK sched/mainLoop fixed-delay law; period re-enqueue via __timer_period__); F-115b revision: launch-frame quiescence does NOT advance the clock (GATE H/G07 goldens frozen) — timers fire under time-driven --frames capture. Faces: FreeKlondike splash-trap → S10; simplestopwatch 5.2s timer (second consumer) | docs/evidence/s64_spotlight/S64_REPORT.md §3,§6 | ROOT-CAUSED-FIXED |
| **F-116 meta-data law family (R-NEW-384 part 2)**: manifest <meta-data> capture (activity+application) → PackageManager.getActivityInfo().metaData Bundle (numeric→INT32, else STRING) + Context.getComponentName. Face: FreeKlondike splash timeout/redirect meta-data | docs/evidence/s64_spotlight/S64_REPORT.md §3 | ROOT-CAUSED-FIXED |
| **F-117 scheduled-tap law (R-NEW-384 part 3)**: when --frames drives the virtual clock, queued taps fire one per frame boundary (AOSP input timing = a touch lands at its Looper time). Face: FreeKlondike deferred-screen interaction | docs/evidence/s64_spotlight/S64_REPORT.md §3 | IMPLEMENTED+TESTED |
| **EXT-01/02 environmental**: Appliberated/HelloWorldSelfAware upstream repo DELETED (404, verified via HTML+API+tags) + local cache wiped by container reset → battery reports 92/94 until a replacement external fixture is frozen (S45 precedent for documented fixture-missing FAILs) | docs/evidence/s64_spotlight/S64_REPORT.md §0,§7 | OBSERVED (environmental) |

## 0e6. S66 Full Visual Proof + Renderer Forensics — capture chain proven, F-120 shipped, honest NO-VISUAL-PROOF where pixels are absent

| Achievement | Evidence | Status |
|---|---|---|
| **Screenshot pipeline proven independently** (§1/§10): controlled canvas_probe fixture (APK 69553417…) draws 11 analytically-exact ops via REAL onDraw DEX bytecode; T2..T9 pixel-exact (#FF0000/#0000FF/#00FF00/#808080, circle center, line); alpha 0x80FF0000 over white → #FF7E7E (1-LSB truncation documented); raw PPM SHA == PNG decoded-pixel SHA (0 byte mismatches) → capture/encoder FAITHFUL; pure-python PNG decoder == PIL byte-identical | docs/evidence/visual_forensics/canvas_probe/ + S66_REPORT.md §1 | INFRASTRUCTURE_PROVEN |
| **F-120/R-NEW-387 Button default-style gravity law shipped** (AOSP Button.java:221 buttonStyle → Widget.Material.Button gravity=center; engine never resolved the style default → Button text painted top-left). Fix: style-resolved default at node creation (create_view/get_or_create_node), CompoundButton/ImageButton excluded; XML/setGravity precedence preserved. BEFORE: TicTacToe marks at cell top-left; AFTER: glyph centers x=180/540/900 = exact column centers. Reruns: canvas probe byte-identical (no buttons), TicTacToe ×3 new deterministic frames, FishRings/OPMT boards byte-identical to S65 (only Button-label frames changed = targeted law change), battery 92/94 (EXT-01/02 environmental) — ZERO regressions | docs/evidence/visual_forensics/tictactoe/run1..3/ + S66_REPORT.md §7 | FIXED+REGRESSION-CLEAN |
| **TicTacToe full visual proof ×3 deterministic runs**: initial 613cfccc… / mid c6670948… / win 2e80e8c0… byte-identical ×3; win frame INSPECTED (X WINS status; 4X+3O; anti-diagonal win); initial-vs-win diff 4,097 px bbox (1,8)-(748,1329); real 9-click chain frame0 "X to move" → frame1 "O to move" → frame7 "X WINS" → frozen | docs/evidence/visual_forensics/tictactoe/ (initial/mid/win/final_full.png + diff.png + metrics.json per run) | VISUALLY_PROVEN (det ×3) |
| **Dooz honest downgrade — NO-VISUAL-PROOF**: v18+v23 re-fetched (SHA d81292cd…/299eab21… match corpus); fresh frames are placeholders (117/197 nonwhite px, bbox 27×36/34×105, 3 colors). Blocker traced: 7× IllegalStateException "layout state is not idle before measure starts" (compose LayoutNode measure-precondition, Log0;.b) — registered, NOT fixed (own campaign) | docs/evidence/visual_forensics/dooz/ + S66_REPORT.md §3 | RENDER_BLOCKED (honest) |
| **S65 re-validation on the F-120 engine**: FishRings frame SHAs byte-match S65 exactly (598ddbfa×4 → 96668475 → 86990d43 → bd2bad7e → e027b021×2) — S10 re-proven, blue→pink ball state change VISIBLE; TriPeaks splash/board byte-match S65 (598ddbfa…/49e02f75…), lobby F-120 SHA change cfc2302e; OPMT board b7606908 byte-match, menu F-120 SHA 3d8a4d15, app-own rc=1 stopper unchanged | docs/evidence/visual_forensics/s65_reval/ + S66_REPORT.md §10 table | RE-VALIDATED |
| **R-NEW-388 registered (TriPeaks board layout, NOT fixed today)**: visual inspection exposed all 31 card ImageViews painted at (0,0) (upstream positions via alignParent+margin idiom; engine's RL solver computes rl_cached_left but the live render reads measured_left → geometry wiring gap) + stat labels narrow-wrap (122px → 2-line → overlap). Painter proven FAITHFUL (frame == ViewTree). TriPeaks visual status honestly PARTIAL | docs/evidence/visual_forensics/S66_REPORT.md §7 + upstream/tripeaks_62f3609/activity_game.xml | REGISTERED (next campaign) |
| **Font forensics**: ASCII text pixel-proven (T7 band 792 px; "X WINS"; TriPeaks labels); Persian "دور" renders ZERO pixels (BitmapFont ASCII 32..126 law) — non-ASCII gap registered; TextView-in-ViewTree explicitly NOT accepted as font proof anywhere | S66_REPORT.md §5 | ASCII_PROVEN / Unicode_GAP_REGISTERED |

## 0e5. S65 Open-Source APK Spotlight 4 — breadth: 3 NEW source-first apps (S7 + S10 + S6), 2 law families, 1 new open family

| Achievement | Evidence | Status |
|---|---|---|
| **FishRings S10 PROVEN source-first** (eu.veldsoft.fish.rings, GPLv3, VelbazhdSoftwareLLC/FishRingsForAndroid @ dc3807e v1.23/vc6, APK 14d7dd80…): full repeatable chain — launch → SplashActivity (F-116 metaData) → F-115 Timer 5000ms → SplashActivity$1.run → Class.forName → startActivity → GameActivity <init> (F-118) + onCreate → 44-view board (pink ball + red rotation arrows + ebinqo art = the app's OWN drawables) → 3× tap → REAL handlers GameActivity$5/$6 (rings.ccwa/cwa → updateInfo) → changed frames 2,072,211 → 483,395 → 478,169 → 7,347 px. 3-run det: 598ddbfa×4 → 96668475 → 86990d43 → bd2bad7e → e027b021×2 BYTE-IDENTICAL. Post-F-119: [R358-ANEW] newInstance(I, dims=[3,12]) → [[I | docs/evidence/s65_spotlight/S65_REPORT.md §4 + fr_*.png | EXECUTED+OBSERVED (S10) |
| **TriPeaks S7 source-first** (eu.veldsoft.tri.peaks, GPLv3, VelbazhdSoftwareLLC/TriPeaksSolitaireForAndroid @ 62f3609 v1.2.1/vc4, APK 52272ae6…): splash → F-115 Timer → lobby (205,638 px, New Game/About Us/Help/Exit) → tap New Game (target=24) → GameActivity onCreate 7905 insns → board 2,073,600 px (green felt + ebinqo art + "Cards Remaining: 23" = app's own state); 52 cards bound listener_id=38 post-F-118; card tap CLICK → GameActivity$1 real handler. Honest stopper: the app's own guard IOOBE via OBJECT-IDENTITY family (recorded §7, deferred). det ×3 | docs/evidence/s65_spotlight/S65_REPORT.md §3 + tp_*.png | EXECUTED+OBSERVED (S7) |
| **OPMT S6 + chain-to-GameActivity source-first** (one.scarecrow.games.OPMT, GPLv3, 20Nick/OPMT @ 3240c4cf v0.1.2/vc1, APK 4f91e380…; androidx compile-stub + staged themes/layouts per siggen law): menu 6 views, REAL strings "Play with Friend"/"Play with Computer"/"How to play?" (214,144 px); tap → MainMenu$$ExternalSyntheticLambda2 → startActivity → GameActivity <init> 26 insns (F-118) → onCreate 1756 insns → frame diff 461,211 px. Honest stopper: app-own nextInt(0) via empty move list (OBJECT-IDENTITY family); RC=1 deterministic every run. det ×3 | docs/evidence/s65_spotlight/S65_REPORT.md §5 + opmt_*.png | EXECUTED+OBSERVED (S6) |
| **F-118 activity-constructor law (R-NEW-385 ROOT-CAUSED-FIXED)**: G08 startActivity path skipped <init> — field-initialized listeners stayed typed-zero (TriPeaks 52 dead taps; [EXP060] listener_id=0). AOSP Instrumentation.java:1448 newActivity → constructor contract. Fix in consume_pending_intent with [G08-LIFECYCLE] record; 3 consumers day one (TriPeaks, FishRings, OPMT) | docs/evidence/s65_spotlight/S65_REPORT.md §3 | ROOT-CAUSED-FIXED |
| **F-119 X.TYPE + primitive-array descriptor law (R-NEW-386 ROOT-CAUSED-FIXED)**: [SGET-MISS] Integer.TYPE → null matrix → aput-null NPE (FishRings 3 uncaught, rc=1). OpenJDK Integer.java:106 TYPE = Class.getPrimitiveClass("int") + Array.java:74/110. Laws: X.TYPE for 9 box classes → I/Z/B/C/S/J/F/D/V; Array.newInstance primitive components → "[I"-style descriptors recursively. After: [[I matrix, rc=0, S10. TicTacToe R-NEW-358 Button[][] golden PASS on the changed path | docs/evidence/s65_spotlight/S65_REPORT.md §4 | ROOT-CAUSED-FIXED |
| **OBJECT-IDENTITY family REGISTERED** (new open family): field/array-element object-ref identity churn (cardsViews[] element comparisons fail; listener field 38→273 churn evidence) blocks TriPeaks S8 + OPMT S7+; forensic trail in run logs; NEXT highest-leverage target — field-initialized listeners are an extremely common app pattern | docs/evidence/s65_spotlight/S65_REPORT.md §7 | OBSERVED (open family) |

## 0f. S61 Runtime Spotlight Corpus (Phase A) — the capability-driven sweep

> **S61 corpus law**: selection by Android-capability coverage (not
> randomness); every APK F-Droid-sourced + SHA-verified; every L-level
> recorded honestly from run artifacts (screenshots, render-walk traces,
> lifecycle traces). Canonical data: `docs/corpus/spotlight_manifest.json`
> + `docs/corpus/spotlight_results.json`; narrative:
> `docs/corpus/SPOTLIGHT_COVERAGE.md`.

| Bucket | Count | Notes |
|--------|-------|-------|
| F-Droid apps fetched (SHA-verified manifest) | **53** | api/v1-driven; idempotent pipeline `scripts/s61_spotlight_fetch.py` |
| Apps executed in the S61 sweep (budget 60s, real-dalvik) | **52** | `scripts/s61_spotlight_run.py`; per-app run dir + classified.json |
| Pre-existing corpus apps (earlier sessions) | **9** | dooz v18/v23, Notes, uNote, GM Dice, ChessClock, microtimer, simplestopwatch, headingcalculator |
| **Total corpus (Phase A)** | **61** | Phase B (100) deferred — pipeline is idempotent |
| L5 — drawing to framebuffer | **7** | diary (2,073,600 px), tuner (1,823,360), accordion (935,172), pckeyboard (208,440), shorty (44,684), siggen (47,809), schildbach.wallet (5,695) |
| L4 — real measured geometry | **3** | giggity, ghostsq.commander, jens.automation2 |
| L2 — Activity/lifecycle dispatched | **39** | modern androidx/recycler/compose-heavy apps |
| L1 — DEX/class loading, lifecycle incomplete | **3** | bouncy (libGDX/SurfaceView), two solitaire suites — honest frontier faces |
| Simple Games Spotlight subset | **8** (+3 pre-existing L7 games) | minesweeper, ludo, memory, sgtpuzzles, solitaire ×2, 2048, bouncy |

**Sweep evidence**: `run/s61_spotlight/<package>/` (screenshot.png +
SHA256, stderr trace, report.md, classified.json per app).

## 0g. S72 WAVE 4 — NEW real game (AndroidGameSnake) → MEANINGFUL SCREENSHOT + 3 P0 law families

| Achievement | Evidence | Status |
|---|---|---|
| **AndroidGameSnake S10/L6+ SCREENSHOT-PROVEN source-first** (zhangman.github.snake, Apache-2.0, zhangman523/AndroidGameSnake @ b4968c39 v1.0/vc1, APK 54cf48a9…): real-time game-loop family — launch → ConstraintLayout UI (F-148 geometry: snake_view 1080×780, biased button pad) → tap START → CLICK → reStartGame → GameMainThread (Thread subclass self-run law) → 2 ticks/frame EXACT (125ms sleep @ 250ms frame-delay, F-150 wake-time scheduler) → direction taps steer the snake cell-by-cell (BOTTOM/RIGHT/LEFT chains; app's reverse-guard honored) → food (0,0) blue + snake #FF4081 cells painted by the app's own onDraw (801 canvas ops/frame). Final frame: 122314 px non-white, luminance 248.87, entropy 0.3679, dominant #6fa8dc/#ff4081/#0000ff, snake [(7,10),(8,10),(9,10)] + food [(0,0)]; determinism ×3 BYTE-IDENTICAL (pixel sha 1a419545419deb3a, PNG sha 958031dc…) | docs/foundation/S72_WAVE4.md + docs/evidence/s72_w4_snake/ (frames + APK + SHA256SUMS) | **EXECUTED+OBSERVED (S10/L6, SCREENSHOT-PROVEN)** |
| **F-148 ConstraintLayout anchor family ROOT-CAUSED-FIXED (P0)**: layout_constraint* attrs unparsed → children 0-wide/stacked; now parsed + per-axis topological solver subset (MATCH_CONSTRAINT spread, bias 0.5, one/no-anchor laws, replay contract). Regressions: corpus 10/10 + fixtures 25/25 pixel-SAME | S72_WAVE4.md §2 | ROOT-CAUSED-FIXED |
| **F-149 Resources.getDisplayMetrics + TypedValue.applyDimension + device-density unity ROOT-CAUSED-FIXED (P0)**: three stacked silent-null/zero gaps (§038) — app dp2px computed 0px → onMeasure 0x0; now the ONE device law (2.625/420 @1080×1920) across getDisplayMetrics + applyDimension bridge + singleton | S72_WAVE4.md §2 | ROOT-CAUSED-FIXED |
| **F-150 Thread game-loop family ROOT-CAUSED-FIXED (P0)**: 4 stacked roots (sleep no-op shadow; subclass-descriptor receivers — javac emits GameMainThread.sleep; starts drained only in parks; no yield-resume) → hierarchy-aware is_thread_receiver + frame-boundary start/yield drains + wake-time registry. The while(!done){tick;sleep;} family (bouncy wall, secuso walls) becomes reachable | S72_WAVE4.md §2 | ROOT-CAUSED-FIXED |
| **Constitution-impact re-test (185 rules)**: fresh 10-APK corpus re-run on the unchanged W3 binary = 10/10 pixel-identical, dooz ×3 byte-identical (baselines reproduce, nothing rotted); dooz 197→23472 px / unote recovery / fishrings board stand as measured constitution-era deltas; F-146/F-147 re-probed UNCHANGED (still OPEN — honest) | run/s72_w4_corpus + run/s72_w4b_corpus | RE-VALIDATED |

## 0h. S73 — GitHub Execution Ledger + Historical Evidence Audit + AUTONOMOUS Snake Gameplay

| Achievement | Evidence | Status |
|---|---|---|
| **AndroidGameSnake AUTONOMOUS GAMEPLAY** (real APK, real input chain, no state injection / no renderer bypass / no screenshot fabrication): iterative closed-loop controller with pixel-only vision (#FF4081 snake / #0000ff food, 20×20 grid) + 23 scheduled real taps (x,y@frame) through the canonical TouchDispatcher DOWN/UP pipeline (F-117 scheduled-input extension; legacy form verified byte-identical to W4 evidence 1a419545419deb3a) → **88 moves, 22 accepted turns, 1 FOOD CAPTURE (frame 34: growth 3→4, snake-cell px 3042→6084, food respawn (0,0)→(9,0)), no game-over**; 3-run reproducibility **3/3 IDENTICAL** (90/90 frames, per-frame PNG sha equality) + gameplay_trace.json (C5 schema) + snake_autoplay.gif (39KB, real frames only) + B3 screenshot metrics | docs/evidence/s73_snake_autoplay/ (run_01..03, determinism_proof.json, screenshot_metrics.json, autoplay_summary.json); scripts/s73_snake_{controller,finalize,screenshot_gate}.py | **EXECUTED+OBSERVED (AUTONOMOUS, 3/3 BYTE-IDENTICAL)** |
| **C4 game-law probes via real taps (app logic authoritative)**: reverse-direction guard REJECTED (LEFT while moving R → direction stayed R); **WRAP LAW discovered** — head (19,10)→(0,10), walls wrap, no wall death; self-collision game-over OBSERVED (engineered head re-entry into occupied (5,10); panel → game-over surface 1,868,783 px); restart via START after game-over NOT observed (honest open — possible Dialog path) | run/s73_snake_c4/c4_probe_report.json + run/s73_snake_c4b/c4b_report.json | OBSERVED (app-specific laws) |
| **GitHub canonical execution ledger**: 14 [EXEC] issues (#10–#23), one per tracked application, duplicate-checked; 15 labels; dated evidence comments on #13–#23; #10/#11/#12 closed as documented completed states (HelloWorld golden, TicTacToe 9-click ×3, ConnectFour 24-step hash chain) | github.com/Sh-TB/MiniAndroid-Compatibility-Runtime issues #10–#23; scripts/s73_github_{issues,comments}.py | IMPLEMENTED (live ledger) |
| **Historical evidence audit (B1–B4)**: 10 canonical APKs + snake re-executed on the rebuilt-from-HEAD binary (rebuild fidelity proven: dooz ×3 0e334abe1b10b592 + snake W4 recipe 1a419545419deb3a byte-identical to stored records); per-app pixel faces recorded (unote 231120 / bouncy 2073600 / gmdice 182628 / microtimer 1041437 / fishrings board 2073360 frames 4–8 / opmt 213286 / tripeaks lobby 205638 / tictactoe blank-class face consistent with S51 record) | run/s73_corpus/; docs/evidence/S73/S73_REPORT.md §2 | RE-EXECUTED+OBSERVED |
| **DOOZ METRIC RECLASSIFICATION (honest)**: the "23472 px real content" surface = 23,472 PURE BLACK pixels forming a (0,0)–(489,47) rectangle, BYTE-IDENTICAL to Stopwatch's frame (an app with NO launchable Activity) → engine-default black region, NOT dooz content; dooz's own UI remains unrendered; F-146/F-147/F-145 unchanged and exact; F-141 stays CLOSED; dated correction in #14 (no history rewritten) | run/s73_corpus/{dooz_23_toplevel,com.github.muellerma.stopwatch_6}/ + issue #14 comment | RECLASSIFIED (honest) |
| **Regression**: fixtures 25/25 rc=0 with zero f141-throws; corpus re-run; dooz det ×3; snake autonomous ×3 identical; zero regressions on the rebuilt binary + F-117 extension | run/s73_fixtures/; S73_REPORT §6 | REGRESSION-CLEAN |

## 0k. S75 CLOSURE — ledger truth closure + A7 P0 fix + queued-lead probes (runtime wave: A7 only)

| Achievement | Evidence | Status |
|---|---|---|
| **A7 FIXED (the last P0 "law known, no code" census gap)**: manifest label/icon REFERENCE resids captured at parse (literal "@0x…" degrade removed) + `ManifestReader::resolve_resid_string` ARSC resolve wired at the ResourceRuntime ensure_loaded site (AOSP PackageParser labelRes/loadLabel law; resolution failure reported, never invented) | miniandroid/src/apk/manifest_reader.{h,cpp}; src/runtime/execution_engine.cpp; docs/foundation/s75/S75_REPORT.md §2 | **IMPLEMENTED+TESTED (f54 fixture)** |
| f54_manifestlabel fixture: `android:label="@string/app_name"` resolved through ARSC → "F54 LabelProof" in engine.log `[A7]` line + ViewTree; icon resid captured (decode honestly NOT claimed) | docs/evidence/foundation/fixtures/f54_manifestlabel/; upload/foundation_apks/f54_manifestlabel.apk (sha 0464ebf8…) | **PROVEN (6/6 asserts)** |
| ITEM75 ledger closure audit: all 47 UNVERIFIED census rows reconciled against gap-matrix FULL rows + live code (file:line cited) + registry; ROOT CAUSE of the blanket UNVERIFIED found (ledger builder truncated matrix rows at column 2 — status columns never seen) and fixed | docs/audit/ITEM75_CLOSURE.md + item75_closure.json; scripts/audit/item75_closure.py | 19 TESTED / 11 PARTIAL / 17 PENDING, 0 conflicts |
| Master ledger truth refresh: UNVERIFIED 59 → 4 (only source-not-recoverable rows remain); CRITICAL-001/005/006 → OBSERVED; CAM-S74OPS → OBSERVED; ledger 375 rows | docs/audit/MASTER_CHECKLIST.md; scripts/audit/build_master_audit.py (full-row fix) | RECONCILED |
| Level C fidelity on the A7 binary: committed snake 23-tap schedule replayed fresh → **90/90 frames byte-identical** (A7 render-neutral, proven) | docs/evidence/s75/snake_fidelity_probe/; scripts/s75_fidelity_probe.py | **REPRODUCED (90/90 BYTE-IDENTICAL)** |
| Regression: battery 26/26 rc=0 (25 + f54) + verifier 24/24 + graph validator PASS | docs/evidence/foundation/fixtures/VERIFICATION.json | REGRESSION-CLEAN |
| dooz F-146/F-147 re-probed at HEAD: both escapes reproduced (same sites); NEW OBSERVATION — F-147's null receiver is p0 (frame this) itself, consistent with secondary-to-F-146 (recorded, not claimed as law); black region 23,472 px bbox (0,0)–(488,47) byte-consistent | docs/evidence/s75/dooz_f146_probe/ | OBSERVED (open lead advanced) |
| gmdice roll-visibility lead reproduced with sharper detail: listener path fires (view 39 "3D20", click_kind=listener) but roll render byte-identical (0 changed px) | docs/evidence/s75/gmdice_roll/ | REPRODUCED (open) |
| snake restart-after-game-over re-probed at HEAD (S73 C4B design verbatim, schedule recovered from committed trace): game-over OBSERVED at frame 94 (exact S73 match); restart via START@99 still NOT observed — honest open re-verified | docs/evidence/s75/snake_restart_probe/; scripts/s75_snake_restart_probe.py | REPRODUCED (open re-verified) |
| R-NEW-388 re-verified at HEAD instead of unfounded implementation: f14 RL anchor laws hold exactly (x=780 / (340,760) / y=300); TriPeaks still splash-blocked (app-specific) | docs/foundation/s75/R-NEW-388_HEAD_REVERIFY.md; docs/evidence/s75/rnew388_{f14,tripeaks}/ | CONFIRMED (no code change warranted) |

## 0j. S74 FOLLOW-UP — operational base completion (evidence wave; runtime untouched)

| Achievement | Evidence | Status |
|---|---|---|
| All 14 canonical apps executed at HEAD `3505591b` with per-app sandbox data roots; 10 real-APK runs + 2 golden-fixture validator runs + 2 reused committed proofs (snake per §8, helloworld golden) | docs/evidence/s74_ops/*/session.json | **EXECUTED (14/14 dossiers audited)** |
| Human-visible representative evidence per app, each frame individually opened and reviewed by the executing agent before status assignment | docs/evidence/s74_ops/<app>/0*.png | **11 HUMAN_VISIBLE / 3 truthful NOT_HUMAN_VISIBLE** |
| Unote real SQLite persistence: notes.db created on launch, survives close/reopen in same data root (sha 2bccf9475fe3810d unchanged) | docs/evidence/s74_ops/unote/ | **OBSERVED (first corpus persistence proof)** |
| MicroTimer real input->state->render at HEAD: keypad clicks populate display (00:09:87) | docs/evidence/s74_ops/microtimer/05_frame_006.png | **OBSERVED at HEAD** |
| TriPeaks lobby newly proven at HEAD (splash->lobby at frame 7; 205,061 px) | docs/evidence/s74_ops/tripeaks/02_lobby.png | **NEW current-HEAD evidence** |
| Telegram v12.10.3 (official URL, sha-pinned) re-executed at HEAD: engine-default visual, init NPE family recorded truthfully; historical EXP071 SmsView path preserved | docs/evidence/s74_ops/telegram/session.json | **HONEST BLOCKER EVIDENCE** |
| Validator extended with §35 operational gates (visual-evidence claims, session/SHA presence, evidence links, persistence/security truthfulness, utilization consistency) — immediately caught 3 real inconsistencies (connectfour bundle path x2, tictactoe blocker field) which were then fixed | tools/validate_compatibility_graph.py | **PASS (extended)** |

## 0i. S74 — Compatibility Platform (architecture wave; runtime untouched)

| Achievement | Evidence | Status |
|---|---|---|
| **Level C fidelity probe (real APK, byte-identity)**: the exact S73 autonomous schedule (23 scheduled real taps) replayed fresh on the current binary → **90/90 frames byte-identical vs the committed `run_01` evidence** — the binary+evidence pair at S74 HEAD reproduces proven results with zero runtime drift (S74 made NO runtime code changes; architecture-only wave) | run/s74_fidelity_probe/; scripts/s74_fidelity_probe.py | **REPRODUCED (90/90 BYTE-IDENTICAL)** |
| **Level A fixtures on the current binary**: 25/25 rc=0, f141-throws=0 (exact S73 record match) | run/s73_fixtures/ (S74 re-run) | REGRESSION-CLEAN |

## 1. Master matrix — current-HEAD verdicts

Verdicts at HEAD `8c575f71` + F-080/F-081 (S54) unless marked **[S53]**
(HEAD ef569eda+). All 25 corpus rows re-audited at S54; five interactive
apps re-RUN with fresh screenshot pairs (9/9 JPGs byte-identical to the
S53 gallery before the F-080/F-081 engine fixes — deterministic replay
across HEADs proven; gmdice/chessclock re-captured after the fixes as the
fixes legitimately change their frames).

| # | App | Version | APK SHA256-16 | Source | Result | Ladder | Persistence |
|---|-----|---------|---------------|--------|--------|--------|-------------|
| 1 | Chess Clock | 2.11.2 (vc29) | `5ca6f2c54c05efe7` | F-Droid | **SUCCESS — L7** **[S54 UPGRADE]**: real clock face restored by F-080+F-081; P1/P2 panels, active-player accent; click → active-player switch (80,289 px) | L4 → **L7** | PARTIAL (prefs round-trip [S52]) |
| 2 | uNote | 30 | `be91103f0e7db443` | F-Droid | **SUCCESS [S56 UPGRADE]**: main-menu input chain PROVEN — R-NEW-368 premise REFUTED (old probe grid never covered the bottom-44px button band y=1876..1920); canonical tap (270,1898) → DOWN consumed (target=13 Add note) → UP click → app's own addNote → startActivity **NoteEdition** launched | L5; **L6 input→navigation PROVEN** (persistence ladder next) | PARTIAL (notes.db round-trip; editor input pending) |
| 3 | Bouncy (ball) | 39 | (registry) | F-Droid | **SUCCESS** (S51 era; APK not re-fetched at S53 — corpus SHA mismatch) | L5 (frame `4219c511…`) | NOT TESTED |
| 4 | Heading Calculator | 1 | `274ec873098eea51` | F-Droid | **SUCCESS — L7**: full keypad UI; digit click → display text changes | L5→**L7** | NOT TESTED |
| 5 | Notes (billthefarmer) | 139 | `82cf8bc44c163748` | F-Droid | **SUCCESS — L7 [S55 UPGRADE]**: F-082 restores the ViewSwitcher read↔edit state machine — FAB click → face swap (2,057,718 px, 99.23%); note CONTENT stays blank-class (read face = MarkdownView **extends WebView** — R-NEW-377 next dep) | L4 → **L7** (content face blocked) | NOT TESTED |
| 6 | MicroTimer | 8 | `79c6f730f64886e7` | F-Droid | **SUCCESS — L7**: keypad UI; click → `00:00:00` timer display appears | L5→**L7** | NOT TESTED |
| 7 | Simple Stopwatch | 26 | `b3ec1a5ec24ce53b` | F-Droid | **SUCCESS — L7**: Start/Delay → **Stop/Lap** running-state transition | L5→**L7** | NOT TESTED |
| 8 | GM Dice | 8 | `1621eda11b5dbc0c` | F-Droid | **SUCCESS — L7/L9-quality**: 8/8 clicks state-changed; dialog roll rendered (1.85 M px); post-F-081 base additionally renders the result label | L5→**L7 + app-specific semantic result** | NOT TESTED |
| 9 | Simple Keyboard | 145 | `d83060833dc2bc97` | F-Droid | SUCCESS (entry screen — IME, no launch UI) | L5 (entry class `eb16ab5c…`) | NOT TESTED |
| 10 | RTTT (kirkezz) | 1.3 (vc3) | `704fa51869ad7ff4` | F-Droid | SUCCESS (entry screen; Compose frontier) | L5 (entry class) | NOT TESTED |
| 11 | Dooz v18 | 18 | `d81292cd346dcb23` | F-Droid | **PARTIAL [S55]** — R-NEW-361 **ROOT-CAUSED + FIXED (F-083)**: ScatterMap ghost-metadata probe spin eliminated (HALT-LOOP gone; MainActivity.onStart/onResume dispatched for the first time); new frontier **R-NEW-376** pinned (post-F-083 ctor-climb exceeds the 2048-frame budget) | L3 → L4-in-progress (composition runs, first frame not yet reached) | NOT TESTED |
| 12 | Dooz v23 | 23 | `299eab21ac8b3c61` | F-Droid | **PARTIAL [S60]** — R-NEW-380 **ROOT-CAUSED + FIXED (F-106 reflection-surface law family: getDeclaredConstructor full upstream contract + getModifiers/Modifier bit laws + Class.toString token law; unmodifiableMap view law; Long.toString(J,I) radix law)**: the create chain resolves through the app's OWN Hilt factory (Lk2; case-1 SavedStateHandle machinery; Lqs;/Lxd0; attach OK) and the GameViewModel constructs with its real SettingsRepository dependency — ZERO exceptions in the post-fix run (was the throwing-factory RuntimeException at depth 81); the run reaches the healthy frame loop (MainActivity.onStart/onResume dispatched; Choreographer machinery alive). Successor frontier **R-NEW-381** (first frame dark — the Compose draw path; same face as the S59 post2 evidence). Prior: R-NEW-379 FIXED (F-105), R-NEW-376 FIXED (F-102), R-NEW-344 FIXED (F-086). Battery ALL PASS 96; semantic 32/32 | L5 → L5+ (creation chain closed; draw path open) | NOT TESTED |
| 12 | Dooz v23 | 23 | `299eab21ac8b3c61` | F-Droid | **PARTIAL [S59]** — R-NEW-379 **ROOT-CAUSED + FIXED (F-105: ComponentActivity view-tree owner contract + declaration/heap reference reconciliation + CLASS_REF token instance-of)**: the lifecycle-owner walk now HITS the owner (installed on the activity-as-view node; the app dialog machinery propagates it onto the decor in its own DEX), ISE ×4 → 0; the Lwl0;.containsKey Class-key guard passes (F-105c); execution advanced depth 8 → 81; next frontier **R-NEW-380** (ViewModelProvider create chain — the throwing factory fallback, empty class-name render) pinned. Prior: R-NEW-376 FIXED (F-102), R-NEW-378 FIXED (F-103). Deterministic (S58 record sha16 ef47a2d3cdc6929e ×3; the S59 state advances deeper, honest new face) | L4 → L5- (past ViewTreeLifecycleOwner; dies inside ViewModelProvider create) | NOT TESTED |
| 13 | TicTacToe (emmanuelmess) | 3 | `760fe5acf7b39435` | F-Droid | PARTIAL — blank first frame | L4 (blank class) | NOT TESTED |
| 14 | Telegram v12 | 12.10.1 (vc70389) | `f5e1192725772960` | telegram.org | **PARTIAL** — 540 s inside real init, no frame yet | L3-attempt (init depth) | NOT TESTED |
| 15 | WhatsApp | — | **NO APK** (0-byte placeholder) | — | **BLOCKED — APK unavailable** | — | — |
| 16 | Stopwatch (muellerma) | 6 | `3b6a10c8dc8ddc72` | F-Droid | PARTIAL — manifest has NO launchable Activity (QuickSettings Tile app) | L2 (by design) | — |
| 17 | BGClock | 2 | `72c140b0083ef273` | F-Droid | PARTIAL — WebView root (clock face is HTML/JS) | L4-minus (frame `2f85dd74…`) | NOT TESTED |
| 18 | TicTacToe (itsfrz) | 1.0.5 (vc5) | `2a057a9a519acd81` | F-Droid | PARTIAL — NPE at app boundary | L3 | NOT TESTED |
| 19 | Privacy Friendly Dicer | 2.0.0 (vc101) | `f2b4d3f021c3a620` | F-Droid | PARTIAL — ISE at app boundary | L3 | NOT TESTED |
| 20 | OpenLauncher | 39 | `b3320463a7a1ed46` | F-Droid | PARTIAL — heavy launcher, default screen | L5 (entry class) | NOT TESTED |
| 21 | Simple Flashlight | 66 | (corpus) | F-Droid | PARTIAL — app-boundary, default screen | L5 (entry class) | NOT TESTED |
| 22 | Antimine | 17.6.3 F | `e7b635b6629bc5b0` | F-Droid | PARTIAL — killed at 300 s; reaches MainActivity.onCreate | L3-attempt | NOT TESTED |
| 23 | Secuso Memory / Sudoku | 8 / 19 | (corpus) | F-Droid | PARTIAL — >300 s each, killed | L3-attempt | NOT TESTED |
| 24 | Secuso 2048 / Lexica | 1.4.2 / 3.13.1 | `02c799d3d582669d` / `255d26352ab1247c` | F-Droid | NOT re-run — historical EXEC BUDGET TIMEOUT (540 s heavy) | L3-attempt | NOT TESTED |
| 25 | s36/s37 game corpus (solitaire, braincup, minesweepers ×3, word game, puzzle, dice overflow, roll, game2048, yahtzee dicer, droidify) | various | (corpus) | F-Droid | NOT re-run this session — era records stand | era records | NOT TESTED |
| 26 | Tiny Music Player | 1.0 | `d7bcb24d101b04be` | F-Droid | era record (campaign014) | era record | NOT TESTED |
| 27 | TicTacToe Classic (palahsu) | ? | `752852c94c980788…` | legacy cache | **BLOCKED — APK unavailable** (cache lost; F-Droid `com.palahsu.ttt` NOT_FOUND at S54); historical S37 full-render + S44 playable record stands at its recorded HEADs | era: L9 | — |

**Count summary (S57, HEAD 28b644b7+F-086):** SUCCESS with real recognizable
GUI **6** (Chess Clock, GM Dice, MicroTimer, Simple Stopwatch, Heading
Calculator, uNote) + **Notes upgraded to L7 mode-switch** (content face still
blank-class — WebView end-to-end probe pinned) — **6 with proven input→state-change
screenshot pairs** (GM Dice additionally renders the app-specific dice-roll
result) · entry-class 2 · PARTIAL 13 · BLOCKED 2 (WhatsApp no APK; TicTacToe
Classic no APK) · persistence storage-round-trip verified 2 · S57 corpus
gate re-run at F-086 HEAD: chessclock 2,040,736 nb, notes 2,073,600 nb,
unote 236,520 nb (run/s57_corpus).

## 2. In-repo fixture achievements (strongest ladder proofs)

| Fixture | What is proven | Ladder | Evidence |
|---|---|---|---|
| **tictactoe_golden** | 9 scripted taps, X→O→X chain, **win state detected**, pixel-deterministic replay | **L9** | battery §29 ("tictactoe_golden PASS, interaction 9/9") |
| **helloworld_golden** | 18-check golden render (typography, density) | L5 | battery §28 |
| **hello_widgets** | most advanced View-world render: ImageView drawable + EditText + Button + TableLayout 3 rows + RelativeLayout layout_below (2,059,104 non-white px golden) | L5 | S38/S39 records |
| **hello_smoke** | click → setText state change under LinearLayout | L7 | S38 record |
| **s38_shift_law** | androidx.collection ScatterMap long-arithmetic law probe (7 laws, 26 checks) | law probe | S38 record |
| EXT-01/02 HelloWorldSelfAware | external APK re-fetched + SHA-verified (`009b4671…`), typography 9/9 + interaction 12/12 checks | L7 | battery G48 stages; §3.0 card |
| density_matrix / G06-G08 / M3 chain | toolchain fixtures, 3-run determinism, ARSC/style chain | — | battery 94/94 |
| F-0xx law chain | F-012/016/020/024/025/026/027/028/030/040/044/050/074/**080**/**081** | — | battery 94/94 |

## 3. Per-app detail cards

### 3.0 HelloWorld — canonical control target (S54)

**HelloWorldSelfAware** `com.appliberated.helloworldselfaware` v1.1.0 · APK
SHA256 `009b467109c4d48d…` (full-sha verified on fetch) · GitHub release
(Appliberated, MIT) · Runtime HEAD `8c575f71` (S54)
- Chain (all stages evidence-logged in the run): APK ZIP parse →
  AndroidManifest.xml (AXML) → resources.arsc + res/ → resource resolution →
  classes.dex load → real Dalvik execution → Activity creation → lifecycle
  onCreate→onStart→onResume → setContentView → View construction → measure →
  layout → draw (Canvas/text/background) → framebuffer screenshot.
- Visual proof: **`docs/evidence/s54_frames/helloworld_ext01_base.jpg`** — the
  app's real text UI rendered on its dark theme ("hello world" + the
  app-computed device hash "i'm 6f1c3a9d2e5b4780" + version lines). The frame
  is DARK-CONTENT (98.7% near-black, 256 colors) and passes the refined gate
  with the battery EXT-01 typography golden (9/9 static checks vs the upstream
  phone screenshot) as its independent content check.
- Interaction: EXT-02 long-press → 12/12 interaction checks (real dispatch into
  the app's DEX handlers, per-frame SHAs in manifest.json).
- Reproducibility: battery re-run 3× this session — ALL PASS.
- Known limitations: none recorded for this app at this HEAD.

### 3.1 SUCCESS — full render + input→state-change

**GM Dice** `de.duenndns.gmdice` v8 · APK SHA256 `1621eda11b5dbc0c…` · F-Droid ·
Runtime HEAD `8c575f71`+F-080/F-081 (S54)
- Lifecycle: launch→RESUMED, rc=0.
- UI [gate PASS]: real dice UI — dialog, "Push buttons to roll!",
  "Long-press buttons to configure dice.", dice bar `1d20 / 1d6 / 1d6+4`,
  and (new at S54, post-F-081) the rendered result label at base.
- Input→state change: `--click-test` 8/8 state_changed; most-changed frame
  renders the dialog roll (1,853,871 px delta). Deterministic: identical
  roll values `14 · 15 · 15` reproduced across S53→S54 HEADs.
- Semantic result: dice values produced by app logic and rendered — the
  strongest corpus-app record in this ledger (L7 chain + app-specific result).
- Screenshots: `s54_frames/gmdice_base.jpg` + `gmdice_after.jpg` (SHA256 +
  gate numbers in `s54_frames/SHA256SUMS`; the S53-era frames were
  byte-identical JPGs before the fixes — cross-HEAD determinism proven).
- Next: persistence (roll state across close/reopen) → L10.

**Chess Clock** `com.chessclock.android` v2.11.2 (vc29) · APK SHA256
`5ca6f2c54c05efe7…` · F-Droid · Runtime HEAD `8c575f71`+F-080/F-081 (S54)
- **[S54 UPGRADE — RENDER_ONLY → SUCCESS/L7.]** The S53 downgrade stood on a
  real defect, and S54 root-caused and fixed it with TWO generic shared-layer
  laws (no app-specific code):
  - **F-080 — Resources.getColor two-arg overload arg-mapping.** The app's
    `color()` helper compiles to `invoke-virtual {recv, resid, theme}` with
    `const/4 theme=0 (null)`; the shadow read a fixed slot and resolved the
    NULL THEME as the resid (`getColor resid=0x0` → black) — black text +
    black buttons on black panels = the "2-color dark blank". Fix: the resid
    is the FIRST int-typed argument (receiver/Theme are references) —
    robust under both receiver conventions. Evidence: `[RES] getColor
    resid=0x7f050005 -> 0xff499ebd` (real ARSC color) after the fix; frame
    went 99.3% near-black/2 colors → 187 colors.
  - **F-081 — M3-19 active-cycle key overload-distinct.** The app's
    `formatTime(J Z)` legally delegates to the `formatTime(J)` overload
    inside its own active window; the name-only cycle key stubbed the
    nested overload to null → the clock text was the literal "null".
    Fix: include the method descriptor in the active-invoke key (JVM/ART
    method identity is (name, descriptor)-exact). Evidence: `setText
    text="10:00"` ×2 after the fix; 0 cycle stubs.
- Visual proof: `s54_frames/chessclock_base.jpg` — the REAL clock face: P1
  "10:00" dimmed (inactive), P2 "10:00" white with the blue active accent
  (`0xff499ebd`), divider, dark theme.
- Input→state change: `--click-test` probed=8 state_changed=3; the
  most-changed frame (`chessclock_after.jpg`, 80,289 px) shows the
  active-player SWITCH — P1 becomes active (white + accent), P2 dims.
  The S52 "tap delta sub-perceptual" observation is superseded: the
  sub-perceptual delta was the blank-class frame, not the app.
- Persistence [S52]: `shared_prefs/default.xml` round-trips (storage-class
  evidence; full L10 ladder now unblocked).
- ASC [S52]: manifest decode 294 ms (`.ChessClock` launcher, minSdk 21/target
  25) + `getclass` (BRONSTEIN/FISCHER delay modes, P1/P2 click handlers).
- Next: L10 persistence ladder (start a clock → close → reopen → state kept).

**MicroTimer** — L7 re-verified at S54 (fresh run): click → `00:00:00` display
appears (31,863 px, frame byte-identical to S53). `s54_frames/microtimer_*.jpg`.

**Simple Stopwatch** — L7 re-verified at S54: Start → Stop/Lap running-state
transition (40,915 px, byte-identical to S53). `s54_frames/simplestopwatch_*.jpg`.

**Heading Calculator** — L7 re-verified at S54: digit click → display value
changes (1,389 px, byte-identical to S53). `s54_frames/headingcalculator_*.jpg`.

**uNote** — [S56: R-NEW-368 premise refuted; L6 input→navigation PROVEN]

S56 HEAD (F-084/F-085). The S52-era verdict "buttons unreachable for input"
was a PROBE-GRID artifact: the 16 probes (y ∈ 300..1780) never covered the
bottom-44px band where the main-menu buttons actually live (EXP092-RENDER:
node 13 Add note at (0,1876) 360×44, node 14 Search (360,1876), node 15
Quit (720,1876); the LinearLayout row is node 12 at (0,1876) 1080×44).
Paint rect == touch rect — no geometry-law divergence existed.

Proof (`--tap 270,1898`):
- `[G06-TAP] DOWN (270,1898) target=13 consumed=1` — canonical hit-test
  + consume on the Add note button.
- `[G06-TAP] UP click_posted=1` — UP posted the click.
- The app's own `NoteMain.addNote` ran → `startActivity →
  Lapp/varlorg/unote/NoteEdition;` — the editor activity was launched and
  its onCreate dispatched (its own calls logged).

That is the L6 input→state→navigation chain for uNote's main menu. Next
ladder rung: NoteEdition input + the notes.db persistence round-trip.

Historical (S54): uNote L5 re-verified at S54 (byte-identical): real list UI (417 colors);
2/4 small click changes (max 2,011 px); input BLOCKED by **R-NEW-368**
(paint vs touch-hit geometry divergence; 16-probe grid found no target) —
honestly not called interactive. Persistence [S52]: notes.db round-trips.
`s54_frames/unote_base.jpg`.

**Bouncy (ball)** v39 — SUCCESS rc=0 full render at HEAD `1b37afd1`
(deterministic frame `4219c511…`, s51_audit era). The F-Droid re-fetch at S53
does NOT match the original corpus SHA — no new verdict recorded. NOT stored
in the S54 gallery (era evidence).

### 3.2 RENDER_ONLY / downgraded — open roots

**Notes (billthefarmer) — [S55 UPGRADE: RENDER_ONLY → L7 mode-switch; content
face still blank-class.]** v139 · APK SHA256 `82cf8bc44c163748…` · F-Droid ·
Runtime HEAD 646952b6 + F-082/F-083 (S55)
- **S55 tree forensics REFUTE the S53 "ListView item paint" hypothesis:** the
  v139 main layout has NO ListView. `U007-INFLATE` inflates 7 views, 0
  unresolved: FrameLayout → ViewSwitcher [ScrollView+EditText (edit face) |
  MarkdownView (read face)] + FAB ViewSwitcher [2× ImageButton].
- **F-082 (generic AOSP ViewAnimator law)** — `setDisplayedChild/
  getDisplayedChild/showNext/showPrevious` were REC-MISS silent no-ops;
  now implemented on the ViewShadow node model (clamp + showOnly visibility
  walk + requestLayout). Regression: `tests/view_animator_law_test.cpp`
  18 checks ALL PASS (battery stage "F-082 ViewAnimator law").
- Runtime proof: `--click-test` FAB → `animateAccept` → `setDisplayedChild`
  → face swap = **2,057,718 px delta (99.23% of frame)**, probed=3
  state_changed=1 (was 0/3 at S53). Frames byte-identical across two runs
  (`docs/evidence/s55_notes_v2/SHA256SUMS`: cf521b16… / ae697935…;
  census + deltas in census_delta.json).
- **Content face root cause PROVEN (R-NEW-377):** the read face is
  `Lorg.billthefarmer.markdown.MarkdownView;` which **extends
  `Landroid/webkit/WebView;`** (verified by the runtime's own dex parser).
  `getSettings/setWebViewClient` REC-MISS → the markdown load pipeline
  never starts → honest inline placeholder (C013-CUSTOMVIEW). Editor face
  (ScrollView+EditText) inflates, measures, renders; fresh data dir =
  empty note is CORRECT behavior.
- Next dependency (pinned, P1 shared framework): a generic WebView content
  model. App-specific markdown rendering is forbidden by the campaign scope
  laws (§25-family). Screenshot: NONE stored for the content face (blank
  class, per policy); the mode-switch pair is recorded as SHA256 + census
  text only (both frames blank-class).

### 3.3 PARTIAL — open roots (the honest frontier)

**Dooz v18** — **[S55: R-NEW-361 ROOT-CAUSED + FIXED by F-083; new frontier
R-NEW-376 pinned.]** The v18 face (HALT-LOOP `Lh/r;.c` → aput-oob) was
DOWNSTREAM of the real defect: the 56th `Ln/a;.r` (Kotlin LongArray-fill
helper) invocation entered `try_recursive_invoke` at depth=80 ==
MAX_RECURSION_DEPTH and was silently dropped (EXP-053 law: ~80KB C++ stack
per DEX frame → 80-frame cap under the 8MB process stack). The dropped void
initializer left map o5051's metadata at heap-zero; the subsequent sentinel
write produced ghost bytes (`0xff007f6600000000`, zero EMPTY 0x80 —
[R361-STORE] traces) → the findImpl probe never terminates. **F-083**
(generic): cmd_run executes on a dedicated 1GB-virtual-stack thread;
MAX_RECURSION_DEPTH 80 → 2048; the limit-drop is ALWAYS loud
([RECURSION-LIMIT] stderr). Post-fix: no HALT-LOOP, no aput-oob, metadata
init correct (`0xff80808080808080` on healthy maps),
MainActivity.onStart/onResume dispatched for the FIRST time in campaign
history. Key traces: `docs/evidence/s55_dooz/` (SHA256SUMS). New frontier
**R-NEW-376**: Compose init ctor chains exceed the 2048-frame budget
(9 cap-climbs; j0/t0/E0 hop evidence captured) — next steps ranked in the
registry entry.

**Dooz v23** — PARTIAL: deterministic pipeline completion; first frame = blank
Compose class `31ddd4d5…` (×4+ runs). Root **R-NEW-344** (Recomposer suspends
without re-posting frame callback). Blank frame is NOT an achievement.

**Telegram v12** — PARTIAL: 540 s inside real init (989k log lines, SafeIterableMap
cycle-stub, 400 REC-MISS), no frame. ASC startup card ranks: REC-MISS
static-init surface → SafeIterableMap iterator law → NativeLoader boundary.

**WhatsApp** — **BLOCKED — APK unavailable** (0-byte placeholder proven; no
unauthorized acquisition per §30). Historical u011_3 probe stands at its HEAD.

**TicTacToe (emmanuelmess)** — blank first frame (Compose/libGDX family).
**BGClock** — WebView root boundary. **muellerma Stopwatch** — no launchable
Activity (L2 by design). **itsfrz TicTacToe / Privacy Friendly Dicer** — app
boundary. **Antimine / Secuso memory / sudoku** — >300 s kills. **TicTacToe
Classic (palahsu)** — APK lost with legacy cache, F-Droid NOT_FOUND (S54);
historical S37 full-render + S44 fully-playable records stand at their
recorded HEADs; re-verification BLOCKED until the APK is re-obtained.

## 4. Persistence testing (S52 experiment, section-14 protocol)

Method: two runs with the SAME `--data-root`; compare data-root tree + frames.
Both S52-tested apps were blank-class then, so these are storage-layer
round-trip proofs only. With ChessClock now L7, the full state-delta ladder
is unblocked and scheduled.

| App | data-root artifact | Survives reopen? | State delta observable? | Verdict |
|---|---|---|---|---|
| Chess Clock | `com.chessclock.android/shared_prefs/default.xml` | YES | no (tap state in-memory by design) | **PARTIAL** — storage round-trip VERIFIED |
| uNote | `app.varlorg.unote/databases/notes.db` | YES | no — input blocked (R-NEW-368) | **PARTIAL** — storage round-trip VERIFIED |

## 5. ASC reconnaissance ledger (S52, unchanged)

Tool: **Droid ASC (MG1937/ASC)** v0.1.1.post1 @ `3279d9dd…`, LOCAL venv
(gitignored). Reconnaissance helper ONLY — never a substitute for runtime
evidence; no ASC output committed; claims cross-checked at runtime.

| Query | Target | Time | Outcome |
|---|---|---|---|
| `getmanifest` | chessclock vc29 | 0.29 s | launcher + Prefs + sdk levels |
| `listclass`/`getclass` | chessclock | ms | fields/handlers recon |
| `findrefs` | chessclock | ms | ref-search semantics validated |
| `getmanifest` | Telegram v12 (73 MB) | 0.32 s | ApplicationLoaderImpl + LaunchActivity |
| `getclass` ×2 | ApplicationLoader(+Impl) | s | full startup-path law list |
| `findrefs type` | SafeIterableMap | s | LiveData/SavedStateRegistry consumers |
| `getclass` | Dooz18 `Lh/r;` | s | ScatterMap.set loop → R-NEW-361 candidates |
| `getmanifest` | WhatsApp placeholder | — | exposed 0-byte file → BLOCKED provable |

S54 added: bytecode-level disassembly (androguard probe, saved as
`scripts/forensic/s54_chessclock_disasm.py`) of `ChessClock.color` /
`formatTime` — this is what pinned F-080/F-081 to exact DEX shapes.
Compact cards: `docs/evidence/s52_asc/`. Raw decompiled files stay
LOCAL-ONLY.

## 6. Screenshot policy (binding)

A screenshot may be committed only if: real recognizable UI · proves something
text alone cannot · linked to an entry above · SHA256 recorded · deterministic
name · ≤100 KB JPG · **passes the gate** (§0 refined law; checker
`scripts/s54_image_audit.py`, gallery emit `scripts/s54_gallery_emit.py`).

**Canonical gallery: `docs/evidence/s54_frames/`** (12 gate-passing JPGs +
`SHA256SUMS` with per-file gate numbers; REJECTED section records the
blank-class refusals). Era galleries: `s53_frames/` (9 JPGs, superseded by
this file but kept for provenance — 9/9 byte-identical JPGs were re-produced
at S54 pre-fix, proving cross-HEAD determinism), `s51_audit/` (6 meaningful
era JPGs). No gallery is generated for its own sake.

## 7. Historical records (superseded pointers)

- `docs/EXECUTION_ACHIEVEMENTS.md` — S52/S53 canonical; absorbed HERE at S54.
- `docs/evidence/SCREENSHOT_INDEX_S51.md`, `SCREENSHOT_INDEX*.md` — era records.
- `docs/history/campaign-reports/`, `docs/evidence/{campaign014,MASTER4…}` —
  era evidence. **Divergent-lineage caution (S54):** campaign reports dated
  Sep 9–15 reference HEADs (`8de5382b`, `d202e43d`, `12cf043f`, `4931f8a4`,
  `7dc70e9c`, `f60634e4`, `e2e91928`) that are NOT objects in this
  repository — those sessions ran in divergent workspaces. Any claim sourced
  ONLY from those reports is treated as unverified here unless independently
  re-proven at a canonical HEAD. (The equivalent laws F-028/F-028h/F-029
  exist in this lineage via `52e4a5c5`.)
- `docs/achievements/*.png` (untracked residue): the gate rejected
  `chessclock_rendered.png` (SHA-16 `e4a2d7c90cd2fd26` = the EXACT S53
  blank-class frame — an old "achievement" image that was actually the
  blank frame; refusal recorded). The remaining 7 PNGs have no provenance
  chain in this repo and are not presented as achievements.

## 0l. S76 — the queued leads EXECUTED: producer traces → root fixes, second interactive app, dialog restart (runtime wave)

| Achievement | Evidence | Status |
|---|---|---|
| **F-146 ROOT-CAUSED+FIXED**: dooz producer trace (s76_g8_disasm.py full disasm of Lg8;.a) proved the pc=569 null receiver's def is `File.getAbsoluteFile()` at pc=565/568 — R-NEW-390 (never-null File-returning sibling of getAbsolutePath) + R-NEW-391 (getCanonicalFile/Path for the DataStore singleton guard) close the chain; dooz now runs through the guard into protobuf schema init; new first divergence F-152 (Llt0;.w pc=808) registered | src/dex/dalvik_engine.cpp (R-NEW-347 block); docs/evidence/s76/dooz_f146_upstream/; docs/foundation/s76/S76_REPORT.md §1 | **FIXED+PROVEN (escape gone, chain moved deeper)** |
| **gmdice roll made VISIBLE (second interactive app)**: three stacked roots — R-NEW-392 (TextView SUBSUMPTION law: Button.getText dispatches via is_subclass_of ancestry walk), R-NEW-393 (View.getBackground() themed-widget non-null law + Drawable.setColorFilter tint record) — onCreate completes 5/5 buttons live; first click diff 1,511,441 px (S75: 0); roll results "6"→"5" render on the result view | src/dex/dalvik_engine.cpp; src/framework/android_shadows.cpp; docs/evidence/s76/gmdice_roll_visible/ (frames + manifest visible_texts) | **PROVEN (click→roll→render)** |
| **snake Dialog-restart hypothesis CONFIRMED+EXERCISED**: static DEX proof (showMessageDialog → AlertDialog "Game Over!" → positive "重新开始" → reStartGame); R-NEW-394 dialog decor LAYOUT + topmost-window TOUCH law (decor node bounds mirroring painter geometry; decor_root_at routing); tap (758,1022)@99 after game-over@94 → RESTART OBSERVED (fresh game runs to frame 115+, wall wrap, 2 captures); CJK label paint residual honestly registered F-153 | src/framework/dialog_shadow.{h,cpp}; src/runtime/execution_engine.cpp (F117 tap site); docs/evidence/s76/snake_dialog_restart/; scripts/s76_snake_dialog_restart.py | **PROVEN (restart@frame-99)** |
| **A7b icon decode capability PROVEN**: resid → arsc.select_file → APK entry → decode_image_bytes → dims/color/FNV-1a logged; f54 + gmdice both decode res/drawable-hdpi-v4/logo.png 72x72 rgba with IDENTICAL fnv1a 0x8a66dfd69a301225 (cross-app determinism); f54 verifier gate strengthened to the A7b DECODED line | src/runtime/execution_engine.cpp (A7b block); scripts/foundation/verify_foundation.py (gate strengthened) | **PROVEN (capability; object semantics future)** |
| Regression: zero regressions across every code change — battery 26/26 rc=0, verifier 24/24 PASS (after the strengthened f54 gate), Level C fidelity replay BYTE-IDENTICAL 90/90; registry 397 → 404 roots (R-NEW-390..394, F-152, F-153; F-146 → ROOT-CAUSED-FIXED) | scripts/foundation/; root_registry.json; scripts/s76_registry_update.py | REGRESSION-CLEAN |

## 0m. S77 — MASTER MISSING-WORK CLOSURE & OPERATIONALIZATION (audit wave)

| Achievement | Evidence | Status |
|---|---|---|
| **Missing-artifact closure as derived views (no second audit universe)**: 9 operational artifacts built over the canonical sources — RUNTIME_FAILURE_REGISTRY.md (32 F-records, status rollup: 6 OPEN / 17 ROOT-CAUSED-FIXED / rest implemented-verified; F-146/148/152/153 expanded with full chains), CRASH_HANG_ANR_REGISTRY.md (crash/hang/ANR classification), SANDBOX_ERROR_REPORT.md + sandbox_errors.json (15 SBX records seeded from real dossiers/sessions + the dooz DataStore chain CLOSED record), SESSION_EVIDENCE_CHAIN.md (4 full session→…→evidence chains, all real paths), PROGRESS_REPORT.md (per-task table + S72–S76 reconciliation), EVIDENCE_LINEAGE.md (8 key claims walked CLAIM→SOURCE→CODE→TEST→EXECUTION→TRACE→SCREENSHOT→SHA→ISSUE), APP_MATRIX.md (14 apps, no inflation), BLAST_RADIUS.md (7 law consumer maps) | docs/audit/ (generated by scripts/s77_build_audit_views.py from root_registry.json + dossiers + s74_ops + knowledge records) | **BUILT+LINKED** |
| **Ledger §18 orphan repair**: master-audit validator FAIL (20× "TESTED without test reference") → every flagged row linked to its EXECUTED S75 code-check in item75_closure.json (pattern + file:line + found flag) — 20/20 linked, 0 downgrades, validator now PASS (375 rows) | docs/audit/master_audit.json; tools/validate_master_audit.py EXIT=0 | **REPAIRED+PASS** |
| **S76 canonicalization**: F numbering RESOLVED from the canonical registry — F-152/F-153 correct (F-145..F-150 pre-exist; F-151 = confirmed numbering gap, never registered); root count 397→404 enumerated EXACTLY (R-NEW-390..394, F-152, F-153); commit accounting 8 unpublished = 5 S75 carry-over (affc0d57..b326acfd) + 3 S76 (2f13abe2..a8704916), origin/main c67230be ls-remote-verified; stale `total` scalar 397→404 fixed with a canonicalization note | root_registry.json (S77 note); scripts/s77_registry_canonicalize.py | **CANONICAL** |
| **False-completion scanner operational**: scripts/s77_false_completion_scan.py — 212 claim lines across 15 canonical reports, 158 with adjacent evidence, 54 flagged (adjudicated: mostly table-cell pointers outside the regex + honest historical lines; 0 evidence-free strong claims found in current canonical corpus; SECURITY_PROFILED-vs-OBSERVED vocabulary restated in EVIDENCE_LINEAGE) | scripts/s77_false_completion_scan.py output (S77_REPORT §scan) | **BUILT+RUN** |
| **Baseline re-established after container reset**: disk 100% full recovered (stale Sep-2..11 backup bundles/logs purged, 1.9G freed — logged); run/ root-owned recreated; engine binary rebuilt (pre-S76 binary lacked R347-FILE/R393-BG/R394-TAP markers) → battery 26/26 rc=0; pixel verifier 26/26 SAME incl. f54 A7B_GATE_OK; Level C fidelity BYTE-IDENTICAL 90/90 at a8704916 | run/s77_baseline/; scripts/s77_baseline_battery.sh; scripts/s77_verifier.py; scripts/s75_fidelity_probe.py | **PROVEN (three gates green)** |
| Honest gaps carried (not silently dropped): F-152 OPEN (Llt0;.w pc=808 producer trace — no speculative patch); F-153 OPEN (CJK dialog label paint); Lsr.run F084 spin; icon Bitmap/Drawable object law; gmdice prefs REC-MISS family (Integer.parseInt/Random); persistence NOT_OBSERVED for 13/14 apps; security PROFILED not OBSERVED corpus-wide; per-step sandbox lifecycle emitter seeded-not-automated; PUBLISH_BLOCKED (8+ commits await tokened push) | docs/foundation/s77/S77_REPORT.md; PROGRESS_REPORT.md | **RECORDED** |

## 0n. S78 — DEEP RUNTIME CLOSURE & EVIDENCE-TO-IMPLEMENTATION (runtime wave)

| Achievement | Evidence | Status |
|---|---|---|
| **PUBLISH DEBT RESOLVED**: 11 wave commits (5 S75 + 3 S76 + 3 S77) pushed to origin/main c6d14d2e with the user-provided PAT (secret scan clean; ls-remote verified); accidental 593MB UUID snapshot commit d51f1815 quarantined on backup/s78-accidental-snapshot (rollback preserved, nothing deleted) | git push output; worklog S78; git ls-remote | **PUBLISHED** |
| **F-152 ROOT-CAUSED+FIXED**: producer trace pc=490 sget Llt0;->o (null) ← doPrivileged silent stub; laws R-NEW-395 (doPrivileged dispatches run(), libcore) + R-NEW-396 (synthetic getDeclaredFields theUnsafe subset); unsafeNPE 9→0; regression 6/6 (real APK) | run/s78_f152_repro; run/s78_regression; scripts/s78_lt0_disasm.py; scripts/s78_f152_regression.sh | **FIXED+TESTED** |
| **F-154 REGISTERED+FIXED** (parent F-152): Collections.EMPTY_SET SGET-MISS → Set.iterator NPE at Lh3;.h pc=36; law R-NEW-397 (EMPTY singletons + Empty-family contract); setIterNPE 8→0; dooz depth chain F-146→F-152→F-154 in registry | run/s78_f152_postfix2/3; root_registry.json | **FIXED+TESTED** |
| **F-153 ROOT-CAUSED+FIXED+OBSERVED**: draw_text ASCII-only byte iteration painted 0 CJK px; law R-NEW-398 (non-ASCII→TextShaper routing + kFaceCJK WenQuanYi fallback; ASCII path byte-identical); 重新开始 0→56 px, 退出 0→28 px; restart re-verified + second life 120 moves/25 turns/2 captures; regression 3/3 | docs/evidence/s76/snake_dialog_restart (S78 re-run); scripts/s78_f153_regression.py | **FIXED+OBSERVED** |
| **gmdice §14 replay**: 5/5 real clicks dispatched into GameMasterDice listeners; first-click diff 1,506,884 px; result band renders; nextInt REC-MISS recorded (no distribution claim); multi-roll PARTIAL (tap hit-test target=0 = next probe) | run/s78_gmdice/clicktest | **REPLAYED** |
| **Knowledge + registry operationalized**: registry 404→409 (F-154 + R-NEW-395..398); knowledge records 31→35 (verified laws 24); dossiers dooz/snake/gmdice updated per §21; derived views regenerated via fixed generator (§24) | root_registry.json; docs/knowledge/laws/LAW-R-NEW-39*.json; docs/audit/* | **CANONICAL** |
| **Disk guard + retention**: scripts/s78_disk_guard.sh (STOP_BUILD threshold + safe-cleanup candidates + never-delete policy); retention policy in S78_REPORT §27-28 | scripts/s78_disk_guard.sh | **OPERATIONAL** |
| **Final regression**: battery 26/26 + verifier 26/26 (A7B_GATE_OK) + fidelity BYTE-IDENTICAL 90/90 after ALL changes | run/s77_baseline/; s75_fidelity_probe output | **GREEN** |
