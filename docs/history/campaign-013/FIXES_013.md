# FIXES_013 — Campaign 013 fix ledger

Every fix: root cause → files → regression evidence → APK unlock count → commit.
All commits on branch `campaign-013` (baseline `v0.13.0-baseline` = `ea81e00`).

---

## FIX-013-01 — Dialog/Toast/ArrayAdapter object model (B1)

- **Root cause.** `AlertDialog$Builder` / `AlertDialog` / `Dialog` / `Toast` /
  `ArrayAdapter` calls fell through to the API bridge as invisible no-ops. Real
  app callbacks executed (proven in 011.2/011.3 click probes) but nothing
  became pixels — gmdice's first-launch dice dialog produced an honest 0-px
  second frame.
- **Implementation.** `framework/dialog_shadow.{h,cpp}` (new): DialogWindow
  state (builder options → create() → Dialog object → show/dismiss/isShowing),
  DecorView trees as REAL ViewShadow ViewNodes (input participates in the
  standard dispatch), window chrome painter (dim overlay + panel +
  title/message/items/buttons) composited into the same framebuffer before the
  fb copy, stacked-window alpha compositing, Toast windows.
  `ArrayAdapterShadow` records per-object item lists backing setAdapter
  dialogs. `ViewNode.dialog_owner_obj/dialog_which` route clicks as
  `DialogInterface$OnClickListener.onClick(dialog, which)`; no-listener buttons
  still dismiss (AOSP behavior).
- **Files.** dialog_shadow.{h,cpp} (new), android_shadows.h, dalvik_engine.{h,cpp},
  execution_engine.cpp, application_runtime.{h,cpp}, main.cpp, Makefile.
- **Evidence.** gmdice (SHA `1621eda1…`): click "…" → dice-set dialog VISIBLE
  (1,737,264 px diff, click_frame_0.png); dialog item click dispatches
  `which=2` → the app opens a SECOND dialog (stacked compositing verified by
  pixel analysis: two windows, per-window dim); 4/4 probed views
  changed_px>0; 4 click frames saved.
- **Regression.** Fixtures 8/8 + 5/5; simplestopwatch golden `2a12587a` EXACT;
  Telegram golden `088ea640` EXACT.
- **Unlocks.** gmdice REAL_UI → REAL_INTERACTION; dialog layer shared by every
  AlertDialog-class app (unote menus, Telegram dialogs next).
- **Commit.** `a5f7995`.

## FIX-013-02 — Hierarchy-aware shadow dispatch (B4)

- **Root cause.** Shadows claim framework classes by NAME.
  `ActivityShadow::handles_class` had grown a hand-maintained list of app
  class names (`/GameMasterDice;`, `/StopWatch;`, `/Notes;`, `/NoteMain;`,
  `/MainActivity;`, `/AndroidLauncher;`) — the per-app special-casing the
  directive forbids. `ChessClock` (and any new app) matched no claim →
  setContentView/findViewById silently no-op'd → synthetic default screen.
  chessclock + stopwatchmuellerma both rendered the identical fallback
  (`eb16ab5c…`).
- **Implementation.** `try_shadow_dispatch` Pass 3: walk the receiver's DEX
  superclass chain (`class_to_superclass_`) and retry the shadow registry per
  ancestor. `ChessClock → android/app/Activity → ActivityShadow`. Benefits
  ALL shadows (views, threads, …) for ALL apps — zero special cases.
- **Evidence.** chessclock: 0 views → 15 view nodes, 2,072,520 px REAL_UI,
  `[C013-HIER]` dispatch trace.
- **Unlocks.** chessclock (+2 apps downstream with the ARSC fix).
- **Commit.** `cb621fc` (with FIX-013-03).

## FIX-013-03 — Real-tree inflation policy + screen-gated custom-view visibility (B5-class)

- **Root cause (a).** The UNIFIED_011 recovery guard accepted an inflated tree
  only if `views>=5 || strings>0`; weaker REAL trees were thrown away in favor
  of the synthetic default screen — the exact fake-positive the evidence
  standard forbids.
- **Root cause (b).** App-defined leaf views cannot run their own onDraw, so
  real trees could render all-white (headingcalc: LinearLayout + 2 custom
  views, 0 px).
- **Implementation.** (a) accept ANY inflated tree with a root; rejection only
  when inflation produced none. (b) deferred grey placeholder drawn ONLY when
  the whole frame would otherwise be ~blank (<5000 non-white px) — working
  apps keep exact pixels.
- **Evidence.** headingcalculator fallback → real tree; simplestopwatch
  BigTextView placeholder disabled by the screen gate → golden `2a12587a`
  EXACT (the gate was introduced precisely because the first, per-node
  version changed this golden — caught by the regression gate, fixed, and
  re-verified).
- **Commit.** `cb621fc`.

## FIX-013-04 — ARSC file-backed value-path resolution (§18)

- **Root cause.** `apk_path_for()` matched resources to APK files by entry
  NAME stem. AGP resource obfuscation renames files (`res/0D.xml`,
  `res/w6.xml`) and rewrites entry VALUES; the name never exists as a file.
  Probe (`tests/c013_arsc_probe.cpp`, notesbillthefarmer `0x7f070003`):
  `resolve() → layout/main`, config value `STRING "res/w6.xml"`,
  `apk_path_for → NONE` → inflate root_id=0 → synthetic screen.
- **Implementation.** Value-first resolution — a file-backed entry's STRING
  value IS the path (the real Android model); legacy name matching kept as
  fallback.
- **Evidence.** notesbillthefarmer 0→7 views (31,752 px); **bouncy (libGDX)
  ACTIVITY_FAILED → 280 view nodes, 2,073,600 px**; unote → 64 view nodes,
  2,073,600 px.
- **Regression.** Fixtures 8/8+5/5; simplestopwatch `2a12587a` EXACT; Telegram
  `088ea640` EXACT. gmdice frame-1 SHA moves 158040→1744539 px because the
  app's first-launch dialog now RENDERS (previously silently dropped) —
  app-driven change, documented.
- **Commit.** `b9d93cc`, tag `v0.11.4-fix-01`.

## FIX-013-05 — Real onDraw(Canvas) execution (§10/§15/§19)

- **Root cause.** Apps draw custom views via `View.onDraw(Canvas)` +
  android.graphics calls; the runtime never executed that bytecode. Custom
  views painted nothing and libGDX canvas-backend games could not reach a
  real frame.
- **Implementation.** `framework/canvas_shadow.{h,cpp}` (new): CanvasShadow
  records drawColor/drawARGB/drawRGB/drawRect/drawCircle/drawLine/drawText/
  drawPaint during a REAL `try_recursive_invoke(view_class,"onDraw",
  {view,canvas})`; Paint state per heap object; replay() rasterizes recorded
  ops into the same framebuffer at the view's measured bounds (span-rasterized
  circles, stepped lines, stroke boxes). Dotted→slashed descriptor
  normalization (heap `class_descriptors` are dotted; the DEX index is
  slashed — root cause of the first dispatch=NO). Registration fixed in the
  actual `run` path (main.cpp registry).
- **Evidence.** bouncy ScoreView.onDraw `dispatched=YES`, app ops replayed —
  the idle-state "Select table" content is REAL app-driven pixels.
  simplestopwatch BigTextView.onDraw `dispatched=YES ops=0` (uncaptured APIs)
  → graceful degradation, golden EXACT.
- **Known boundary (next).** CanvasFieldView.onDraw lives in bouncy's
  secondary DEX (multi-dex class-index method completeness); Canvas
  translate/rotate/Path/Bitmap ops not yet recorded.
- **Commit.** `cd0463f`.
