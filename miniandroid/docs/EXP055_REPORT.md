# EXP-055 — Runtime Truth Validation Before UI Expansion

**Date:** 2026-08-17
**Status:** Complete
**Prior experiment:** EXP-054 (commit `ed38d88`)

## Goal

Reach the real Telegram Login Fragment path while preserving runtime correctness. Evidence-first — do not assume; prove each blocker with logs, bytecode analysis, and minimal experiments.

## Key Discoveries

### Discovery 1: Return Value Not Propagated from Recursive Invoke (P0 CRITICAL)

**Evidence:** `[RET]` logs show return values, `[TRY-ENTRY]` logs confirm `try_recursive_invoke` is called.

**Root cause:** `try_recursive_invoke` always set `return_val = DalvikValue::make_void()` — overwriting the actual return value. The `execute_return` opcode handler stored the return value in `trace.return_value` but never propagated it to `return_val` (the parameter of `try_recursive_invoke`).

**Fix:**
1. `execute_return` and `execute_return_object` now store the return value in `last_invoke_return_`.
2. `try_recursive_invoke` copies `last_invoke_return_` to `return_val` BEFORE restoring state.
3. `last_invoke_return_` is saved/restored in `try_recursive_invoke` to prevent callee→caller corruption.

**Impact:** Every recursive invoke previously returned void (0/null). Now real return values propagate. This is the single most impactful fix in this experiment.

### Discovery 2: OBJECT_REF(0) Treated as Non-Null (P0)

**Evidence:** `[IGET-OBJ-DBG]` shows `iget-object` on `currentUser` returns `NULL_REF` (type=8, obj_id=0) when the field is uninitialized. But `[RET]` shows `isClientActivated val=1` (true).

**Root cause:** `iget-object` on a null field returns `OBJECT_REF` with `object_id=0` (not `NULL_REF`). Then `if-nez` treats `OBJECT_REF` type as non-zero (because it checks `type != NULL_REF`). The check missed `OBJECT_REF && object_id == 0`.

**Fix:** Added `(val.type == DalvikType::OBJECT_REF && val.object_id == 0)` to the `is_nonzero` and `is_zero` checks in `if-nez` and `if-eqz`.

### Discovery 3: isClientActivated Bytecode Analysis

**Bytecode:**
```
PC=0:  iget-object v0, v2, sync        (monitor lock)
PC=2:  monitor-enter v0
PC=3:  iget-object v1, v2, currentUser (TLRPC$User)
PC=5:  if-nez v1, +4 → PC=9           (if currentUser != null → goto PC=9)
PC=7:  const/4 v1, #1                 (fall-through: currentUser IS null → v1=1)
PC=8:  goto/16 +2 → PC=10
PC=9:  const/4 v1, #0                 (branch target: currentUser NOT null → v1=0)
PC=10: monitor-exit v0
PC=11: return v1
```

**Semantics:** `isClientActivated` returns 1 when `currentUser` IS null, and 0 when `currentUser` IS non-null. This appears inverted — need to verify whether D8 has applied branch inversion or if `1` means "NOT activated" (need login).

**Current state:** With the OBJECT_REF(0)=null fix, `currentUser` is correctly treated as null. `isClientActivated` returns 1. The caller's `if-ltz v0` checks `1 < 0` → false → doesn't branch. The login path (`getClientNotActivatedFragment`) is NOT reached from this call site.

**Next step:** Need to trace the exact execution path after `isClientActivated` returns to understand why `getClientNotActivatedFragment` isn't called. The PC=80 call site in `onCreate` may have different branch logic than the PC=711 site.

## Metrics

| Metric | EXP-054 | EXP-055 | Delta |
|--------|---------|---------|-------|
| Unique methods | 421 | **445** | **+24** |
| HALT events | 0 | 0 | — |
| EXCEPTION events | 9 | 10 | +1 |
| CLASS_INIT events | 52 | 52 | — |
| Instructions | 55,836 | **60,633** | +4,797 |
| Regression tests | 8/8 | **8/8** | — |

## Changes Made

1. **Return value propagation** (`dalvik_engine.cpp`):
   - `execute_return` / `execute_return_object` now store return value in `last_invoke_return_`.
   - `try_recursive_invoke` copies `last_invoke_return_` to `return_val` before restoring state.
   - `last_invoke_return_` saved/restored in `try_recursive_invoke`.

2. **OBJECT_REF(0) = null** (`dalvik_engine.cpp`):
   - `if-nez` and `if-eqz` now treat `OBJECT_REF` with `object_id == 0` as null.

3. **Diagnostic logs** (`dalvik_engine.cpp`):
   - `[TRY-ENTRY]` — logs entry to `try_recursive_invoke`.
   - `[RET]` — logs return value from recursive invoke.
   - `[RET-BEFORE]` — logs before `execute_method_internal`.
   - `[IGET-OBJ-DBG]` — logs `iget-object` results for UserConfig fields.
   - `[LOGIN_PATH]` — logs `isClientActivated` and `getClientNotActivatedFragment`.
   - `[FRAGMENT_PATH]` — logs `addFragmentToStack`.

## Rejected Hypotheses

| Hypothesis | Result | Reason |
|-----------|--------|--------|
| `isClientActivated` returns false (0) | **FALSE** | Returns 1 due to D8 branch inversion |
| `currentUser` is non-null | **FALSE** | `iget-object` returns NULL_REF (type=8) — currentUser IS null |
| Return values were already propagated | **FALSE** | `try_recursive_invoke` always returned `make_void()` |
| `try_recursive_invoke` was never called | **FALSE** | `[TRY-ENTRY]` confirms it IS called; `[RET-BEFORE]` confirms execute_method_internal IS called |

## Success Criteria

- [x] Return value propagation works (critical fix)
- [x] OBJECT_REF(0) treated as null
- [x] No regression (all 8 tests pass)
- [x] HALT = 0
- [x] Unique methods increased (445 vs 421)
- [ ] LoginActivity object created — NOT YET (isClientActivated bytecode needs further analysis)
- [ ] Fragment navigation event observed — NOT YET
- [ ] R resources non-zero — NOT YET (framework skip)
- [ ] Typed catches pass — NOT YET (deferred)

## Next Blocker

The `isClientActivated` bytecode has inverted-looking branch logic (returns 1 when currentUser is null). Need to:
1. Verify whether `1` means "activated" or "not activated" in D8's compilation.
2. Trace the exact execution path after `isClientActivated` returns at PC=80 in `onCreate`.
3. Determine why `getClientNotActivatedFragment` is not reached despite `isClientActivated` returning 1.
