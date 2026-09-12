# EXP-059 Phase 0 — Baseline (EXP-058 final state)

**Date:** 2026-08-19
**Build commit:** 7641717 (EXP-058 final)
**Goal:** Establish a forensic baseline before any EXP-059 code changes.

## Run Configuration

- APK: `download/exp038_telegram/Telegram.apk` (Telegram 12.9.2, 82.7 MB)
- Binary: `build_exp042/miniandroid_exp042`
- Output dir: `run/exp059_baseline/`
- Output files: `stdout.log`, `stderr.log`, `application_runtime.json`, `screenshot.png`

## Baseline Metrics (EXP-058 final state)

| Metric | Value |
|--------|-------|
| Total instructions executed | 38,879 |
| Unique methods (`[METHOD-IN]` distinct) | 454 |
| Unique classes | 215 |
| HALT events | 0 |
| EXCEPTION events | 18 |
| CLASS_INIT events | 56 |
| `addFragmentToStack` mentions | 17 |
| `onFragmentCreate` mentions | 2 |
| `setParentLayout` mentions | 0 |
| `onCreateView` mentions | 0 |
| `createView` mentions | 2 (BaseFragment stub only) |
| `onResume` mentions | 0 |
| Heap objects | 3,021 |
| Duration | ~6 seconds |
| Peak RSS | ~503 MB |

## Verified Execution Frontier

```
LaunchActivity.onCreate ✅
  → getIntent() → non-null Intent ✅
  → isClientActivated() → returns 1 (currentUser is null) ✅
  → getFragmentStack() → returns NULL_REF ✅
  → List.isEmpty() → returns false (null receiver) ✅
  → getClientNotActivatedFragment() → ENTERED ✅
  → LoginActivity.loadCurrentState() → stubbed (loop guard)
  → addFragmentToStack() → CALLED ✅
      → onFragmentCreate() on BaseFragment → returns 1 (true) ✅
      → fragmentsStack.contains() → returns VOID_ (null receiver)
      → if-nez VOID_ → not branched  ← BLOCKER (PC=24)
  → BLOCKED: addFragmentToStack returns 0 (false) at PC=26
```

## Identified Blocker (to be fixed in Phase 5)

`ActionBarLayout.addFragmentToStack(BaseFragment, int)` returns 0 (false) because:

1. At PC=18, `iget-object v0, this.fragmentsStack` returns NULL_REF
   (field never initialized — see Phase 1-4 investigation).
2. At PC=20, `invoke-interface List.contains(fragment)` runs on a null
   receiver and returns VOID_.
3. At PC=24, the bytecode `if-eqz v0, +3 → PC=27` is dispatched to
   `execute_if_nez` (the WRONG handler — see Phase 2 opcode audit).
4. `if-nez` does NOT branch when v0 is zero, so execution falls through
   to PC=26 `return v1 (false)`.

The runtime reaches `onFragmentCreate` but then returns false at PC=26
without ever calling `setParentLayout`, `attachView`, `createView`, or
building any View hierarchy.

## Reproducibility

Single run captured. Output preserved in `run/exp059_baseline/`.
