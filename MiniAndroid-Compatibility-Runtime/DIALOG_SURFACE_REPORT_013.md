# DIALOG_SURFACE_REPORT_013 (§4/§5/§6/§7/§20)

## Object model shipped (FIX-013-01)

The smallest reusable dialog architecture — no hard-coded rectangles, no
fake dialogs:

```
AlertDialog$Builder.<init>      → DialogWindow (builder state) bound to heap obj
  .setTitle / .setMessage       → recorded (resid resolved at render time)
  .setItems / .setSingleChoiceItems / .setAdapter → item list + listener
  .setPositive/Negative/NeutralButton → label + DialogInterface listener
  .setView                      → custom content subtree re-parented
  .create()                     → Dialog heap object bound to same window
  .show()                       → showing=true; DecorView tree built as REAL
                                  ViewShadow ViewNodes; window geometry computed
Dialog.show / dismiss / cancel / isShowing → same window lifecycle
Toast.makeText / show           → transient bottom window
ArrayAdapter.<init>/add/getCount → per-object item lists
```

The dialog participates in:
- **measure/layout/draw** — DecorView tree is ordinary ViewNodes; window
  chrome (dim + panel + content) is painted into the SAME framebuffer before
  the fb→framebuffer copy (stacked windows composite in show order with
  per-window dim).
- **input** — item rows/buttons are clickable ViewNodes carrying
  `(dialog_owner_obj, dialog_which)`; `dispatch_click` routes them as
  `DialogInterface$OnClickListener.onClick(DialogInterface dialog, int which)`.
  No-listener buttons still dismiss.

## §6 multi-frame proof — gmdice (real clicks only)

All evidence from `--click-test` (frame-1 restore → real dispatch → re-render
via the SAME stage_render_frame pipeline → honest pixel diff):

| Step | Interaction | Result |
|------|-------------|--------|
| FRAME_0 | launch | main screen (158,040 px content) |
| click "…" (real listener dispatch) | app builds ArrayAdapter + AlertDialog.Builder → show | **dialog visible**, 1,737,264 px diff, click_frame_0.png |
| click item which=2 (DialogInterface routing) | app callback runs, opens SECOND dialog | stacked compositing pixel-verified (two windows, inner white panel at computed geometry), 1,868,540 px diff, click_frame_3.png; dice display mutates to "1 1 1" |
| per-view report | 4/4 probed views | changed_px>0, state_changed=true |

Second-interaction criterion (§7): dialog visible → item click → app state
mutation + second dialog → second visible framebuffer change. MET by gmdice.
No direct callback invocation, no forced state, no synthetic screenshots —
the full chain is `[UI-EVENT] → RECURSIVE INVOKE (app bytecode) →
[DIALOG] show() → [DIALOG-RENDER] → EXP092-COPY → PNG`.

## §7 criterion status

- ≥3 APKs with real interaction → visible dialog/menu: **1 proven end-to-end
  (gmdice)**; unote (64-view list UI) has dialog code paths now reachable and
  is the first validation target for the next session.
- ≥2 apps with dialog → second interaction → dismiss/state change → second
  visible change: **1 (gmdice)**.

Honest shortfall: the §7 target of 3/2 apps was not reached within the
campaign budget; the architecture is general and the remaining work is
per-APK validation, not new machinery.

## §20 Window/Surface architecture assessment

One window abstraction now serves Activity content + Dialog windows + Toast;
the framebuffer is the single compositing surface. SurfaceView/GLSurfaceView
(OB-3) remain outside it — the GLES stage plan should introduce a Surface
abstraction that the renderer composites like dialog windows today (z-ordered
surfaces in one framebuffer), reusing the window-compositing pattern landed
here.
