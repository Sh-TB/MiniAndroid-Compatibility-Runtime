# MiniAndroid Project State

**Last updated:** 2026-08-17 (EXP-047)
**Latest commit:** ed0879c

## Current Execution Frontier

**LaunchActivity.onCreate COMPLETES** with 189 unique methods, 5 JNI calls dispatched, 0 HALT events.

### Checkpoints

| Checkpoint | Status | Evidence |
|-----------|--------|----------|
| A: LaunchActivity entered | ✅ | METHOD-IN log |
| B: LaunchActivity completed | ✅ | Result: SUCCESS |
| C: Application initialized | ✅ | postInitApplication reaches PC=224+ |
| D: UserConfig initialized | ✅ | UserConfig.getInstance, loadConfig (492 insns) |
| E: SharedPreferences accessed | ✅ | SharedPrefsHelper.init, getSharedPreferences |
| F: NativeLoader reached | ✅ | NativeLoader.initNativeLibs (234 insns) |
| G: First native dispatched | ✅ | native_getCurrentTime × 5 via JNI bridge |
| H: Persistent state | ❌ | Not yet tested with two-process proof |
| I: Login UI state | ❌ | Not yet reached |

## Current Blocker

The execution COMPLETES successfully in 3.4s with 189 methods. The next frontier is:
1. **Persistent SharedPreferences** — need two-process persistence proof
2. **Deeper LaunchActivity.onCreate** — the method has 1330 instructions and may reach Login UI paths
3. **More native methods** — ConnectionsManager.native_init, native_setJava not yet dispatched

## Solved Blockers (EXP-047)

| ID | Description | Commit |
|----|-------------|--------|
| const/4 register/literal extraction | 11n format B\|A\|op was decoded wrong | 3b726b6 |
| Per-DEX field resolution | field_idx was resolved from merged DEX | fd1de55 |
| JNI bridge | 12 native method stubs registered | 46e1ee3 |

## Key Evidence Files

- `run/exp047/first_native_call.json` — First native method dispatch proof
- `docs/EXP046_NATIVE_MAP.md` — 462 native methods inventoried
- `docs/EXP046_PROGRESS.md` — EXP-046 progress summary
- `docs/exp045/BASELINE.md` — EXP-045 baseline
- `docs/exp045/FINAL_STATUS.md` — EXP-045 final status
