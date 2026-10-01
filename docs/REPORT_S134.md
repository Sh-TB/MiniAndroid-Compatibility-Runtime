# S134 — FINAL RUNTIME ROOT-CAUSE CAMPAIGN (white/black/grey/blank/stale)

## A. EXECUTIVE RESULT

```
S134 STATUS: VERIFIED (one P0 root root-caused, fixed, regression-clean, 3-run)
```

- **The central §3 hypothesis was PROVEN on current HEAD** — two logical state
  slots aliased one physical slot: MiniAndroid's DEX heap keyed instance fields
  by **bare field name**, so any two classes in one object's hierarchy sharing
  a field name shared one storage slot. This is exactly the "multiple writers,
  one state" divergence class the campaign mandates hunting.
- **F-NEW-160 (P0) ROOT-CAUSED-FIXED**: DEX instance-field identity law
  (declaring-class-qualified keys + ART declarer resolution + honest field
  defaults). First divergence fixed for the solitaire_71 face of F-NEW-156.
- **In-wave regression caught and fixed**: the first cut of the law split
  `StopWatch.options`/`ShowTime.options` (one logical field, two DEX ref
  classes); the FAST suite caught simplestopwatch going blank; the ART
  declarer-resolution walk fixed it and preserved the solitaire fix.
- **Zero regressions vs HEAD (A/B-proven)**: rebuilt fbc0291 in a scratch
  worktree — dooz `ba8a95eb2278594f` and ballbreak `8a951f5f975c4742` are
  BYTE-IDENTICAL between HEAD and the fixed tree; laws130 51/51; webfix T02
  golden `c95affdefb734ffd` ×3.
- The reported S133 stale-gate values in `scripts/s112_gates.py` (`want` SHAs)
  are S112-era and now formally SUPERSEDED by the A/B method (current-HEAD A/B
  is the honest regression oracle; static golden SHAs rot as the runtime
  legitimately advances).

## B. CAMPAIGN START STATE (reconciliation)

```
CURRENT HEAD:  fbc0291494215ce13f454a5d8b9b7eef8c2a2c7b   (verified)
BRANCH:        main
ORIGIN MAIN:   none — local-only repo (ls-remote fails honestly)
WORKTREE:      tmp/flappycow (pre-existing) + S134 source changes
BUILD:         miniandroid/build/ was WIPED (workspace reset) — rebuilt from
               source this session before any claim
CONTROL-PLANE: master_worklist 673 items consistent with registry 454→457
               roots; s112_gates.py wants = STALE (S112 era); F-NEW-156
               OBSERVED-FAIL carried 4 faces whose current reality diverged
               (measured below)
```

## C. FAST-PATH FINGERPRINTS (§35, before/after the fix)

| target | before fix (HEAD) | after fix (final binary) |
|---|---|---|
| solitaire_71 | rc=1, TRUE_EMPTY (2 colors, 98.87%), 9 SYNTH-EXC, first = `h.<init> pc=11 Window.getCallback on null` | frontier moved: delegate constructs, AppCompat theme machinery runs, app reaches onStart; new first divergence = support-v7 WindowCallbackWrapper IAE family; 3-run `6588621c4a0c4182` |
| headingcalc_1 | rc=0, NONBLANK 483 colors | unchanged rc=0, 483 colors (C013 overpaint → F-NEW-162) |
| chessclock_29 | rc=1, `Uri.toString on null` at setUpGame pc=321 | unchanged (→ F-NEW-161, producer unattributed) |
| simplestopwatch_26 | rc=0, STATE_NONBLANK 16 colors, 0 errors | rc=0, 0 errors, 18 colors, 3-run `e00fe7e082c385f8` ×3 (isolated `--data-root`) — mid-wave regression caught & fixed |
| boxcars_libgdx | rc=0 **SUCCESS Errors=0** but frame = C013 placeholder (3 colors 99.81%) | unchanged (§30 gate violation → F-NEW-162) |

## D. FIRST DIVERGENCE (the campaign deliverable)

```
STAGE          DEX execution — iget-object in support/v7/app/e;.i (getDelegate)
EXPECTED       field e.m (AppCompatDelegate) reads its own default: null
               (delegate not yet created) → creation branch runs
ACTUAL         read answered the app Handler b/b#30 stored by classes.c <init>
               under the SAME bare name "m" (name-aliased heap slot)
FIRST DIVERGENCE  heap get_object_field(oid, "m") — name-keyed storage
CALLER         Landroid/support/v7/app/e;.i pc=0 (iget-object e.m)
DOWNSTREAM     e.onCreate invoked delegate family on a HANDLER →
               g.a(Activity,f) received a Handler as Activity →
               activity.getWindow() answered null (Handler has no window) →
               support/v7/app/h.<init> pc=11 NPE → APP-BOUNDARY unwind →
               blank two-color screen (2 colors, 98.87% white)
PROOF          [S134-QGET] key=m obj#16 hit=Y val=b/b#30 (pre-fix binary);
               DEX dumps: b.b.<init> = Handler subclass ctor; e.i returns
               #30 at pc 0xc; sol_v6.log FIELD-TRACE put/get pair
```

## E. THE FIX (semantic law, no name heuristics)

1. **Qualified identity**: DEX instance fields key as `Ldeclaring;->name`
   when the declaring class is DEX-defined (app, support lib, androidx —
   package prefix is NOT a criterion; the support library lives under
   `Landroid/*` and still collides). Framework-owned classes (no DEX body)
   keep bare keys — C++ shadow interop unchanged.
2. **ART declarer resolution**: a field ref `(C, name)` resolves through the
   superclass chain to the class that actually DECLARES the field
   (`resolved_field_declarer`); the ref class is only the starting point.
   simplestopwatch wrote `ShowTime.options` and read `StopWatch.options` —
   one logical field, two ref classes.
3. **Honest defaults**: a never-written field reads its declared DEFAULT
   (zero/null) — never another class's slot.
4. **R-NEW-414 initializer scan restricted** to the field's declaring class
   with initializer-type == field-type matching (it previously matched by
   name across the whole ancestor chain and materialized `classes.c`'s
   `new b.b()` Handler for the unrelated `e.m`).
5. **Dual-write**: DEX iput writes the qualified key + bare legacy mirror
   (C++ bare-name readers stay fed).

New code ≈ 90 LOC in `dex/dalvik_engine.cpp` + 1 const member in the header.
No new dependencies. Env-gated probes kept as permanent instrumentation:
`MINIANDROID_S134_QGET`, `MINIANDROID_S134_WINDOW_TRACE`.

## F. ANSWERS TO §45 (mandatory questions)

- WHY did the APK fail? The AppCompat delegate was never created — a Handler
  object answered as the delegate because two fields shared one slot.
- WHERE first divergence? `get_object_field(oid, "m")` in `e.i` (getDelegate).
- WHEN? First `iget-object e.m` of the run, inside `super.onCreate` dispatch.
- WHO created the bad state? `classes/c;.<init>` iput of `m = new b.b()`
  (a legal write) into a slot that ALSO belonged to `e.m`.
- WHO overwrote the valid pixels? No pixel writer — the UI tree was never
  built; the blank frame is honest absence of content.
- WHICH subsystem owned the wrong value? The DEX heap field map (name-keyed).
- WHICH upstream law? ART field resolution (hierarchy walk to the declaring
  field); JLS field shadowing semantics; `Activity.attach()` window law for
  the downstream getWindow/getCallback chain.
- WHY did MiniAndroid diverge? The heap simplified fields to bare names;
  obfuscated builds (ProGuard single-letter names) collide massively.
- WHY did the screenshot hide the true state? It didn't — the white frame WAS
  the honest symptom; the trace turned it into a causal chain.
- WHAT is the minimal generic fix? Qualified field identity + declarer
  resolution + honest defaults (≈90 LOC, no refactor of heap storage).
- WHAT applications share the root? Every APK whose hierarchy reuses field
  names across classes — all obfuscated builds; measured fan-out: solitaire
  fixed, simplestopwatch/headingcalc/chessclock/boxcars unchanged-behavior
  (their remaining roots are F-NEW-161/162).
- WHAT regressions were checked? laws130 51/51; dooz/ballbreak A/B
  byte-identical vs HEAD; webfix T01–T14 + T02 ×3; FAST suite before/after.
- WHAT remains genuinely unresolved? F-NEW-161 (chessclock Uri producer),
  F-NEW-162 (C013 placeholder law), solitaire's downstream support-v7 chain
  (WindowCallbackWrapper IAE / SharedPreferences null / FragmentManager
  "No activity" at onStart), F-NEW-157 libGDX GL chain, R-NEW-456 z.ai
  Svelte-5 replay bisect.

## G. FAILURE TAXONOMY (§32 classification)

```
solitaire_71   : UI_NOT_CREATED → (fixed) → now LIFECYCLE frontier (onStart)
simplestopwatch: STATE_NONBLANK (rendered, placeholder-contaminated)
headingcalc_1  : STATE_NONBLANK (rendered, placeholder-overpaint)
chessclock_29  : EXECUTION_STALL/NPE_BOUNDARY (F-NEW-161)
boxcars        : NATIVE/JNI_FAILURE masked by DIAGNOSTIC writer (F-NEW-162)
```

## H. EVIDENCE

| artifact | path |
|---|---|
| FAST fingerprints (before/after) | run/s134/fast/ + FAST_RESULTS.json |
| qualified-key probes | run/s134/sol_v8.log, sol_v12.log ([S134-QGET]) |
| getCallback proof | run/s134/sol_v13.log ([S134-GCB], AppCompat theme chain) |
| DEX dumps | scripts/dex_method_dump.py outputs (b.b.<init>, e.i, e.onCreate, g.a) |
| 3-run solitaire | /tmp/s134_sol3_*.png → 6588621c4a0c4182 ×3 |
| 3-run simplestopwatch | /tmp/s134_ssd_*/ → e00fe7e082c385f8 ×3 (isolated data roots) |
| HEAD A/B worktree | /tmp/s134_head (fbc0291 rebuild; dooz/ballbreak byte-identical) |
| webfix suite rerun | run/s133/fixsuite/ (T02 c95affdefb734ffd preserved ×3) |
| registration | scripts/s134/s134_register_roots.py |
| runtime binary | miniandroid/build/miniandroid (sha16 cccbc461c62f2961) |

## I. STATUS VOCABULARY USED

```
F-NEW-160  ROOT-CAUSED-FIXED (P0)  — law + fix + fixture faces + gates + 3-run
F-NEW-156  PARTIAL (P0)            — solitaire face fixed; downstream faces open
F-NEW-161  OBSERVED-FAIL (P1)      — chessclock, producer unattributed
F-NEW-162  OBSERVED-FAIL (P1)      — C013 placeholder contamination / false SUCCESS
F-NEW-157  OBSERVED-FAIL (P0)      — annotated with boxcars measurement
```

## J. NEXT HIGHEST-LEVERAGE ROOTS

1. **F-NEW-162 (P1)**: C013 placeholder law — route custom views extending
   known bases to base draw semantics (§16); forbid placeholder SUCCESS for
   SurfaceView/GL families (§30 gate). Fan-out: every corpus title with
   unknown custom views (headingcalc, simplestopwatch, boxcars visible today).
2. **Solitaire downstream chain** (P1): WindowCallbackWrapper IAE →
   SharedPreferences shadow gap (`c/m.aR`) → FragmentManager "No activity" —
   each is a named, traceable API family.
3. **F-NEW-161** (P1): chessclock Uri producer attribution (needs a
   multidex-safe disassembler pass or an engine arg-trace at pc=321).
4. **R-NEW-456** (P2): z.ai Svelte-5 replay bisect (S133 queue).

## K. LAWS READ / NEW LAWS DISCOVERED

```
LAWS READ: CONSTITUTION_V2, worklog S82–S133, root registry (454), master
worklist (673), reuse registry, S133 report + battery/gates layout, S134
directive (48 sections).
NEW LAWS DISCOVERED AND REGISTERED:
  N-134-1  DEX instance field identity = (resolved declaring class, name,
           type); name-only keying aliases slots across the hierarchy.
  N-134-2  A field ref's class_idx is the RESOLUTION START, not the owner;
           the declarer is found by the superclass walk (ART ResolveField).
  N-134-3  A never-written instance field answers its declared DEFAULT,
           never another field's storage.
  N-134-4  Initializer materialization (R-NEW-414) is owned by the field's
           declaring class; name-matching across ancestors fabricates state.
  N-134-5  Determinism law (measured): identical runs require isolated
           --data-root; a shared root feeds run N's prefs into run N+1.
```

## L. WAVE 2 — F-NEW-162 C013 PLACEHOLDER LAW (same session)

```
STATUS: PARTIAL (contamination eliminated; SUCCESS-gate downgrade open)
```

- **Surface-family suppression**: SurfaceView/GLSurfaceView-descendant custom
  views never receive the diagnostic placeholder. boxcars (EbitenSurfaceView)
  frame went from placeholder-contaminated (3 colors) to an honest single-
  color frame — the diagnostic writer no longer stands in for an unrendered
  surface.
- **Text-base routing**: custom views descending from TextView/Button/EditText/
  CheckBox/RadioButton/Switch route to text semantics — text draws when
  present; empty text is an honest blank (§19: an empty view stays empty
  unless its own semantics draw). headingcalc's ExplainableTextView headings
  (TC/WD/TH/TAS/WS) now render REAL labels; the pink "custom view (not
  rendered)" boxes are gone; unique colors 483 → 823.
- **Descriptor normalization law**: the view-tree class_desc may be DOTTED
  (Lorg.debian...) while the DEX hierarchy index is SLASHED — the semantic
  base is invisible without normalization (measured: routing silently no-op'd
  until normalized).
- **Regression on the final binary**: laws130 51/51; dooz `ba8a95eb2278594f` +
  ballbreak `8a951f5f975c4742` byte-identical to HEAD; T02 `c95affdefb734ffd` ×3.
- **Remaining frontier**: §30 SUCCESS-gate downgrade for surface-family-only
  frames (boxcars still reports SUCCESS with an unrendered native surface) and
  routed-text geometry refinement (label/value overlap).

