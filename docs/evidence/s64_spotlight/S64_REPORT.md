# S64 — Open-Source APK Spotlight 3: 3 NEW source-first apps executed; breadth +2 (pmk S6 → deterministic render; FreeKlondike S10 full interaction chain; shopping-list-calc S9 click→state→changed-frame); F-114/F-115/F-116/F-117 generic law families

Date: 2026-09-19 (S64 breadth continuation). RECON at session start: local
HEAD == origin/main == `64d830b4` (S63-PUSH-VERIFY), tree clean; toolchain +
engine ABSENT (container reset — restored via scripts/build/bootstrap_toolchain.sh
+ make); zoekt/csearch/Go ABSENT (rebuilt this session: Go 1.26.0,
zoekt @153817f643cd, codesearch v1.2.0). No new campaign/branch/roadmap.
Mission: increase the count of REAL open-source apps built from source and
executed launch→UI→(input→state→render). Hello/goldens = regression gate only.

## 0. RECON (ground truth, no assumptions)

```text
HEAD == origin/main = 64d830b4fdf895ed174f670ce56648f95b5f82ac (S63-PUSH-VERIFY)
TREE = clean
BATTERY (measured, fresh) = 94 stages: 92 PASS + EXT-01/EXT-02 FAIL
  EXT-01/02 = UPSTREAM-DELETED: Appliberated/HelloWorldSelfAware repo now
  404 (release page + tags gone; verified 2026-09-19 via HTML + API); local
  cache wiped by container reset. Environmental FAIL, precedent = S45
  ("EXT-01/02 fixture-missing" recorded FAIL). Zero relation to engine state.
CORPUS PROVEN = HelloWorld, TicTacToe, bouncy, Anuto(L5), OpenSudoku(L5),
  gmdice(S10/L6), siggen(S7), Blockinger(deferred), dooz, Notes, uNote,
  ChessClock(L7), MicroTimer(L7), HeadingCalculator(L7) + 61-app sweep
TOOLCHAIN = aapt2 8.13.2-14304508 / ECJ 3.33.0 / r8 8.13.23 / android-34
  stubs restored; engine rebuilt (make -j2, 39 objects)
SEARCH TOOLS = zoekt-index/zoekt built @ 153817f643cd (Go 1.26.0,
  GOPROXY=direct); cindex/csearch v1.2.0 built; both USED with evidence (§5)
```

## 1. Candidate selection (REAL survey, fact matrix)

Survey tool: F-Droid index-v2.json (60,145,769 bytes, 4,408 packages) fetched
and scanned LOCALLY (scripts/s64_candidate_survey.py; keyword scan → 69 hits →
52 shortlisted); per-candidate GitHub probes (rate-limited mid-run — core
remaining 0 — then direct git clones). F-Droid package API (v1, -L) used for
version metadata of all 3 picks. Evidence: /tmp/s64_survey/*.json (transcribed
into this report).

Excluded (already corpus or WebView): Anuto, OpenSudoku, gmdice, siggen,
Blockinger (deferred S63), 2048-android (WebView), billthefarmer/* (corpus).

### Fact matrix (forensic evidence, not opinion)

| Field | NEW-001 pmk-android | NEW-002 FreeKlondike | NEW-003 shopping-list-calc |
|---|---|---|---|
| SOURCE | github.com/xvadim/pmk-android @ 100eea1 (2026-06-09) | github.com/VelbazhdSoftwareLLC/FreeKlondike @ 789dba5 (2026-05-10) | github.com/buildsbyben/shopping-list-calc @ e1d3f74 (2026-09-06) |
| LICENSE | GPL-3.0 | GPL-3.0-or-later | MIT |
| F-Droid | com.cax.pmk.ext v3.3.1(vc331); repo v3.3.6(vc336) | eu.veldsoft.free.klondike v2.0.1(vc3) | io.github.buildsbyben.shoppinglistcalc v2.0(vc15) |
| BUILD (aapt2/ECJ/D8) | YES — 19 java → 34 zip entries; APK 0b3bfdc3… | YES — 33 java → 141 entries; APK 985afeb0… | YES — 7 java → 8 entries; APK b51e6ecf… |
| ACTIVITIES | 4 (plain Activity) | 15 (plain Activity) | 2 (plain Activity) |
| FRAGMENTS / support-lib | 0 / none (code) | 0 / none (code) | 0 / none (code) |
| CUSTOM VIEWS | 2 (AutoScaleTextView extends TextView; Slider extends SeekBar) | 0 (ImageView grid) | 0 |
| DATABASE | 0 (prefs) | 0 (file save) | 0 |
| THREADING | Emulator extends Thread | Timer/TimerTask (splash) | 0 |
| INPUT→STATE→RENDER | keypad touch → emulator.keypad → indicator setText | tap card/button → game state → board ImageViews | click/TextWatcher → store → totals setText |
| Compose/WebView/Native/Network | none / none / none / none | none / WebView banner / none / INTERNET unused | none / none / none / none |
| Build complexity | low (aapt2 quirk: PreferenceScreen XML under res/layout/) | low | low (programmatic UI) |
| Known compatibility | Theme.FullScreen dark bg + skin drawables | drawables + meta-data + Timer | programmatic View tree |
| VERDICT | **BUILD** | **BUILD** | **BUILD** |

Deferred-by-facts during survey (breadth law, pre-build): BMI_Calculator
(com.zola.bmi — AppCompatActivity + support-v4 Fragment = FragmentManager
family), AlexCalc (AppCompatActivity + PreferenceFragmentCompat), rttt
(SDL native), com.sidhant.nonogram (Dart/Flutter), TriPeaks (repo name
unresolved). Staging: scripts/s64_stage_candidates.sh (documented
anuto/gmdice law: AGP8 manifests lack package= → staged package= +
versionCode/Name; pmk BuildConfig.java generated per AGP contract).

## 2. NEW-001: pmk-android (Электроника МК-61 calculator emulator)

### Gates A–B (build + load)

```text
Repository   github.com/xvadim/pmk-android @ 100eea1, v3.3.6/vc336 (staged)
Build        aapt2 compile+link → ECJ -source 8 (android-34 stubs) → D8 →
             deterministic zip; 34 entries; warnings only
APK SHA256   0b3bfdc3ea264d86b2f0b75c9969822ff306f1121ec9afbfece75c0044060c82
Load         manifest + resources.arsc + DEX all loaded; package com.cax.pmk
```

### Gates C–E (execute / UI / render) — FIRST POST-FIX RUN rc=0

```text
Run          ./build/miniandroid run --execution-mode real-dalvik --max-seconds 180
Result       rc=0, Status: SUCCESS, Errors: 0, Warnings: 0
Inflate      [U007-INFLATE] root_id=30 views=179 strings=85 ids=0 unresolved=5
Render       2,073,600 non-white px (Theme.FullScreen black bg + skin panel)
             top colors: (0,0,0), (240,240,240) keypad panel, (119,255,119)
             green indicator glyphs
Provenance   AutoScaleTextView indicators "/ / / / / / / / / / / / //",
             "MK 61" model label, "ГРД" angle label, E/F/K indicators,
             ⓘ buttons — ALL real resources/texts of the app
Screenshot   docs/evidence/s64_spotlight/pmk_frame0_indicator.png
             RUN1/2/3 frame SHA c9a2a7035c75c9c8 ×3 (DETERMINISTIC)
```

### Gates F–I (input) — honest partial

```text
click-test   2/2 setOnClickListener lambdas dispatched
             (MainActivity$$ExternalSyntheticLambda2/4) + xml_onClick
             onIndicatorTouched dispatched on AutoScaleTextView (view 40);
             changed_px=0 (indicator tap has no visible state effect)
tap keypad   [G06-TAP] DOWN (540,1400) target=0 — keypad grid renders
             COLLAPSED (skin buttons squeezed at panel top; labels overlap)
             → TableLayout/TableRow weight-measure family (recorded, §6)
Power path   Slider extends SeekBar implements its own touch model in app
             DEX (getThumb().getBounds()/setProgress/onProgressChanged);
             requires thumb-bounds + setProgress state + a DRAG gesture
             (harness has no MOVE gesture — recorded family, §6). Without
             power, emulator==null → onKeypadButtonTouched returns early
             (the app's own null guard) → no state mutation available.
STAGE        S6 PROVEN (deterministic meaningful render, real provenance)
             + input dispatched to real handlers. NOT S7/S8: honest.
```

### The blocker that was fixed (F-114 family, R-NEW-383 ROOT-CAUSED-FIXED)

First run: rc=1, `NumberFormatException: For input string: ""` at
`MainActivity.activateSettings` — escaped onCreate [APP-BOUNDARY].

```text
SOURCE OBSERVATION (disasm, scripts/dex_method_dump.py):
  activateSettings: getString("pref_button_sound", DEFAULT_DUMMY_STRING=null)
  → Integer.parseInt(s==null ? "0" : s); later Float.parseFloat(
  getString("pref_button_text_size", null)) — UNGUARDED.
  DEFAULTS come from PreferenceManager.setDefaultValues(ctx,
  R.layout.activity_preferences, false) — the res IS a PreferenceScreen
  XML stored under res/layout/ (real-world quirk, works on ART).
TRACE: [F114-DIAG] prefs getString a2(t=NULL_REF,is_null=1) — the NULL
  default arrived; the bridge answered "" (typed-zero-string); also
  PreferenceManager.getDefaultSharedPreferences answered NULL receiver
  (a0 NULL_REF) and setDefaultValues was a no-op → no defaults existed.
UPSTREAM (fetched 2026-09-19, aosp-mirror/platform_frameworks_base @ main):
  SharedPreferencesImpl.java:307-313 getString: `return v != null ? v :
  defValue;` (@Nullable defValue — null must return as NULL REFERENCE);
  PreferenceManager.java:67 KEY_HAS_SET_DEFAULT_VALUES; :661-673
  setDefaultValues one-shot guard law; getDefaultSharedPreferencesName
  law = <pkg>_preferences.
SEMANTIC LAW (generic): (a) F-114a null-default law; (b) F-114b
  setDefaultValues law (parse defaults XML → persist key/defaultValue
  pairs + _has_set_default_values flag; CheckBoxPreference→boolean,
  else→string); (c) F-114c getDefaultSharedPreferences law.
FIX: dalvik_engine.cpp prefs bridge (3 handlers).
APP BEFORE: rc=1, 2 uncaught NFEs, no UI. APP AFTER: rc=0 SUCCESS,
  views=179, deterministic frame. SECOND-APP RESULT: omegacentauri
  simplestopwatch prefs loaded via the same laws ([F114B] defaults=24).
REGRESSION: battery 92/94 + goldens byte-identical (§7).
```

## 3. NEW-002: FreeKlondike (solitaire)

### Gates A–B

```text
Repository   github.com/VelbazhdSoftwareLLC/FreeKlondike @ 789dba5, v2.0.1/vc3
Build        aapt2/ECJ/D8; 141 entries; APK SHA256
             985afeb00ae19a3efc9553d098854318028010e5857e8352137457e6e87186bb
```

### The blocker that was fixed (F-115 + F-116, R-NEW-384 ROOT-CAUSED-FIXED)

First run: rc=0 but the app was TRAPPED ON THE SPLASH (0 non-white px,
MenuActivity unreachable):

```text
SOURCE OBSERVATION: SplashActivity.onResume → new Timer().schedule(
  TimerTask, timeout=metaData "timeout"=5000) → task.run() →
  startActivity(Class.forName(metaData "redirect")).
TRACE: [REC-MISS] java/util/Timer;.<init>/TimerTask;.<init>/Timer;.schedule
  → task never ran; metaData.getInt("timeout") → typed-zero 0.
UPSTREAM: OpenJDK java/util/Timer.java sched() law (single-shot delay,
  fixed-delay period, fixed-rate); AOSP PackageItemInfo.metaData contract
  (PackageParser builds the Bundle from <meta-data> children).
SEMANTIC LAWS: (a) F-115 Timer law — TimerTask rides the SAME
  HandlerShadow MessageQueue; period>0 re-enqueues at dispatch
  (__timer_period__ field; fixed-delay). (b) F-116 ActivityInfo.metaData
  law — manifest <meta-data> capture (manifest_reader) →
  getActivityInfo(ComponentName, flags) → ActivityInfo.metaData Bundle
  (numeric→INT32, else STRING); getComponentName law.
FIX: dalvik_engine.cpp (Timer bridge + meta-data bridge +
  getComponentName) + manifest_reader.{h,cpp} + apk_parser.{h,cpp}.
APP BEFORE: splash-trapped, 0 px. APP AFTER: full chain (below).
SECOND-APP RESULT: omegacentauri simplestopwatch Timer fired via the same
  law (its 5.2s demo timer) — recorded as the REASON the launch-frame
  quiescence law was REVISED (F-115b: no clock advance at launch; timers
  fire under time-driven --frames capture; GATE H golden preserved).
```

### Gates C–I — FULL INTERACTION CHAIN (S10)

```text
Run      ./build/miniandroid run --frames 7 --frame-delay 1500
         --tap 5,5 --tap 5,5 --tap 5,5 --tap 5,5 --tap 540,15
         (--tap k fires at frame k per the F-117 scheduled-tap law:
         AOSP input timing = a touch lands at its LOOPER TIME)
Frames   000-003 splash (31ddd4d5b8e6d18e; WebView banner inflated views=2)
         004 GAME BOARD after: F-115 clock 5000ms → TimerTask.run (real DEX
             SplashActivity$1) → Class.forName(MenuActivity) → startActivity
             → MenuActivity.onCreate (54 insns) → tap (5,5)@frame4 hit
             New Game (target=23) → MenuActivity.onClick →
             startActivity(GameActivity) → board render f3c81cfb97f59754
             (green felt (51,170,17), 6 ace-slot outlines, real drawables)
         005-006 tap (540,15)@frame5 hit target=102 (deck) → app's own
             "Deal!" response → frame f9639e683ca736f6 (8,120 px diff,
             in-deck-region)
GATE I   menu(64bf2071f501b3c9) → game(f3c81cfb97f59754): 2,073,600 px diff;
             game → Deal!-response: 8,120 px
DET      RUN1/2/3: game f3c81cfb97f59754 ×3, post-tap f9639e683ca736f6 ×3
STAGE    S10 PROVEN — repeatable end-to-end interaction (launch → splash
         timer → menu → tap → new game → tap → app response → changed
         frame), 3-run deterministic
Evidence docs/evidence/s64_spotlight/fk_{splash,menu,game_board,
         game_deal_response}.png
Honest   cards not yet dealt (deck tap = Deal! hint; actual dealing needs
         the deck-drag/deal interaction — next face, recorded §6)
```

## 4. NEW-003: shopping-list-calc

### Gates A–I

```text
Repository   github.com/buildsbyben/shopping-list-calc @ e1d3f74, v2.0/vc15
Build        aapt2/ECJ/D8; 8 entries; APK SHA256
             b51e6ecf41585ab0a50a2e09200e709c78986f0ca23c4556f719a423052fcfa4
Run          rc=0 SUCCESS 0 errors — NO FIXES NEEDED (first run)
UI           programmatic View tree (setContentView(View) F-023 parent-link
             path): dark theme, "$null" totals row (the app's own initial
             formatting), blue EditText rows + clear (×) buttons, tax-rate
             row "1.00000" — 2,073,600 non-white px
INPUT        --click-test: 7/7 clickable Buttons dispatched → REAL app
             lambdas (MainActivity$$ExternalSyntheticLambda{23,16,15,24,25,9,8})
HANDLER+STATE changed_px 6124/8348/21786, state_changed=TRUE per the app's
             own DEX; before SHA 2cd328b35622a2fa → after 94e90357e4df2340
             (8,348 px diff in the tax-rate row band)
DET          RUN1/2/3 base 2cd328b35622a2fa ×3 + after 94e90357e4df2340 ×3
STAGE        S9 PROVEN (input → real handler → real state mutation →
             changed rendered frame; 3-run deterministic)
Evidence     docs/evidence/s64_spotlight/sc_{frame0_launch,after_click}.png
```

## 5. Search ledger (real usage evidence)

```text
TOOL zoekt (sourcegraph @ 153817f643cd, built this session, Go 1.26.0,
  GOPROXY=direct; zoekt-index -max_trigram_count 100000000 over /tmp/cand
  → shard cand_v16.00000.zoekt 96,144,317 B / 3,277 files)
  Q1 "onKeypadButtonTouched" → 13+ hits (XML android:onClick law + handler)
  Q2 "Emulator extends Thread" → Emulator.java:10 (pmk thread law)
  Q3 "setContentView file:GameActivity.java" → FK line 293
  Q4 "startActivity file:SplashActivity.java" → FK redirect path
  Q5 "addTextChangedListener" → SLC MainActivity:582 SimpleWatcher family
  LEARNED: launch/input/state paths of all 3 candidates mapped pre-build.
  DECISION CHANGED: pmk input path classified as xml_onClick (not only
  touch-listener); build order picked (pmk highest thread/value density).
TOOL csearch/cindex v1.2.0 (CSEARCHINDEX 48,902,993 data B / 5,681,701 idx B)
  Q "onKeypadButtonTouched" → 5+ lines (MainActivity + activity_main.xml)
  Q "Emulator extends Thread" → Emulator.java:10
  Q "addTextChangedListener" → 5 files incl. SLC:582
  (matches zoekt — cross-tool consistency; transcript saved)
TOOL F-Droid index-v2.json local scan (60,145,769 B, 4,408 packages)
  QUERIES 20 keywords → 69 hits → 52 shortlisted (scripts/s64_candidate_survey.py)
TOOL F-Droid API v1 (-L): com.cax.pmk.ext (3.3.1/331), eu.veldsoft.free.klondike
  (2.0.1/3), io.github.buildsbyben.shoppinglistcalc (2.0/15) — version pins
TOOL GitHub API: repos/search + rate_limit (core remaining 0 mid-survey —
  recorded); switches to direct git clones (pinned SHAs) per evidence law
TOOL AOSP (raw.githubusercontent aosp-mirror/platform_frameworks_base @ main):
  SharedPreferencesImpl.java:307-313 (F-114a); PreferenceManager.java:67/
  661-673 (F-114b/c) — upstream contract evidence
TOOL OpenJDK law (F-115): java/util/Timer.java sched()/mainLoop fixed-delay
  repeat law (cited in-code; class contract from the JDK source line model)
TOOL git ls-remote / HTML probes: Appliberated/HelloWorldSelfAware 404
  (upstream deleted — EXT fixture unavailability evidence)

TOTAL_SEARCHES 17 documented queries (5 zoekt, 3 csearch, 1 F-Droid index
  scan [20 keywords], 3 F-Droid API, 2 GitHub API, 2 AOSP raw, 1 upstream
  release probe) + OpenJDK law citation
UNIQUE_QUERIES 17; REPOSITORIES_CHECKED 9 (xvadim/pmk-android,
  VelbazhdSoftwareLLC/FreeKlondike, buildsbyben/shopping-list-calc,
  zikalify/BMI_Calculator, alexbarry/AlexCalc, kirkezz/rttt, sidhant947 ×2,
  Appliberated/HelloWorldSelfAware) + aosp-mirror + F-Droid index
DOMAINS 5 (github, f-droid, aosp, openjdk-law, go module proxy)
RELEVANT_HITS 24; IMPLEMENTATIONS_FOUND 4 (SharedPreferencesImpl.getString;
  PreferenceManager.setDefaultValues/getDefaultSharedPreferencesName;
  java.util.Timer.sched; PackageParser meta-data→Bundle)
TESTS_FOUND 0 (upstreams carry no instrumentation tests for these faces —
  honesty row)
SEARCH_EXHAUSTED no (frontier queries queued in §6)
```

## 6. Compatibility families discovered / updated

```text
1. TABLE-MEASURE-SKIN family (pmk keypad grid collapsed; skin buttons
   drawn at panel top overlapping) — TableLayout/TableRow weight rows.
   Reusability: keyboards/skin-calculators/table games. NOT attempted
   (breadth) — next candidate family.
2. ABS-SEEKBAR-DRAG family (pmk power-on Slider needs a MOVE/drag gesture
   + thumb-bounds + setProgress state). Harness gap: no drag primitive.
   siggen (S7 knob) shares the custom-slider face.
3. TIMER/SCHEDULER family (F-115) — FIXED this session; second consumer =
   simplestopwatch (GATE H golden preserved by the F-115b revision).
4. PREFERENCES family (F-114a/b/c) — FIXED; second consumer = simplestopwatch
   (24 defaults written through the same law).
5. META-DATA family (F-116) — FIXED; any app reading manifest meta-data.
6. SCHEDULED-TAP family (F-117) — harness input timing law; reusable by
   every deferred-screen app (splash/menu flows).
7. CARDS-DEAL face (FreeKlondike) — deck interaction next (open).
```

## 7. Regression

```text
BEFORE engine changes (fresh baseline): 94 stages, 92 PASS, EXT-01/02 FAIL
  (environmental — upstream repo deleted; S45 precedent)
AFTER F-114..F-117: first battery run → G07 lifecycle golden + GATE H
  REGRESSED (F-115b launch-quiescence clock advance fired deferred
  app timers before the launch frame). ROOT-CAUSED and REVISED: the
  launch-frame quiescence keeps the frozen semantics; timers fire under
  time-driven --frames capture. Re-run: 94 stages, 92 PASS, ONLY
  EXT-01/02 (pre-existing) — ZERO regressions; goldens preserved
  (helloworld 26 checks, tictactoe 8 checks, G06 21 checks + 3-run det,
  G08 17 checks + 3-run det, GATE H image pipeline).
```

## 8. Final numbers

```text
NEW APPS SURVEYED:            8 (3 built + 5 deferred-by-facts pre-build)
NEW APPS SOURCE-FORENSICED:   6 (class inventory + call chain each)
NEW APPS BUILT:               3 (pmk 0b3bfdc3, klondike 985afeb0, shopcalc b51e6ecf)
NEW APPS EXECUTED:            3 (rc=0 SUCCESS each)
NEW APPS WITH REAL UI:        3 (179 / 13+ / programmatic views)
NEW APPS WITH MEANINGFUL RENDER: 3 (deterministic frames ×3 each)
NEW APPS WITH INPUT:          3
NEW APPS WITH REAL HANDLER:   3 (pmk handlers dispatched; no state face)
NEW APPS WITH STATE MUTATION: 2 (FreeKlondike, shopping-list-calc)
NEW APPS WITH CHANGED FRAME:  2 (FK 2,073,600 px + 8,120 px; SLC 8,348 px)
NEW APPS L6+:                 2 (FK S10, SLC S9)
```

## 9. Corpus execution matrix (this session's rows)

| App | Source | Build | DEX | Lifecycle | UI | Render | Input | Handler | State | Changed Frame | Stage | Blocker |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| NEW-001 pmk | YES @100eea1 | YES | YES | YES | YES 179 views | YES det×3 | YES (clicks+onClick) | YES (lambdas+onIndicatorTouched) | NOT PROVEN | NOT PROVEN | **S6** | table-measure + seekbar-drag families |
| NEW-002 FreeKlondike | YES @789dba5 | YES | YES | YES | YES | YES det×3 | YES (scheduled taps) | YES (Menu.onClick) | YES (navigation+Deal!) | YES (2,073,600 px + 8,120 px) | **S10** | cards-deal face open |
| NEW-003 shopcalc | YES @e1d3f74 | YES | YES | YES | YES | YES det×3 | YES 7/7 | YES (7 lambdas) | YES (state_changed) | YES (8,348 px) | **S9** | — |

Prior rows unchanged (HelloWorld/TicTacToe/bouncy/Anuto/OpenSudoku/gmdice/
siggen — see docs/ACHIEVEMENTS.md).

## 10. Honest frontier (recorded, not hidden)

1. pmk interaction faces: table-measure-skin + seekbar-drag (§6.1/6.2).
2. FreeKlondike cards-deal (deck drag / deal interaction).
3. EXT-01/02 fixture unrecoverable upstream — battery reports 92/94 until
   a replacement external fixture is frozen (documented environmental FAIL).
4. F-115b semantics: launch quiescence does not advance the clock (frozen
   golden contract); timers need time-driven capture.
