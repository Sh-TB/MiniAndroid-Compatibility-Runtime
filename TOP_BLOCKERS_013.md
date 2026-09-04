# TOP_BLOCKERS_013 — ranked shared blockers (post-campaign state)

Ranked by affected-APK coverage × architectural leverage. Status reflects the
campaign-013 HEAD after FIX-013-01..05.

## RESOLVED this campaign

### B1 — Dialog / Toast / adapter rendering (RESOLVED, FIX-013-01)
- **Was:** every AlertDialog/Toast/ArrayAdapter call was an invisible bridge
  no-op; real callbacks produced no pixels (gmdice honest 0-px since 011.3).
- **Now:** Dialog→Window→DecorView object model with real ViewNode trees,
  show/dismiss/isShowing, DialogInterface click routing, stacked-window
  compositing, ArrayAdapter-backed items, Toast windows.
- **APK evidence:** gmdice two-dialog chain (4/4 interactions changed pixels).

### B4 — App-class shadow dispatch by name list (RESOLVED, FIX-013-02)
- **Was:** hand-maintained app-class list inside ActivityShadow; ChessClock
  silently no-op'd setContentView.
- **Now:** superclass-chain shadow dispatch — general for all apps/shadows.

### B5a — Inflation rejection guard (RESOLVED, FIX-013-03)
- **Was:** real trees under 5 views / 0 strings replaced by a synthetic
  default screen (fake-positive per §25).
- **Now:** any real inflated tree wins; rejection only when no root.

### RES-1 — Obfuscated ARSC file-backed values (RESOLVED, FIX-013-04)
- **Was:** name-stem matching; all layouts of AGP-obfuscated APKs unresolved
  (bouncy, notesbillthefarmer, unote family).
- **Now:** value-first path resolution (real Android semantics).

### CV-1 — Custom-view onDraw never executed (RESOLVED for canvas primitives, FIX-013-05)
- **Now:** real onDraw bytecode executes; recorded primitives replay into the
  framebuffer; graceful degradation when APIs are uncaptured.

## OPEN (ranked, with evidence)

### OB-1 — Compose runtime boundary (dooz, droidify) — ARCHITECTURAL
- dooz/droidify: 1 view, 0 px. droidify dies in the appcompat/activity-init
  chain BEFORE setContent (MainActivity.backHandler completed = Compose code
  RUNS, no composition root materialized). Next primitive: Compose
  ViewRoot/Composition → node tree → measure/place/draw. Carry-over from the
  011.x dooz livelock work (children never compose).

### OB-2 — AppCompat/fragment activity chains (stopwatchmuellerma, openlauncher, simplekeyboard)
- stopwatchmuellerma: Application.onCreate runs; AppCompatActivity entry
  chain never reaches app onCreate → no view tree. openlauncher:
  OnBoardActivity.skipStart completes but no inflation (appcompat +
  fragment/backstack prerequisites). simplekeyboard: PreferenceActivity
  headers model. Next primitive: AppCompatActivity.onCreate super-chain +
  fragment transaction machinery.

### OB-3 — GLES/libGDX GL backend (tictactoe, bouncy GL mode) — STAGED
- tictactoeemmanuelmess: libGDX initializeForView creates the GLSurfaceView
  successor view; setContentView(View) receives it (arg obj#6) but the view
  is not a ViewShadow node and no EGL context exists. Stage plan (unchanged
  from directive): Stage 1 context+clear+renderer callbacks → Stage 2
  shader/program → Stage 3 buffers/textures → Stage 4 real libGDX frame →
  Stage 5 interactive frame. Canvas-backend apps are already served by
  FIX-013-05 (bouncy).

### OB-4 — Multi-dex class-index method completeness (bouncy CanvasFieldView)
- CanvasFieldView.onDraw exists in classes2.dex; the injected index resolved
  only setManager. ScoreView (primary DEX) works. Next: index-merge parity
  for injected classes.

### OB-5 — App-side validation exceptions mid-onCreate (microtimer)
- IAE raised by the app's own obfuscated androidx-Preconditions code at
  MainActivity.onCreate pc=1724; propagates (011.3 semantics), onCreate
  aborts before UI. Per §9 not suppressible — requires the missing semantic
  that makes the precondition pass (upstream API return values).

### OB-6 — WebView-based UIs (tinymusicplayer)
- v4 APK now SHA-locked and boots (upgrade from BOOT_FAILED); UI is
  WebView-hosted — WebView is out of campaign scope, documented boundary.

### OB-7 — Canvas state/geometry ops (translate/rotate/Path/Bitmap, stroke-accurate circles)
- CanvasShadow records a flat op list; save/restore/translate are accepted
  but not stateful. Needed for richer custom views (bouncy field once OB-4
  lands).

## Historical BUG-01..85 reconciliation
See BUG_RECONCILIATION_013.md — hypotheses only; current-campaign evidence
above is the authority.
