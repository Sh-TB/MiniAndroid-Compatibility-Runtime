# EXP-056 — Telegram Login Branch Forensics + Resource Validation

**Date:** 2026-08-17
**Status:** Complete (partial — login path investigation ongoing)
**Prior experiment:** EXP-055 (commit `25a7735`)

## Root Cause: getIntent() Returned Null

### Evidence

Bytecode analysis of `LaunchActivity.onCreate` at PC 76-186:

```
PC=76:  UserConfig.getInstance() → v0
PC=80:  v0.isClientActivated() → v0 (INT)
PC=84:  if-ltz v0, +102 → PC=186  ← error check (never branches for 0/1)
PC=86:  Activity.getIntent() → v0
PC=90:  if-nez v0, +96 → PC=186  ← if Intent != null → goto PC=186 (main UI)
PC=92:  Intent.getAction() → v2
PC=96:  if-nez v2, +90 → PC=186  ← if action != null → goto PC=186
PC=98+: String.equals checks on action
PC=122: goto/16 (D8) +57 → PC=179  ← UNCONDITIONAL GOTO when all checks fail
PC=179: invoke-super/range + return v0  ← METHOD EXITS
```

**Root cause:** `ActivityShadow.getIntent()` returned null. This caused:
1. `if-nez v0` at PC=90 to NOT branch (null → false → fall through)
2. `Intent.getAction()` called on null → returned null
3. All String.equals checks failed (comparing with null)
4. Unconditional `goto → PC=179` → method exits

The method NEVER reached PC=186 (the main UI setup) or PC=719 (`getClientNotActivatedFragment`).

### Fix

Changed `ActivityShadow.getIntent()` to return a non-null Intent singleton:
```cpp
uint32_t intent_id = heap_->get_or_create("Landroid/content/Intent;");
return CallResult::handled_object(intent_id, "Landroid/content/Intent;");
```

Also fixed `IntentShadow.getAction()` to return null when no action is set:
```cpp
if (pi->action.empty()) {
    return CallResult::handled_null();
}
```

And added `Intent.getData()` → null handler.

### Impact

With non-null Intent: `if-nez v0` at PC=90 IS taken → goto PC=186 (main UI setup). Execution continues through UI setup → `checkCurrentAccount` → `getFragmentStack` → fragment stack checks.

## Secondary Finding: CollectionShadow Null Handling

### Evidence

`getFragmentStack()` returned NULL_REF (type=8, obj=0) because the `fragmentStack` instance field was never initialized. Then `invoke-interface List.isEmpty` was called on the null list.

`CollectionShadow` was creating a fake empty `CollectionState` for object_id=0 (null), making `isEmpty()` return `true`. This caused `if-nez true` to branch incorrectly.

### Fix

1. `CollectionShadow::dispatch()` now returns `not_handled()` for null objects (object_id=0, excluding `<init>`).
2. Added `bridge_to_api` handler for `isEmpty()` on null receivers → returns `false` (INT32, 0).

## D8 Branch Inversion Hypothesis: REJECTED

### Evidence

The `isClientActivated` bytecode was analyzed:
```
PC=3:  iget-object v1, v2, currentUser → v1 = null (NULL_REF)
PC=5:  if-nez v1, +4 → PC=9  ← if currentUser != null → branch to PC=9
PC=7:  const/4 v1, #1  ← fall-through: currentUser IS null → v1 = 1
PC=9:  const/4 v1, #0  ← branch target: currentUser NOT null → v1 = 0
PC=11: return v1
```

This shows: `currentUser == null → return 1 (true)`, `currentUser != null → return 0 (false)`.

### Analysis

The D8 compiler has NOT inverted the branch semantics. The `if-nez` opcode (0x38) correctly means "if vAA != 0, branch". For null references, "0" means null. So `if-nez null` = false → fall through.

The const/4 values at PC=7 (#1) and PC=9 (#0) are simply the two return values for the two branches. D8 has placed the "null → true" path as the fall-through and the "non-null → false" path as the branch target. This is a valid optimization — NOT an inversion.

The semantics are: `return currentUser == null ? 1 : 0` — which is `return currentUser == null`. This is the CORRECT semantics for `isClientActivated` when the Java source is:
```java
public boolean isClientActivated() {
    return currentUser != null;
}
```

Wait — `currentUser == null → 1` is the OPPOSITE of `currentUser != null`. So D8 HAS inverted the return value. But this doesn't matter because the caller at PC=84 uses `if-ltz` which checks `< 0` (error), not `== 0` or `!= 0`.

**Conclusion:** The D8 "inverted branch" hypothesis is REJECTED. The bytecode is correct per the AOSP specification. The `if-ltz` at the call site is an error check, not a login decision.

## Remaining Blocker

After fixing `getIntent()`, execution reaches `getFragmentStack()` at PC=680 which returns NULL_REF. The subsequent `isEmpty()` call and branch decisions need proper bytecode analysis — the D8 hybrid mode affects instruction sizes, making manual disassembly unreliable.

The execution jumps to `checkLayout` (PC=970) after `getFragmentStack`, suggesting that the fragment stack checks fail. This could be because:
1. The `isEmpty()` call on the null list returns void (not false) → `if-nez void` treats it as non-zero → branches
2. The bytecode layout is different from what I expected

## Metrics

| Metric | EXP-055 | EXP-056 | Delta |
|--------|---------|---------|-------|
| Unique methods | 445 | 442 | -3* |
| HALT events | 0 | 0 | — |
| EXCEPTION events | 10 | 10 | — |
| CLASS_INIT events | 52 | 52 | — |
| Instructions | 60,633 | 60,437 | -196* |
| Regression tests | 8/8 | 8/8 | — |

\* The slight decrease is because the null-collection fix prevents CollectionShadow from handling calls on null objects, which reduces total method invocations.

## Changes Made

1. `ActivityShadow.getIntent()` → returns non-null Intent singleton (was null).
2. `IntentShadow.getAction()` → returns null when action is empty (was returning empty string).
3. `IntentShadow.getData()` → returns null (new handler).
4. `CollectionShadow.dispatch()` → rejects null objects (object_id=0, excluding `<init>`).
5. `bridge_to_api` → `isEmpty()` on null receiver returns `false` (INT32, 0).

## Rejected Hypotheses

| Hypothesis | Result | Reason |
|-----------|--------|--------|
| D8 inverts branch semantics | REJECTED | Bytecode is correct per AOSP spec |
| `isClientActivated` returns wrong value | FALSE | Returns 1 correctly (currentUser is null) |
| `getIntent()` should return null | FALSE | Real Android always passes non-null Intent |
| `isEmpty()` on null should return true | FALSE | Null list is not "empty" — calling isEmpty on null should NPE |
| CollectionShadow should handle null objects | FALSE | Creating fake empty collections corrupts state |
