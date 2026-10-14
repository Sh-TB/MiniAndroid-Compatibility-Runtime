# CONT-52 RESULT — the invoke-super BOUNDARY law (F-NEW-324)

Binary: `b5998a50a679c2e3` (HEAD `67c537b0` = the CONT-51 push + one generic
law). No APK-specific hacks, no fake objects. Probe FIRST (PRE faces captured
before the engine edit, deterministic ×3).

## Phase 0 — reconciliation

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | HEAD == origin/main == `67c537b0` (the CONT-51 push, verified); build reproducibility: the CONT-51 close rebuilt byte-exact `d19d5ba63c47a19f` before its fixes | git rev-parse; sha256sum |
| TESTED | CONT-51's post-fix face held on entry: GameSelector.onResume dispatches via DEX (ok=1, 22361 insns), 0 uncaught, NavigationMenuView measures with real specs | run/cont51/sol_post2/r1..r3 |

## Phase 1 — the decode: NavigationView.onMeasure "FAILED(no write-back)"

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED (static) | `NavigationView.onMeasure(I,I)` is REAL DEX: a MeasureSpec sparse-switch over the width mode, then `invoke-super f.onMeasure(v4, v5)` where `f` = ScrimInsetsFrameLayout (DEX) — and `f` defines NO onMeasure (the class walk lists none); `f`'s super is the FrameLayout boundary | scripts/cont46_disasm.py |
| TESTED (runtime) | `[DEX-MEASURE] NavigationView.onMeasure spec_w=… FAILED(no write-back)` on EVERY pass (3x/run in CONT-51 runs) — dex_measure_valid never set; ZERO `setMeasuredDimension` rows for any design.* receiver; the NavigationView (298) / NavigationMenuView (322) nodes absent from the EXP092-RENDER tree | run/cont51/sol_post2/r1.err |
| TESTED (engine) | execute_invoke_super's bridge arm passed `declaring_class` (R-NEW-345 law) = `Landroid/support/design/internal/f;` — the DEX intermediate; the FrameLayout.onMeasure bridge's class whitelist matches only framework names → silent miss; try_recursive_invoke(f, "onMeasure") correctly returns false (no DEX body) and the bridge is the ONLY remaining path | dalvik_engine.cpp:21311; android_shadows.cpp:5857 |

## Phase 2 — probe FIRST (fixtures/fnew324_probe, APK `4f06d7f711067013`)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | the EXACT NavigationView inheritance shape: `Leaf extends Mid [DEX, no onMeasure] extends FrameLayout`; Leaf.onMeasure does `super.onMeasure(w,h)`; the control shape `Direct extends LinearLayout` (declaring class IS the framework class — the R-NEW-345 case) | fixtures/fnew324_probe |
| TESTED | PRE ×3 deterministic: **`[DEX-MEASURE] Leaf.onMeasure FAILED(no write-back)`** and the Leaf FrameLayout bridge executed **0 times** (S109-VG-MEASURE rows: only Direct's LinearLayout bridge fired). Honest note: the P1 VALUE face (measured=100x60) PASSES in PRE — the View.measure fallback masks the missing super chain; the bridge-log face is the judgment surface, pinned here as the PRE/POST criterion | run/cont52/f324_pre/r1..r3 |

## Phase 3 — the fix (minimal, generic, ART-faithful)

| Law | Change | Scope guard |
|-----|--------|-------------|
| F-NEW-324 | in execute_invoke_super's bridge arm: when `declaring_class` is DEX-defined, walk `superclass_of` up to the FIRST non-DEX ancestor and pass THAT boundary class to bridge_to_api; framework declaring classes are untouched (the R-NEW-345 case — probe P2 pins it). ART law: super resolution continues past a DEX intermediate that does not define the method, onto the first framework ancestor | dalvik_engine.cpp:21312..21340; one call site |

## Phase 4 — POST verification (final binary `b5998a50a679c2e3`)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | fnew324 probe POST ×3: **`[S109-VG-MEASURE] FrameLayout obj#13 spec=100x60 children_measured=1`** — the FrameLayout measure law now executes FOR the leaf THROUGH the DEX intermediate; the FAILED(no write-back) face is gone; rows 3/0 ×3 deterministic (`5e89f5db`) | run/cont52/f324_post/r1..r3 |
| TESTED | solitaire ×3: the FrameLayout bridge now executes FOR the NavigationView receiver (`[S109-VG-MEASURE] FrameLayout obj#298 children_measured=1`, both spec faces); 0 uncaught; GameSelector.onResume still dispatches (ok=1) | run/cont52/sol/r1..r3 |
| TESTED | zero-drift regression gate on the final binary: **33/33 REG rows MATCH** (11 canonical anchors ×3 byte-identical — dooz `31ddd4d5b8e6d18e`, micro, unote, gmdice, opencalc, tttdeluxe, flappycow, g2048, tanana `5f7e0114c3bfd6b5`, csw `3442d9a9dc0fa0f9`, simplecalc `e847ca0346708f07`); probe battery == records exactly (the two known non-zero faces f259g 84/7 and fnew302 48/24 unchanged); **support group BMI `b52252c2de19b03a` / alex `c8d69f811b23f245` / notes `eb5ebd559cad1028` MATCH ×2** | run/cont52/gate_cont37.log; run/cont52/gate_*_r* |

## Honest bounds + next frontier

F-NEW-324 makes the super chain REAL for every DEX-intermediate shape (the
NavigationView/f family is one instance; the law is class-agnostic). The
solitaire frame verdict is UNCHANGED (DEFAULT_BACKGROUND_ONLY /
first_missing_stage=APP_PIXELS) — with the bridge now firing, the NEXT first
divergence surfaced one layer up: the measure chain hands NavigationView
spec `0x0/0x0` at the R347-MEASURE face (`view=298 wspec=0x0 hspec=0x0`,
dex_onmeasure=YES) — the DrawerLayout child-spec computation (the
NavigationView LayoutParams width/height as seen by the DEX measure chain)
is the recorded next decode (F-NEW-309 row refreshed). No fix was made for
that face this wave — no fix without its own decode cycle.

**Registry 634→635** (F-NEW-324 appended ROOT-CAUSED-FIXED; F-NEW-309
next_wave refreshed). Evidence: `evidence/cont52/CONT52_RESULT.md`.
