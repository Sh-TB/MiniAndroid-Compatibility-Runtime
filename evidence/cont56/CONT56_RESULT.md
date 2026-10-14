# CONT-56 RESULT — the framework LinearLayout.onMeasure SUPER law (F-NEW-328)

Binary: `11e5fa2c3b4b5037` (rebuilt at HEAD; the session container's
toolchain produces a byte-different but semantically identical build of the
CONT-55 source — decided by the 45/45 gate, not the SHA). No APK-specific
hacks, no R8-name special-casing, no fake objects. Probe A/B + solitaire
runtime proof chain; zero-drift gate green (15 anchors x3 + probe battery).

## Phase 0 — the session reconciliation + the standing user question

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | local container was the CONT-10-era snapshot `e99c2fbd` AGAIN; fetched + ff to `origin/main == 5c9d72e8` (the CONT-55 closeout, 97 commits) | git rev-parse |
| TESTED | rebuilt binary `1f81036989a12a7d`; runtime SOURCE byte-identical to the binary-producing tree (`git diff 678ff67b..HEAD -- miniandroid/` EMPTY) — the SHA delta is container toolchain noise; semantic identity decided by the gate | git diff |
| TESTED | **FRESH app measurements at HEAD x3, ALL byte-exact**: opencalc `a976d2f9` / simplecalc `e847ca03` (rc=0) / tanana `5f7e0114` / BMI `b52252c2` (rc=0) / alex `c8d69f81` / dooz-15s `31ddd4d5`; dooz FULL budget `6841d52a` x2 — the honest measured answer to the standing "did Dooz and the calculators progress" question: simplecalc is a COMPLETE visible calculator (display + all 5 button rows), BMI renders its real form, opencalc's pad is visible-but-left-compressed, dooz renders its real Scaffold at a fair budget | run/cont56/*; evidence/cont56/CONT56_APP_MOSAIC.png |
| TESTED | zero-drift on the rebuilt binary: 15 canonical anchors x3 = 45/45 MATCH | run/cont56/gate_*, g2_* |

## Phase 1 — the decode: why the drawer was unreachable BY INPUT

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | the CONT-55 recorded frontier (the menu-content draw pipeline) is gated BY INPUT: the open-drawer flow needs the hamburger tap; the tap hit-test answered `target=189` (the DrawerLayout) for EVERY toolbar coordinate — the hamburger was never hittable | run/cont56/sol_tap_*/run.log [F117-TAP] rows |
| TESTED (view tree) | the Toolbar measured **0 wide** (0x126); its nav ImageButton (oid=423, click=True) 0x126 — a 0-width hit target; AppBarLayout 1080x1920 (should wrap ~126); NavigationView stacked at y=3840 | run/cont56/sol_vtree/view_tree.json |
| TESTED (R347 rows) | the appbar's incoming spec `0x40000438 x 0x40000780` (EXACTLY 1080 x EXACTLY 1920) — the real DrawerLayout DEX ran; the appbar's answer 1080x1920 = the raw getDefaultSize face | run/cont56/sol_vtree/run.log |
| TESTED (probe-first) | **fnew328 PRE x1 on `1f81036989a12a7d`: P1/P2/P3 FAIL** — a DEX LinearLayout subclass whose onMeasure calls super reads `self=1080x1920 child=1080x1920` (want 1080x48/100x50): the super pass produced NO child measure and NO wrap self | run/cont56/f328_pre/run.log |
| TESTED (dead-end proved) | a ViewShadow-level onMeasure wall law was attempted FIRST: `[F-NEW-328]` fired ZERO times — the bridge's S109 ROOT-042 law claims LinearLayout onMeasure BEFORE any shadow dispatch. The wall was REVERTED; the fix moved to the actual dispatch site (the dead-end proof recorded) | src/framework/android_shadows.cpp F-NEW-328 NOTE |

## Phase 2 — the fix (minimal, generic, AOSP-faithful; two stacked gaps)

| Law | Change | Scope guard |
|-----|--------|-------------|
| F-NEW-328a (LP-SOURCE) | the child-spec source is the child's **LayoutParams**: `child_dim_of = lp_* authoritative (non-INT_MIN), legacy width/height mirrors fallback` — applied at BOTH S109 copies (the bridge S109-VG onMeasure site + the R347 measure-wrapper ROOT-045 recursion) | dalvik_engine.cpp |
| F-NEW-328b (SELF-SIZE) | the container self answer per AOSP LinearLayout: orientation from the EXP-095 node field (0/-1 = HORIZONTAL, 1 = VERTICAL); vertical → want_h = Σ(child+margins)+padding, want_w = max+padding; horizontal → mirrored; **EXACTLY → spec; AT_MOST → min(want, specSize); UNSPECIFIED → want** — LinearLayout receivers only (the other families keep their legacy self answer; their own decode cycles own any change) | dalvik_engine.cpp (S109-VG self block) |

## Phase 3 — probe A/B (fixtures/fnew328_probe, real aapt2/ECJ/D8)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | `fnew328_probe.apk 1cd25382d8a29a35` — MyBar (vertical DEX subclass, match x wrap, one match x 48px child) + MyRow (horizontal, one 100x50 child); each onMeasure calls super then REPORTS self+child measured — the exact AppBarLayout read-back shape | fixtures/fnew328_probe/ |
| TESTED | **PRE x1 on `1f81036989a12a7d`: 1/3** (P1 self=1080x1920 child=1080x1920 FAIL; P2 FAIL; P3 FAIL) | run/cont56/f328_pre |
| TESTED | **POST x3 on `11e5fa2c3b4b5037`: 4/0 x3** — P1 self=1080x48 child=1080x48; P2 self=100x50 child=100x50; P3 EXACTLY keeps 1080x1920 with childH=48; N1 sanity PASS | run/cont56/f328_post2_r1..r3 |

## Phase 4 — runtime verification (solitaire, binary `11e5fa2c3b4b5037`)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | **AppBarLayout 1080x105 (was 1080x1920)** — the appbar's DEX reshape now reads real child values through the super pass; NavigationView/NavigationMenuView y=2025 (was y=3840) | run/cont56/sol_f328_vt/view_tree.json |
| TESTED (honest) | the VISIBLE frame UNCHANGED `ba50a4d28ea62fe7` — the closed drawer's pixels sit off-screen; the Toolbar's OWN DEX onMeasure still answers 0 wide (the support Toolbar DEX body divergence = the recorded NEXT decode), then the DrawerLayout child-edge layout law | run/cont56/sol_f328/screenshot.png |

## Phase 5 — zero-drift regression gate (binary `11e5fa2c3b4b5037`)

| STATUS | RESULT | EVIDENCE |
|--------|--------|----------|
| TESTED | **15 canonical anchors/controls x3 byte-identical — 45/45 MATCH**: dooz `31ddd4d5` / micro `da73010a` / unote `4f1a9e4e` / gmdice `f3b483fe` / opencalc `a976d2f9` / ttt `af609429` / flappy `13cf4746` / g2048 `59ca1526` / tanana `5f7e0114` / csw `3442d9a9` / simplecalc `e847ca03` + BMI `b52252c2` / alex `c8d69f81` / notes `eb5ebd55` / sol `ba50a4d2` | run/cont56/g2_* |
| TESTED | probe battery == records: fnew326 13/0, fnew326b 13/0, fnew327 3/0 + fnew328 4/0 x3 (the new law's own probe) | run/cont56/probe_* |

## Honest bounds + next frontier

The LinearLayout super pass is now AOSP-faithful (probe-proven end to end:
wrap sums, EXACTLY precedence, lp-aware child specs). The solitaire appbar
gained its real reshape (1920 → 105) and the drawer chain moved one layer
up — but the visible frame is unchanged because the remaining legs are:
(1) the **Toolbar's own DEX onMeasure 0-wide face** (the support Toolbar
body's child-measure/spec-mode arithmetic — the next decode), and (2) the
**DrawerLayout child-edge layout law** (drawers pinned to the edge at full
height, not sequential stacking). No fix was attempted for those faces this
wave — no fix without its own decode cycle.

**Registry 638->639** (F-NEW-328 appended ROOT-CAUSED-FIXED). Evidence:
`evidence/cont56/CONT56_RESULT.md`.
