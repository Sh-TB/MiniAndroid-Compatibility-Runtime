# GRAPHICS ROOT CAUSES (canonical) — S82-GFX-REVOLUTION

Law: FIRST DIVERGENCE ONLY — no root cause may be claimed without an
evidence-bit that went 0 (§6). Fix law: ONE ROOT CAUSE → ONE PATCH →
ONE REGRESSION → FANOUT.

## F-NEW-158 — PROGRAMMATIC-BACKGROUND-DROP  [ROOT_CAUSED_FIXED]

- **Symptom**: programmatic UIs render with default/white faces; XML
  `setBackgroundResource(R.drawable.x)` backgrounds never appear.
- **First divergence**: DRAW_CALLED=0 at background paint stage. Two
  concrete defects:
  1. `setBackground(Drawable)`/`setBackgroundDrawable(Drawable)` fell into
     the generic handled-void list — the ColorDrawable color was never
     captured.
  2. `setBackgroundResource(resid)` stored into `image_resource_id`
     (ImageView-src field) — never consulted by the background paint path
     (and clobbered an ImageView's earlier src resid).
- **Evidence**: fixture ladder l0_solid (dark ColorDrawable bg absent:
  2987 nonwhite/white-dominant) + l4_xmldrawables (shape/gradient/layer/
  selector all absent).
- **Fix**: engine-side capture (dalvik_engine) → `ViewNode.bg_resource_id`
  + ColorDrawable obj→color map; render-side resolution (ARSC select_file)
  flows into the SAME paint laws as XML backgrounds (state-list pick,
  F-053 shape, bitmap fit-draw).
- **Regression**: foundation battery 26/26 rc=0; pixel goldens 24/24 exact
  (VERIFICATION.json nonwhite); ladder 6/7 PASS after fix.
- **Fanout**: see GRAPHICS_FIX_FANOUT.md.

## F-NEW-159 — NULL-FRAMEWORK-RECEIVER NPE  [OPEN]

- **Symptom**: onCreate unwinds at APP BOUNDARY → blank/crash status.
- **Exact traces** (fanout probe re-runs, `run/s82gfx/fanout/*.log`):
  - TimeLimit MAND-002: `Lj/u;.b` → `LocaleList.toLanguageTags` on null;
    `WindowInsetsController.setSystemBarsAppearance` on null.
  - APP-001 family: same cluster.
- **Family**: sub-cluster of F-NEW-156 (onCreate APP-BOUNDARY-UNWIND, 35
  titles). Graphics fixes CANNOT reach these titles until lifecycle
  completes — execution order law (§25): F-NEW-156/159 first for them.
- **Next**: shadow the two receiver objects per AOSP semantics
  (LocaleList via Configuration; WindowInsetsController via Window),
  then regression the 35-title fanout.

## F-NEW-157 — libGDX GLSurfaceView NPE / EGL frontier  [OPEN]

- P9 hard-gate discovery (S82). Ladder l6_glsurface (plain GLSurfaceView,
  no libGDX) reproduces the family at HEAD: run "succeeds", 0 API calls,
  white screenshot (nonwhite=0, unique=1). The surface chain
  (Surface created → EGL context → swapBuffers → composition) is absent.
- Reference architectures (§14/§15): Anbox/emugl guest→host GL
  translation; SwiftShader CPU implementation law. MiniAndroid needs ONE
  deterministic software path first; software/GL backends stay separate.

## NON-ROOT-CAUSES (proven healthy — do NOT re-accuse)

- PNG decoder: color types 0/2/3/4/6 + tRNS all decode AND render
  (fixture l2, 1103 unique colors on screen).
- Density/resource selection: ARSC config picks xxhdpi-v4 correctly,
  density scale applied (fixture l3).
- ImageView resid chain: resid → select_file → decode → FIT_CENTER draw
  (fixtures l1/l2: quadrant pixels land exactly).
- Canvas clip + stroke: save/clipRect/restore honored exactly (l5 —
  initial "failure" was a fixture-authoring clip bug, i.e. the runtime
  was MORE correct than the test).
