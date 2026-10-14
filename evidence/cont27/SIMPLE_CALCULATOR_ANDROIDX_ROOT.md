# CONT-27 / TRACK B — SIMPLE CALCULATOR: FIRST FULL SUCCESS

Wave: CONT-27 (continuation of CONT-26's dual-track directive). Track B
resumes Simple Calculator at the divergence CONT-26 recorded as its next
target: `[V6-CTX-FALLBACK]` Toolbar ctor-context MISSING → measure-scratch
fields never initialized → `Toolbar.onMeasure pc=152` aput-null → APP
BOUNDARY → white screen.

**VERDICT UP FRONT:** Simple Calculator reaches its **first FULL SUCCESS
(rc=0)** at the canonical sweep protocol, deterministic ×3, with the engine's
own frame-truth gate (F-NEW-233) passing the frame as authoritative app
content and the rendered tree being the app's OWN layout (the real keypad).
One new generic P0 root (F-NEW-283 — DEX-existence constructor authority in
the inflate gate) was root-caused, fixed, and regression-proven. A pixel-level
CORRECTION to CONT-26's evidence description is recorded honestly (§4).

---

## 0. TRUTH LOCK (Phase 0)

| item | value |
|---|---|
| binary (pre-fix) | `1ff06737f7b12ad4` rebuilt byte-exact at HEAD da92a9f6 |
| Simple Calculator APK | F-Droid archive vc8, sha256 `68da25fd9fdf54b4...` (re-downloaded this wave; vc7/vc6 captured) |
| positive control | `fixtures/fnew253_probe` rebuilt via `scripts/w4_build_probes.sh` |

## 1. B1 — DUAL CONTROL AT THE PRE-FIX BINARY

**Positive control:** fnew253_probe → screenshot sha16 `7602563f52cce823`
(== recorded), **147 PASS / 0 FAIL** rows; re-run green at the final binary.

**Failing target:** Simple Calculator reproduces CONT-26's recorded state
exactly at binary `1ff06737f7b12ad4` / `2ae9591a7dd5e7ad`: rc=1, 2 uncaught
`aput-null` NPEs (`Toolbar.onMeasure pc=152`, `Toolbar.onLayout pc=44`),
`[V6-CTX-FALLBACK]` ctor-context MISSING, screenshot sha16 `7960bce447ac6d8f`.

## 2. B2 — FIRST-DIVERGENCE DECODE (the ctor-skip family)

MINIANDROID_METHOD_TRACE: **ZERO `Toolbar.<init>` METHOD-IN rows** while
Toolbar getters run (getWrapper/getTitle/getSubtitle/getNavigationIcon) — the
Toolbar object was constructed as a shadow-only view; its DEX constructor
never executed. DEX ground truth (`scripts/cont27_disasm.py`):
`Toolbar.<init>(Context, AttributeSet, int)` = 349 units and allocates the
measure-scratch `int[2]` at pc=0x0021 (`new-array [I` + `iput f@2571`). With
the ctor skipped, the scratch stays null → `onMeasure pc=152` aput-null.

**Root:** `LayoutInflater.is_app_class_descriptor` gate used a package-prefix
suppression list that includes **`Landroid/`** — blanket-blocking every
support-v7/androidx class (`Landroid/support/v7/widget/Toolbar;`) even though
the class IS in the APK DEX. The engine's own ADDITIONAL-AUDIT P1-3 note
already stated the AOSP authority for the com.google.android.* family: **"does
the class exist in the APK DEX" — NOT the package prefix.** The same law
applies to Landroid/: the prefix gate predates it and contradicts it.

## 3. B5 — THE GENERIC FIX (F-NEW-283) + RUNTIME PROOF

**Fix (layout_inflater.cpp only, zero app knowledge):** the inflate ctor gate
becomes `prefix rule OR dex_class_exists_hook_(class_desc)` — the probe hook
was already installed (execution_engine.cpp, the V4-TAG law) and its result
is cached thread_local per descriptor. Framework views (Landroid/view/View
etc., absent from app DEX) keep byte-identical behavior; support/androidx
classes bundled in an APK now execute their real constructors with the
F-NEW-197 XML-AttributeSet law intact.

**Post-fix Simple Calculator (binary `6823170ebd443118`, runs r2/r3/r4):**

| metric | pre-fix | post-fix |
|---|---|---|
| rc | 1 | **0** (main.cpp law: exit 0 ONLY on full SUCCESS) |
| Status | PARTIAL SUCCESS | **SUCCESS** |
| uncaught | 2 | **0** |
| aput-null | 2-3/run | **0** |
| Toolbar.onMeasure/onLayout | NPE at pc=152/44 | complete |
| screenshot sha16 | 7960bce447ac6d8f | 7960bce447ac6d8f (byte-identical ×3) |

**Rendered tree (name-level, [EXP092-RENDER]):** ActionBarOverlayLayout →
ContentFrameLayout → LinearLayout(7 children) → the calculator display
`TextView text="0"` (1080x429) and the real keypad Buttons with the app's own
texts — `mod`, `^`, `√`, `C` / `7`, `8`, `9`, `÷` / `4`, `5`, `6`, `*` /
`1`, `2`, `3`, `-` — at the correct 270x262 four-column grid. Pixel census
(full-PNG decode): 121 unique sampled colors — `6fa8dc` blue keypad (88,071
samples), `fafafa` background (41,412), `f68630` orange accent (882) — the
app's material palette. Skeleton-light is default OFF (branch-only
experiment, never merged) — excluded from the claim by construction; the
texts and positions come from the app's own XML and its own widget classes.

## 4. PIXEL-LEVEL CORRECTION TO CONT-26'S EVIDENCE (recorded honestly)

CONT-26's SIMPLE_CALCULATOR_ANDROIDX_ROOT.md described screenshot sha16
`7960bce447ac6d8f` as "white/blank". This wave's full-PNG decode of the SAME
byte-identical sha (produced both pre-fix and post-fix) shows the sha carries
the calculator's rendered content (121 colors, the keypad palette). The
CONT-26 description was therefore inaccurate about the pixels; its measured
facts (uncaught=2, rc=1, the NPE chain) were correct. The honest reading:
pre-fix the app's view tree already rendered (rc=1 because of the Toolbar NPE
process-death), and F-NEW-283's effect is **rc 1→0 with the NPE family
eliminated** — a determinism/completeness fix, not a pixel change.

## 5. B6 — CROSS-APP IMPACT

F-NEW-283 is a generic inflate law (grep-audited diff: no package names, no
app classes). The 8-target anchor suite ×3 at the patched binary is
byte-identical (24/24) — including dooz/opencalc, the other support/androidx
consumers — proving neutrality where the gate change was never reachable. The
positive control re-runs green at the same binary. Simple Calculator is the
first app whose layouts ship support-v7 view classes and thereby exercise the
fixed path.

## 6. STATUS LEDGER

| item | status |
|---|---|
| Positive control reproduced (147 PASS/0 FAIL) | TESTED |
| Simple Calculator pre-fix state reproduced | TESTED |
| F-NEW-283 root-caused + fixed + regression-proven | IMPLEMENTED+TESTED |
| Simple Calculator real render, full SUCCESS, 3 runs | **ACHIEVED** (rc=0 ×3, byte-identical) |
| Skeleton/合成/fallback excluded from the claim | OBSERVED (default OFF; texts from app XML) |
| Next frontier recorded | TESTED — button interaction (input-pump family) beyond the 5-frame sweep |
