# CONT-12 — F-NEW-514 decode + F-NEW-517 fix (the incomplete wave completed)

Wave: CONT-12 (resumed from the committed-but-unfinished state: scripts
`cont12_peri_disasm.py`/`cont12_try_table.py`/`cont12_run_one.sh` at commit
46182900, no decode executed). Date: 2026-10-23.
Base: origin/main b0620f75 (+46182900). Binary: rebuilt at the edited tree.
Target: F-NEW-514 (loading-census P0, issue #387) — the 16-title
Object.getClass umbrella cluster (peri row as decode target).

## 0. BASELINE (pre-fix, binary b0620f75 tree, run/cont12/peri)

| item | value |
|---|---|
| peri face | `b5a7a35d5fe0564b` (blank family), verdict DEFAULT_BACKGROUND_ONLY, first_missing_stage=APP_DRAW_OPS, ops=0 |
| uncaught | 1 — `NullPointerException "getConstructors(...) must not be null"` |
| stack | Intrinsics.checkNotNullExpressionValue ← SavedStateViewModelFactory_androidKt.findMatchingConstructor (caller_pc=48) ← SavedStateViewModelFactory.create ← HiltViewModelFactory.create ← ViewModelProvider$Factory.create ← R8-mangled ViewModel delegate ← MainComposeActivity.onCreate pc=239 |
| second path | same NPE inside the first composition: TagsKt.Folder (pc=701) → viewModel() → GapComposer.doCompose catch-all → "Error was captured in composition." (Recomposer.processCompositionError) → empty UI |
| decoy | `[M3-19-CYCLE] WindowInsetsCompat.toWindowInsetsCompat#10=0 re-entered (depth=46)` — present but NON-KILLING (error-path event, not the root) |

## 1. ROOT (generic, app-agnostic)

`java.lang.Class.getConstructors()` and `getDeclaredConstructors()` had NO
engine law. Every other Class-reflection accessor exists (getDeclaredMethods
F-NEW-190, getMethods R-NEW-464, getDeclaredConstructor/getConstructor F-106,
getInterfaces, getSuperclass) — the constructors enumeration was the one gap,
and the androidx ViewModel factory chain reads it under a Kotlin null-check
intrinsic, so the typed-null became a hard NPE in EVERY Hilt/ViewModel app
that creates a ViewModel during onCreate/composition. The census's
"Object.getClass umbrella" peri row is this single missing law.

## 2. FIX (dalvik_engine.cpp, after the getInterfaces law)

F-NEW-517 — OpenJDK Class.java law:
- `getDeclaredConstructors()`: ALL declared ctors, DEX table order, private
  included.
- `getConstructors()`: PUBLIC only (ACC_PUBLIC 0x1; constructors are never
  inherited — the class's own publics are the whole answer).
- Records carry the FULL Constructor contract the Constructor-side laws
  already consume: `class_desc` (FIX-M3-012b newInstance shim), 
  `__reflect_class` (F-029), `__reflect_name`="<init>", `__reflect_ret`="V",
  `__reflect_mods` (raw DEX flags → Constructor.getModifiers R-NEW-380),
  `__reflect_params` (comma-joined → Constructor.getParameterTypes S60).
- NEVER null (the Kotlin intrinsic demand) — empty array for synthetic
  tokens (libcore parity).
- `[F-NEW-517]` bounded diag (16 lines).

## 3. VERIFY

| gate | result |
|---|---|
| peri (90s) | face b5a7a35d → **4b1637d6ba3226ea** REAL_APP_CONTENT — Setup screen renders: Allow Files Access / Ignore Battery Optimization / Allow Media Access / Post Notifications (Granted/Not Granted states) + Continue; 497 draw ops replayed; 8 uncaught = ALL F084 wall-clock halts (budget law, not app bugs) |
| peri (300s) | face **4b1637d6** byte-identical ×2, **ZERO uncaught** — budget-stable deterministic content |
| anchors | 6/6 ×2 byte-identical ZERO DRIFT: opencalc 63020bc7 / chess a0319686 / microtimer bbd350b6 / unote 7481e9b4 / tower3d 11a38a5a / dooz 851cc176@300s |
| negatives | 19/19 (probe store regenerated into run/gatea/probe_store — the s41 harness path law: BASE=run/gatea, NOT the repo-root probe_store) |
| selftest | 13/13 PASS |
| cluster honesty | notepad + netguard do NOT share this root: notepad = F-NEW-515 family (content-provider IAE) + 2 NPE pins; netguard = Service-Context-null f141 family (getPackageInfo/newWakeLock/obtainStyledAttributes on null Context). Both stay with their registered rows — no false cluster credit. |

Registry 831→832 (F-NEW-514 → ROOT-CAUSED-FIXED with decode addendum;
F-NEW-517 registered ROOT-CAUSED-FIXED), id-unique.
