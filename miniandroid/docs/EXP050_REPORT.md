# EXP-050 Final Report

**Date:** 2026-08-17
**Commit:** de1540c

## What Changed

### CRITICAL: Return Value Propagation Fix

**Root cause:** `move-result` and `move-result-object` opcodes were returning placeholder values (0 and null) instead of the actual return value from the last `invoke-*` instruction. This silently discarded ALL return values from ALL method calls.

**Impact:** Every `if-eqz`/`if-nez` after an invoke was testing 0/null instead of the real return value. Every field access after a getter was using null. Every object reference from a factory method was lost.

**Fix:** Added `last_invoke_return_` member to `DalvikExecutionEngine`. Every invoke-* handler (invoke-virtual, invoke-super, invoke-direct, invoke-static, invoke-interface, invoke-*/range) now stores its return value. `move-result` and `move-result-object` read from this member.

### SharedPreferences Persistence PROVEN

Telegram's own code generated `runtime/data/org.telegram.messenger/shared_prefs/default.xml` via `edit().putBoolean().commit()`. The XML contains real Telegram preference keys with real values.

### HALT-LOOP Stubs

Added stub-only entries for methods that loop due to missing threading/animation state:
- `ArchTaskExecutor.isMainThread` — thread comparison fails in single-threaded runtime
- `BaseFragment.getLastStoryViewer` — story viewer not available
- `SpringAnimation.sanityCheck/start` — animation validation loop
- `DynamicAnimation.startAnimationInternal` — animation start loop

## Before/After Metrics

| Metric | EXP-049 (Before) | EXP-050 (After) | Delta |
|--------|-----------------|-----------------|-------|
| Unique methods | 200 | **336** | **+136** |
| JNI calls | 5 | 5 | — |
| HALT-LOOP | 0 | 6 | +6 (deeper execution) |
| HALT-GOTO | 0 | 0 | — |
| Memory peak | 440 MB | 452 MB | +12 MB |
| SharedPreferences files | 0 | **1** | +1 |
| Result | SUCCESS | SUCCESS | — |

## Evidence

- `run/exp050_returnval.log` — execution log with 336 unique methods
- `runtime/data/org.telegram.messenger/shared_prefs/default.xml` — real Telegram SharedPreferences output
- `docs/EXP050_CURRENT_STATE.md` — complete state document

## Remaining Debt

1. **6 HALT-LOOP events** — from threading/animation state gaps
2. **invoke-* return value** — now propagated, but some API bridge methods may still return void when they should return objects
3. **LoginActivity** — not yet reached (checkCurrentAccount is reached)
4. **More native methods** — only native_getCurrentTime dispatched
5. **View hierarchy** — not yet tracked

## Next Predicted Blockers

1. **Thread identity** — `Thread.currentThread()` vs `Looper.getMainLooper().getThread()` comparison
2. **View creation** — `setContentView` needs to track View hierarchy
3. **Intent** — `startActivity` needs Intent support for LoginActivity
4. **More SharedPreferences keys** — const-string resolution for preference names
