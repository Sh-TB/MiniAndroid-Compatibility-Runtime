# RUNTIME_VIEW_REPORT_013 (§10 — runtime-created views)

## Model before this campaign

Views created AFTER startup (`new TextView/Button/…`, `addView`) existed only
if app code constructed them through the ViewShadow bridge; the renderer and
click probe, however, were tuned around inflated trees. Dialog content — the
single largest category of runtime-created views — never existed at all
(FIX-013-01 root cause).

## What this campaign proved about post-startup views

1. **Dialog decor trees are runtime-created view hierarchies.** Every
   `AlertDialog.show()` synthesizes a LinearLayout root + TextView rows +
   Button nodes in the ViewShadow namespace at callback time, and they:
   - appear in the NEXT rendered frame (measure/layout/draw integration via
     the standard node walk + window painter),
   - receive REAL clicks through the standard candidate discovery +
     `dispatch_click` machinery (gmdice: item rows probed and dispatched with
     app callbacks),
   - compose into a working two-dialog chain (dialog #2 created at click time,
     stacked above dialog #1).

2. **Runtime-created custom views execute their own draw bytecode.**
   `dispatch_custom_view_draw` runs `onDraw(Canvas)` on the view's heap
   object at render time (bouncy ScoreView — real "Select table" pixels).
   The view need not exist at inflation time; it needs a heap object and an
   onDraw — exactly the post-startup creation model.

3. **ArrayAdapter objects accumulate rows at runtime** and their state is
   pulled into windows at show() time (gmdice's dice-set list: "3D20", "4dF",
   … recorded from real `.add` calls during the callback).

## The fixed pre-created views[] suspicion (§10 directive question)

Current architecture: `ViewShadow::nodes_` is a live id→ViewNode map; the
renderer walks from a root id each frame. There is NO fixed pre-created
views[] array anywhere in the render path (the only legacy array is the
synthetic api::View fallback path, which the real-dalvik renderer supersedes).
Evidence: dialog trees created mid-callback render one dispatch later; bouncy
views created by libGDX code render without any registration step beyond
heap existence.

## Remaining gap (honest)

`addView/removeView` on arbitrary existing containers mid-run: nodes are
created and linked (EXP-095 captured LayoutParams), but no corpus app this
campaign exercised add-then-render on a NON-dialog container with a visible
diff. The dialog tree path proves the mechanism; a dedicated probe
(startup tree → click → app addView → next frame) is the designated next
experiment.
