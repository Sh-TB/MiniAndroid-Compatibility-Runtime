# GLES_REPORT_013 (§13/§14/§15)

## What this campaign delivered for graphics apps

**LIBGDX milestone reached (canvas backend).** bouncy (libGDX pinball,
SHA `ffda0d9c…`):

- BEFORE (v0.11.3 baseline): ACTIVITY_FAILED — synthetic fallback screen; the
  app never inflated because its resources use AGP obfuscated names
  (FIX-013-04 root cause).
- AFTER: 280 view nodes inflated, full-screen render, and with FIX-013-05 the
  app's REAL `ScoreView.onDraw(Canvas)` bytecode executes and its draw
  primitives replay into the framebuffer ("Select table" idle content is
  app-driven pixels — `bouncy-frame1.png`, `bouncy-click-frame.png`).
  bouncy additionally classifies REAL_INTERACTION (clicks produce visible
  second frames via the standard click probe).

Milestone mapping (§15): **LIBGDX_STAGE_1 (renderer callback) reached for the
canvas backend** — app draw callbacks execute against a real Canvas; GL
stages below remain open.

## GLES stage status (GL backend)

Stage plan unchanged and still fully open (honest status):

| Stage | Goal | Status |
|-------|------|--------|
| 1 | EGL/context lifecycle + glClear + renderer callbacks (onSurfaceCreated/Changed/DrawFrame) | NOT STARTED — no EGL surface model yet |
| 2 | shader/program | open |
| 3 | buffers/textures | open |
| 4 | real libGDX GL frame | open |
| 5 | interactive GL game frame | open |

Evidence gathered this campaign that shapes Stage 1:

- tictactoeemmanuelmess: `setContentView(View obj#6)` receives the libGDX
  game surface view — the VIEW OBJECT EXISTS and flows through the real
  dispatch chain; it is not yet a ViewShadow node, and no EGL context backs
  it. The first concrete Stage-1 primitive is therefore: **GLSurfaceView/
  SurfaceView shadow nodes + EGL context lifecycle stubs + renderer callback
  dispatch**, not "make one game work".
- bouncy proves the alternate backend (canvas) end-to-end, which de-risks
  everything around the GL surface (view creation, lifecycle, input, frame
  capture) — only the GL translation layer itself remains.

## §14 architecture decision input

Software-GLES emulation vs host-GL translation: the campaign produced a
third, evidence-backed data point — the **canvas replay backend** (record
app draw calls, rasterize in software) works without any GL at all for
canvas-mode libGDX apps. Recommended Stage-1 route: the same record/replay
pattern applied to GLES (record glClear/glViewport/draw-arrays calls on a
software rasterizer) before considering host-GL translation; it preserves
determinism (§15/§16) and the framebuffer-based evidence model.
