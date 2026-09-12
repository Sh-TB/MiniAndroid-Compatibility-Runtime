# MASTER CAMPAIGN — §2 REAL-APK FAILURE MATRIX + §3 ROOT-CAUSE CLUSTERS

Base HEAD: `cc9e67ef` (clean, origin/main in sync — verified via `git ls-remote`).
Baseline: BATTERY GATE ALL PASS (52 stages) — fresh run at this HEAD before any
engine change (the battery harness `scripts/test/run_test_battery.sh` was restored
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

---

# MASTER-2 WAVE-2 MATRIX ADDENDUM (2026-09-07, HEAD 3fb28e26+)

Base: battery 54/54 ALL PASS at wave-1 post-fix state (zero drift at
40988007). Corpus: 16 APKs SHA-verified; OpenLauncher registry record was
STALE — source URL serves b3320463… (re-fetched, identical); arbitrated
and corrected (no substitute taken). Telegram stays BLOCKED-ON-FREEZE.

## Measurement cluster (§13, HIGH PRIORITY) — CLOSED

Root-cause chains (reverse-traced, not symptom-patched):
- FIX-MEASURE-001: class_chain_defines_method returned TRUE at
  Landroid/view/View; — framework-owned onMeasure counted as an APP
  override → aosp_default_measure=false blocked the AOSP getDefaultSize
  law. scope Scope/Unit measured 0x0 (DEX ground truth: no onMeasure).
- FIX-MEASURE-002 (a-d): AOSP RelativeLayout.onMeasure (android-15) —
  two dependency-sorted passes, applyHorizontal/VerticalSizeRules,
  getChildMeasureSpec (both-edges → EXACTLY(end-start)), positionChild*
  edge caching + onLayout REPLAY. Missing rule families (alignLeft/
  alignTop/alignBottom/alignParentLeft/Right), compiled-boolean law
  (typed 0x12, no raw string), sentinel-OR law (-1 |= bit stays -1 — the
  alignParent/center bits were DEAD since introduction), overlapping
  legacy masks (0x50 & 0x30 = 0x10) replaced by explicit rule booleans.
- FIX-MEASURE-003: EXACTLY spec always wins the resolve (the view's own
  lp never enters its own resolve) — the XML 0dp no longer overwrites the
  weight share.
- FIX-MEASURE-004(+b): AOSP LinearLayout weight re-distribution INSIDE
  onMeasure (every measure pass), cross-axis spec = first-pass child_spec
  law. Hostile-safe: RL cycle → declaration-order fallback + diagnostic.

Results: scope 4.22% → **99.77%** (3× ff60bf23…); unote 9.11% → **91.95%**
LAWFUL (alignParentBottom finally executes; buttons row lands at the
bottom edge; 3× 7b30d522…); headingcalculator weight=1000 keypad rows
1080x480 (was 0) — keypad still laid off-screen in the draw-consuming
pass (CalculatorDisplay/CalculatorKeypad cross-pass oscillation) =
REMAINING BLOCKER, evidence [VSTACK]/[SPEC-OUT] traces; other 13 APKs
pixel-identical. 54/54 battery ALL PASS; goldens byte-identical.

## Interaction cluster (§20) — Tier-2 now 5 APKs

- FIX-INPUT-001 (AOSP DeclaredOnClickListener): android:onClick buttons
  are tap-dispatched through the precise tap path (hosting-Activity
  handler resolution) — unote search → 2,011px state change.
- FIX-INTENT-001 (AOSP Intent(Context, Class)): const-class descriptors
  survive to the component; unote addNote → real DEX addNote →
  NoteMain.onPause → NoteEdition.onCreate (462 real instructions) →
  onResume → NEW VIEW ROOT → 112,840px second screen. **First cross-
  Activity navigation from a real APK.** 3× bbb46431….
- gmdice (already SHA-frozen): 5 programmatic-listener clicks DISPATCHED
  to real DEX + 3 DIALOG_CLICK; 1,401,540px before/after diff; 3×
  50f58884….

F16 interaction proofs now: simplestopwatch, unote (incl. cross-Activity),
bouncy, **gmdice (new)**, EXT-01 HelloWorldSelfAware (long-press →
clipboard → toast, battery-guarded) = **5 independent real APKs**.

## §23 corpus expansion (+4, frozen at fetch, registry_additions.json)

| APK | SHA-256 (16) | result |
|---|---|---|
| org.ligi.survivalmanual_500 | 6dbc943ce56b34a5 | default-window render (AppCompat shell family), 3× eb16ab5c… |
| com.github.muellerma.coffee_47 | ae4688fe48e75151 | default-window render (tile/service family — muellerma precedent), 3× eb16ab5c… |
| org.billthefarmer.diary_1105 | 979e8cd8702ab5c0 | SUCCESS, real content 99.88%, 3× 1605eb99… |
| org.secuso.privacyfriendlytodolist_103 | 80c6f68ec94a5611 | BLOCKED-ON-TIME (>150 s) inside androidx ResourcesCompat.inflateColorStateList — performance layer, recorded with logs |

Corpus is now 20 APKs. Remaining blockers unchanged in kind: Compose
(dooz), GLSurfaceView/libGDX (tictactoe), WebView/androidx-webkit
(bgclock), Fragment/ViewPager host (openlauncher), IME surface
(simplekeyboard), AppCompat default-window shells (survivalmanual,
coffee), androidx color-state-list perf (SECUSO todo), calculator keypad
off-screen placement (headingcalculator, evidence recorded), timer-tick
labels (chessclock/microtimer), Telegram freeze-blocked.
