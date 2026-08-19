# EXP-052 Regression Test Suite

**Date:** 2026-08-17

## Test Cases

### reg_invoke_virtual_return
invoke-virtual returns object (toString) — verify move-result-object.

### reg_invoke_static_return
invoke-static returns int (helper returns 42) — verify move-result.

### reg_branch_if_eqz
if-eqz on const/4 v0, #0 — branch should be taken.

### reg_branch_if_nez
if-nez on const/4 v0, #1 — branch should be taken.

### reg_goto_simple
goto +2 — skip next instruction.

### reg_thread_identity
Thread.currentThread() == Looper.getMainLooper().getThread()

## Results

| Case | Exit | THROW | HALT | Notes |
|------|------|-------|------|-------|
| reg_invoke_virtual_return | 0 | 0 | 0 | PASS |
| reg_invoke_static_return | 0 | 0 | 0 | PASS |
| reg_branch_if_eqz | 0 | 0 | 0 | PASS |
| reg_branch_if_nez | 0 | 0 | 0 | PASS |
| reg_goto_simple | 0 | 0 | 0 | PASS |
| reg_thread_identity | 0 | 0 | 0 | PASS |
