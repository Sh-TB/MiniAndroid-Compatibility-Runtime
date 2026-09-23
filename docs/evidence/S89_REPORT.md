# S89_REPORT — SOURCE-FIRST 200-CORPUS ROOT-CAUSE + GRAPHICS ATTACK

Wave: S89 (continues S88 checkpoint). Base: battery 94/94 ALL PASS at HEAD
(series: 9345e976 → f52b36eb S88 F-NEW-175 → S89 laws F-NEW-183/183b/184 →
185/186/187 → 188/188b). Corpus microscope: 225 F-Droid titles profiled
(smallest-first 110 games + 110 apps + user specials), 66 + 6 named executed
this wave, 6 new A/B-proven engine laws.

## A. Corpus (§17-A)

| Metric | Count |
|---|---|
| Indexed candidates (index-v1 via lysator mirror) | 4,452 |
| Profiles (SHA-pinned, lib-family tagged, APK deleted after scan) | **225** |
| Games / Apps queued | 110 / 110 (+5 specials) |
| Executed this wave (batch runner + named titles) | **72** |
| Blocked (download/cap) | recorded per-title in EXEC_RESULTS.json |
| Plugin-architecture non-executable (MAXS family) | 14 |

Execution states (S89 batch, 66 titles): NONTRIVIAL_RENDER 6 ·
PARTIAL_RENDER 15 · SHELL_RENDER 16 · LOAD_FAILED 29 (incl. 14 MAXS
service-only plugin modules — honest NO_LAUNCHABLE_ACTIVITY family, not a
runtime bug).

## B. Graphics (§17-B)

Named-title evidence this wave: torchlight rc=0/0-exc (L1 shell, Splash
residual), chess F-NEW-175 hold, snakes = GODOT-ENGINE family (fragment
chain cleared, native runtime open), Telegram chain inside
MessagesController (never before), Signal 9 frames L1.
Graphics-gate discipline held: rc=0 was NOT promoted to graphic success
anywhere; torchlight's 2-color frames recorded as SHELL under the S85
near-blank gate.

## C. Frequency map (the user's microscope, 225 APKs)

Lib-family presence per title: webkit **83** · lifecycle **73** ·
appcompat **52** · kotlin **51** · sqlite **50** · fragment **47** ·
coroutines **37** · kotlin-reflection **32** · recyclerview **29** ·
material **29** · constraint **29** · viewpager **27** · compose **21** ·
room **15** · glsl-gles **12** · surfaceview **10** · okhttp **10** ·
libgdx **5** · glide **1** · desugar-j$ **7** · multidex **3**.
Full table: `run/s88/corpus/frequency.json` + `family_table.json`;
per-title profiles: `run/s88/corpus/profiles.json`.

## D. Fixes (SOURCE → LAW → TEST → BEFORE → AFTER → FANOUT)

| Law | Source ground truth | Before → After | Fanout |
|---|---|---|---|
| **F-NEW-175** (S88, regression-proven §10) | AOSP ContextImpl: obtainStyledAttributes never null + TypedArray readers | chess hasValue-NPE → gone; no.thanks attrs=115 theme-backed | View-styled near-blank family |
| **F-NEW-183** | ContextImpl.getExternal*Dirs → non-empty File[]; Telegram AndroidUtilities.getCacheDir `dirs[0]` | Telegram: isDirectory ×9 + List.isEmpty ×12 GONE; chain → MessagesController (first time past S74 frontier) | Telegram family + any getExternal*Dirs caller |
| **F-NEW-183b** | AndroidUtilities.getCacheDir ≡ applicationContext.getCacheDir (identity) | silent-null static dispatch bypassed | Telegram family |
| **F-NEW-184** | AOSP LoadedApk: attachBaseContext receives REAL context (never null) | secuso torchlight rc=1 → **rc=0, 0 exceptions** | Kotlin Intrinsics-checking apps (multidex-family) |
| **F-NEW-185** | StrictMode$Builder chain: modifiers return this; build() materializes policy | termbin rc=1 → **rc=0, 0 exceptions** | StrictMode-onCreate apps |
| **F-NEW-186** | Resources.obtainTypedArray → non-null TypedArray | patolli rc=1 → **rc=0** | theme-array apps |
| **F-NEW-187** | AOSP Color.java 12 named colors (EXACT table; no HTML extras) | "Unknown color: red" IAE → resolved | theme color-name users |
| **F-NEW-188/188b** | androidx FragmentManager singleton identity + findFragmentById @Nullable contract | snakes: FragmentController NPE → GodotActivity.onCreate executes | fragment family (**47/225 titles** — highest-frequency law this wave) |

Batch divergence shape: the 66-title batch shows a LONG TAIL of one-off
divergences (no ≥3-member shared root within the batch) — evidence the
previous high-fanout roots (S87 4-law cluster, S88 TypedArray, S89
storage/attach/fragment) are actually cleared.

## E. Remaining frontier (honest OPEN/PARTIAL/BLOCKED)

1. **WebView asset/content family** (83/225 titles — #1 frequency): local
   HTML/CSS/image assets don't render (S87 ledger, mykanji evidence).
2. **androidx lifecycle/savedstate generated-adapter** (R350-FORNAME;
   no.thanks + Signal + F-NEW-162's 12): CNFE is caught where the dex
   try/catches; Lifecycling.resolveObserverCallbackType still dies on
   newer androidx (Signal).
3. **ConstraintLayout solver** (29 titles; no.thanks onLayout getX null):
   requires measure-pass solver infrastructure.
4. **Compose/Recomposer** (21 titles, F-NEW-161): Simple-Flashlight source-
   read confirmed Compose → whole flashlight family sits behind it.
5. **SQLite cursor family** (50 titles; NewsBlur/cryptopass evidence).
6. **Native runtimes**: libGDX (F-NEW-157, 5 titles), **Godot** (snakes —
   NEW family registered this wave), Kivy (1).
7. **Deep interpreter silent-null** (F-NEW-183b evidence): app-class static
   dispatch can answer null without executing the body — registered as a
   standalone R-NEW investigation.
8. **F084 interpreter-halt loops** (Telegram lambdas LocationController/
   MessagesStorage) — collection-iteration loops that never advance.
9. WhatsApp: OUT_OF_SCOPE_NON_OPEN_SOURCE (no legitimate provenance; used
   only as a documented gap per the open-source constitution).

## F. Evidence

- `run/s88/corpus/{profiles,frequency,family_table}.json` — corpus microscope
- `run/s89/batch/EXEC_RESULTS.json` + per-title logs — batch execution
- `run/s89/{telegram_check,snakes_ab3,torchlight_ab,chess_ab}.*` — named A/Bs
- Worklog: `worklog.md` Task ID S89
- Commits: F-NEW-175 (S88) · 183/183b/184 · 185/186/187 · 188/188b · scripts

## G. Regression

**BATTERY GATE: ALL PASS (94 stages)** after every law, including golden
ladder + G04 density-matrix differential oracle + EXT-01/02 externals
(toolchain re-bootstrapped from pinned provenance after container resets:
aapt2 8.13.2-14304508, ECJ 3.33.0, r8 8.3.37, platform-34 stubs —
frame-level goldens byte-identical).
