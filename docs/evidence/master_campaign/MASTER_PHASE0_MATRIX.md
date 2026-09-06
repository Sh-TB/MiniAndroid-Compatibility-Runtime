# MASTER CAMPAIGN — §2 REAL-APK FAILURE MATRIX + §3 ROOT-CAUSE CLUSTERS

Base HEAD: `cc9e67ef` (clean, origin/main in sync — verified via `git ls-remote`).
Baseline: BATTERY GATE ALL PASS (52 stages) — fresh run at this HEAD before any
engine change (the battery harness `scripts/run_test_battery.sh` was restored
from the sandbox copy; it is still sandbox-only and now also carries the
campaign's fix commits' state — tracked as a known gap that the harness is not
in git).

## 1. Phase-0 matrix at base HEAD (before fixes)

Pixel audit = non-background % of the 1080×1920 screenshot (background =
top-left pixel color). "views" = per-view measure/layout tree size
(U007_LAYOUT_DEBUG=2). Blank ≠ no screenshot: blank = uniform-color render.

| APK | SHA-256 (16) | Load | Status | nonbg% | views | first failing layer |
|---|---|---|---|---|---|---|
| headingcalculator | 274ec873098eea51 | OK | SUCCESS | 6.71 | 135 | — (G11-proven) |
| microtimer | 79c6f730f648 | OK | SUCCESS | 50.63 | 52 | — (G11-proven) |
| billthefarmer_notes | 82cf8bc44c16 | OK | SUCCESS | 99.89 | 16 | — (renders, dark theme) |
| simplestopwatch | b3ec1a5ec24c | OK | SUCCESS | 4.05 | 22 | — |
| gmdice | 1621eda11b5d | OK | SUCCESS | 24.61 | 20 | — |
| unote | be91103f0e7d | OK | SUCCESS | 9.11 | 28 | — |
| chessclock | 5ca6f2c54c05 | OK | SUCCESS | 2.71 | 30 | DRAW-content: time labels render "null" (app's own construction-era null-concat — same class as G11 microtimer 'null:null:null', classified LAWFUL) |
| muellerma_stopwatch | 3b6a10c8dc8d | OK | PARTIAL | — | — | F-MANIFEST: activity-less app (G11 FIND-G11-NOACTIVITY-001, classified) |
| tictactoe (emmanuelmess) | 760fe5acf7b3 | OK | SUCCESS | 0.00 | 2 | F12/GL: libGDX AndroidApplication — RelativeLayout inflated, zero children; content requires GLSurfaceView/GL init (native libgdx.so present) — documented §29 scope |
| dooz | d81292cd346d | OK | SUCCESS | 99.86* | 2 | F12/COMPOSE: androidx ComposeView inflated as leaf; composition requires Compose runtime (§29) |
| bgclock | 72c140b0083e | OK | SUCCESS | 0.00 | 2 | F12/WEBVIEW: WebView leaf; androidx-webkit init path throws IllegalArgumentException (compat-continued), WebView itself §29 |
| openlauncher | b7900f56ccbe | OK | SUCCESS | 99.86* | 20 | F12/FRAGMENT: CoordinatorLayout+ViewPager inflate; material-intro slides are Fragment-based — ViewPager/Fragment host layer out of §29 scope |
| simplekeyboard | d83060833dc2 | OK | SUCCESS | 98.87* | — | IME app: renders default window only (no IME surface layer — §29 input-method scope) |
| kiss | da6ab0b1219a | OK | PARTIAL (rc=1) | 98.87* | 15 | **F2-CLASSLINK + F-LIFECYCLE (FIXED this campaign — see §3 cluster A)** |
| bouncy (NEW #1) | ffda0d9cb0b1b2aa | OK | SUCCESS | 83.43 | 62 | renders score bar + buttons; field area layout correct (weight=9000 re-measured 1773 EXACTLY); CanvasFieldView.onDraw content partial |
| scope (NEW #2) | 0e34439ce43bfd47 | OK | SUCCESS | 0.00 | 10 | **F8 default-onMeasure law gap — see §3 cluster B (diagnosed)** |

\* high nonbg% is the window-background-vs-status-bar artifact; PIL color
census confirms near-uniform render (documented in phase0 result JSONs).

## 2. Matrix columns per campaign §2 (all 16 APKs)

Load=OK for all 16. Manifest=OK for 15 (muellerma = activity-less by design).
Application/Activity=OK for 15 (simplekeyboard = IME-only). DEX execution
reaches app code for 14/16 (tictactoe blocked at GLSurfaceView init,
bgclock blocked at WebView). Constructor law (F6) proven on 5 real APKs with
custom View classes: headingcalculator, microtimer, bouncy, kiss, scope.
Render (any non-window content): 9/16. Interactive state change (F16):
3/16 → simplestopwatch, unote, bouncy (all 3× byte-identical deterministic).

## 3. Root-cause clusters

### Cluster A — FIXED: dual shadow registry + constructor-direct violations (KISS)
Evidence chain (fr.neamar.kiss v224, classes.dex ground truth verified by an
independent DEX reader):
1. R8 full-mode horizontal class merging: `TaskExecutor`, `DefaultTaskExecutor`,
   `ActivityResultContract` merged away; **24 classes now extend
   `Lfr/neamar/kiss/db/DBHelper;`** (18 → `Lkotlin/ResultKt;`, 10 →
   `...Forwarder;`). Legal R8 output; ART-compatible.
2. Every merged class's constructor begins
   `invoke-direct {v0}, Ljava/lang/Object;-><init>()V` (declared=Object —
   proven by [C013-HIER] declared= evidence after instrumentation).
3. The engine let `Object.<init>` fall through to the shadow layer, where the
   C013 hierarchy walk (ArchTaskExecutor → DBHelper, from the DEX superclass
   map — correct!) reached `ViewShadow::handles_class` — a CATCH-ALL that
   returns true for ANY user-defined class ("might be a View") — which claimed
   `<init>` and returned `handled_void`.
4. Independently: androidx `LifecycleRegistry.enforceMainThreadIfNeeded`
   (R8-inlined `isMainThread`) evaluates
   `Looper.getMainLooper().getThread() == Thread.currentThread()`. The engine
   owns TWO shadow registries (main.cpp cmd_run vs ApplicationRuntime) with
   different shadow sets; the cmd_run path's registry LACKED
   ThreadShadow/LooperShadow, so the identity chain fell to the legacy bridge
   (Looper.getThread → unhandled; Thread.currentThread →
   get_or_create_singleton) and the ids mismatched → IllegalStateException →
   registerForActivityResult/LifecycleRegistry failures → KISS PARTIAL (rc=1).

Fixes (generic, law-grounded — commit `class/linker/dispatch` + `shadow/arch`):
- `register_platform_shadows(ShadowRegistry&)` — ONE canonical registration
  list; both registry owners call it (F20 §23 duplication-causes-bugs case).
- `Object.<init>` no-op law in `execute_invoke_direct` (ART law: empty
  compiler-mandated constructor never dispatches).
- C013 ancestor walk skips `<init>`/`<clinit>` (constructors are DIRECT
  targets; there is no virtual constructor dispatch in ART).
Post-fix: KISS rc=0, PARTIAL SUCCESS, screenshot 3× byte-identical
(`eb16ab5c…`); battery 52/52 re-run ALL PASS; helloworld golden 26/26.
Residual (honest): `KeyboardManager.performRestore` ISE compat-continued;
registerForActivityResult exceptions reduced but not zero — the launcher's
full surface (wallpaper, adapter-driven list content) is not complete.

### Cluster B — DIAGNOSED (law written, fix queued): default onMeasure law (scope)
`org.billthefarmer.scope` custom views (Scope/YScale/XScale/Unit — plain View
subclasses, wrap_content) measure 0×0/0×1920. AOSP law
(View.java `getDefaultSize`, called by the DEFAULT `View.onMeasure`):
AT_MOST/EXACTLY → `specSize` (parent-available), NOT content size. The
runtime's leaf measure returns content-only (text/image) → 0 for plain
custom views without an onMeasure override. The law-faithful fix requires
the "does this class override onMeasure?" query (dex-report-backed) at
measure time — same seam as F10's real-DEX onMeasure execution. Recorded as
the top queued F8 item; NOT silently patched with a heuristic.

### Cluster C — documented §29 boundaries (unchanged, precisely identified)
- tictactoe: libGDX GLSurfaceView/native (F12/F-NATIVE)
- dooz: Compose composition runtime (F12)
- bgclock: WebView + androidx-webkit (F12)
- openlauncher: ViewPager/Fragment host + design-lib CoordinatorLayout (F12)
- simplekeyboard: IME surface layer (§29)
- chessclock "null" labels: app's own construction-era state (G11
  microtimer precedent); real render = two 953/954px weighted halves +
  divider (weight law CORRECT — re-measure verified at EXACTLY 953/954)

## 4. F16 interaction proofs (input → real DEX callback → state change → frame)

| APK | handler dispatched (real DEX) | base frame | post-tap frame | 3-run |
|---|---|---|---|---|
| simplestopwatch | onButtonStart, onButtonReset | `ed1dfc89…` (= G10 frozen golden) | `6823fc04…` | byte-identical ×3 |
| unote | search, quit | `8197687f…` (= G11 frozen golden) | `86aed616…` | byte-identical ×3 |
| bouncy | 12/12 probed handlers (ScoreView.scoreViewClicked, doPreviousTable, doShowTableList, doNextTable, doPreferences, doQuit, hideHighScore, …); 3 views changed 158,760 px | `072ff178…` | `14500d73…` | byte-identical ×3 |
| EXT-01 HelloWorldSelfAware | onLongClick → Clipboard → Toast (GOLDEN-02, unchanged) | — | 12/12 checks | (battery) |

chessclock probed 8 (4 handlers) but 0 state change (timer state layer — G07
future). microtimer probed 12, 0 change (timer-tick scheduling — recorded G11).
notes probed 3, 0 change (menu-driven app). gmdice produced no click report
(listener wiring not yet probed by the click-test surface — recorded).
