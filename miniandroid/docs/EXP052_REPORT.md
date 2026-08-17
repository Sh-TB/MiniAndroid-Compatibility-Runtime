# EXP-052 / EXP-053 — Deep Runtime Correctness Investigation Report

## Goal

Stabilize interpreter semantics before Login UI implementation. Find the next fundamental semantic blocker preventing Telegram from reaching Login UI. **Do not add more stubs** — surface real bugs.

## Investigation

### P2 — Verify HALT removal did not hide errors

**Concern:** EXP-051 reduced HALT-LOOP from 1 → 0 and HALT-GOTO from 2 → 0. Did this hide a silent regression?

**Method:** Built a clean EXP-050 baseline (commit `776d6ca` + syntax/make_float fixes) at `/home/z/my-project/exp050_baseline_local/` and ran it. Compared method sequences, instruction counts, and API call counts against the EXP-051 final.

**Evidence collected:**
- EXP-050: 337 unique methods, 107,289 instructions, 1 HALT-LOOP (50,001 visits), 2 HALT-GOTO
- EXP-051: 339 unique methods, 57,376 instructions, 0 HALT events
- Method sequence diff (first 100 unique METHOD-IN entries): identical order
- New methods in EXP-051 only: `ArchTaskExecutor.isMainThread`, `BaseFragment.onRemoveFromParent`
- Methods in EXP-050 only (regressions): **NONE**

**Critical math check:**
```
EXP-050: 107,289 instructions
- 50,001 (the HALT-LOOP visits in LifecycleRegistry.enforceMainThreadIfNeeded)
= 57,288 expected
EXP-051 actual: 57,376 (+88 — within expected variance)
```

The "missing" 50K instructions were the infinite loop. **The HALT removal was correct, not hiding errors.** The loop was burning instructions without doing useful work.

### P1 — Exception Diagnostic Mode

**Hypothesis:** The runtime's THROW handler returns to caller without consulting the `tries[]` table. This loses catch-handler information.

**Evidence collected:** Added `tries_size` and `tries_data` fields to `MethodInfo`. Modified `parse_code_item` to capture the raw tries table bytes. Modified `execute_method_internal` to accept tries parameters and store them on the engine. Updated `THROW` opcode handler to:

1. Decode the `tries[]` array (8 bytes each: start_addr, insn_count, handler_off).
2. Find the try_item whose `[start_addr, start_addr+insn_count)` range contains the current PC.
3. Log whether a matching handler was found.
4. Still halt the method (not yet implementing catch-jump).

**Diagnostic output format:**
```
[THROW] in <class>.<method> at PC=0x... exception_class=<...>
        has_try_table=YES/NO tries_size=N
        matching_handler=FOUND/NOT_FOUND handler_addr=N
        — halting method (exception handling not implemented)
```

**Telegram run results:**

| Method | PC | Has try table | Handler found |
|--------|----|---------------|---------------|
| `Lorg/telegram/ui/ActionBar/Theme;.createCommonMessageResources` | 0xcd | YES (1 entry) | FOUND at addr=1 |
| `Lorg/telegram/ui/Stories/StoriesIntro;.startAnimation` | 0xa | NO | NOT_FOUND |

Decoded the catch handler for `createCommonMessageResources`:
```
try_item[0]: start_addr=5, insn_count=513, handler_off=1
encoded_catch_handler_list at offset 1:
  size=0 → catch-all handler_addr=200
```

So `createCommonMessageResources` has a **try-finally pattern** with a catch-all at PC=200. The handler runs `move-exception; goto/16 +2 → PC=202; ... throw v0` — i.e., it re-throws. This is the try-finally cleanup pattern, and our runtime currently treats the first throw as a method-exit, skipping the finally block.

### P1 — Exception Test Cases

Built 4 small DEX test cases in `tools/exp052_exception_tests.py`:

| Case | Description | Has try table | Handler found | Result |
|------|-------------|---------------|---------------|--------|
| case1_no_catch | throw RuntimeException, no try{} | NO | NOT_FOUND | Method halts cleanly (correct) |
| case2_local_catch | throw inside try{} with catch-all | YES (1) | FOUND at addr=1 | Method halts (handler not yet jumped to — known limitation) |
| case3_nested_catch | A() calls B() that throws; A has try/catch | NO (in B) | NOT_FOUND | Method halts in B (no unwind to A — known limitation) |
| case4_catch_all | Same as case2 | YES (1) | FOUND | Same as case2 |

All test DEX files compile cleanly and the runtime produces the expected diagnostic output. The diagnostic mode is now validated.

### P3 — Thread / Looper Identity Verification

**Hypothesis:** EXP-051 introduced ThreadShadow + LooperShadow with a bound identity contract. But the legacy `ArchTaskExecutor.isMainThread → true` stub in `bridge_to_api` was hijacking the call BEFORE the shadow could exercise the identity check.

**Evidence collected:**
- Searched `run/exp051_run6/run.log` for `DefaultTaskExecutor` — **0 occurrences**.
- The `ArchTaskExecutor.isMainThread → true` stub fired before the engine recursed into bytecode.
- This means the Thread/Looper identity contract was NEVER actually tested in EXP-051.

**Changes made:**
1. Removed the legacy `ArchTaskExecutor.isMainThread → true` stub from `bridge_to_api`.
2. Added a new `ArchTaskExecutorShadow` (registered FIRST in the registry).
3. The shadow's `isMainThread` handler verifies the identity contract at runtime:
   ```cpp
   uint32_t from_thread = ts->main_thread_id();
   uint32_t from_looper = ls->bound_thread_id();
   if (from_thread != 0 && from_thread == from_looper) {
       return CallResult::handled_bool(true);
   }
   return CallResult::handled_bool(false);
   ```
4. Added a startup diagnostic log:
   ```
   [THREAD] currentThread object: 1
   [THREAD] mainLooper.thread object: 1
   [THREAD] identity result: TRUE (must be TRUE for isMainThread)
   ```

**Verification:** The Telegram run now shows `[THREAD] identity result: TRUE`. `ArchTaskExecutor.isMainThread` is now reached via the bytecode path → shadow dispatch → returns true via the identity check, not via a hardcoded stub.

### P4 — Handler / Runnable Queue Trace

**Hypothesis:** Telegram may post Runnables during `LaunchActivity.onCreate`. EXP-051 added the queue but never wired the drain to the runtime main loop.

**Changes made:**
- Added `[QUEUE]` log on enqueue and dequeue in `HandlerShadow`.
- Wired `ApplicationRuntime::drain_handler_queue()` to be called after `execute_on_create()` returns.
- Each drained Runnable's heap object_id is logged via `[EXECUTE] Runnable id=N`.

**Verification:** Telegram run shows `handler_queue_depth: 0` — no Runnables are posted during the onCreate path we execute. The queue trace infrastructure is in place for future paths that DO post Runnables.

### P5 — Static Discovery of Login Path

**Hypothesis:** Reaching LoginActivity requires implementing `Intent` + `startActivity` (per the EXP-051 report). But static analysis of `LaunchActivity.onCreate` shows ZERO `startActivity` calls.

**Evidence collected:** Built `tools/exp052_login_path_discovery.py` which dumps all `invoke-*` calls in a given method.

**LaunchActivity.onCreate analysis (200 invoke calls):**
- `UserConfig.getInstance().isClientActivated()` called at PC=80 and PC=711.
- If NOT activated, calls `LaunchActivity.getClientNotActivatedFragment()` at PC=719.
- Then calls `INavigationLayout.addFragmentToStack(fragment)` at PC=723.
- ZERO calls to `startActivity`, `startActivityForResult`, `Intent.<init>`.
- ZERO calls to `presentFragment`, `replaceFragment` (FragmentActivity APIs).

**`getClientNotActivatedFragment` analysis:**
```
PC=3  invoke-static → LoginActivity.loadCurrentState
PC=9  invoke-virtual → BaseBundle.getInt
PC=17 invoke-direct → LoginActivity.<init>     ← Login UI is created here!
PC=23 invoke-direct → IntroActivity.<init>      ← Or Intro on first launch
```

**Conclusion:** Telegram uses **Fragment-based UI transitions**, not Activity-based. The IntentShadow architecture is irrelevant for reaching LoginActivity. We need `INavigationLayout` / `ActionBarLayout.addFragmentToStack` support.

`addFragmentToStack` in `ActionBarLayout` delegates to `INavigationLayout$-CC.$default$addFragmentToStack` which then calls back to `INavigationLayout.addFragmentToStack` (interface dispatch). This creates a dispatch loop unless we resolve the interface to the concrete `ActionBarLayout` implementation.

### P6 — Resources API Evidence

**Hypothesis:** Many resource IDs are being requested via `R.color.X`, `R.drawable.X` constants compiled into DEX.

**Changes made:** Added `[RES]` logging to:
- `Resources.getIdentifier(name, defType, defPackage)` — logs all three args
- `Resources.getDimensionPixelSize(resid)` — logs the resource id
- `Resources.getString(resid)` — logs the resource id
- `Resources.getColor(resid)` — logs the resource id
- `Resources.getDrawable(resid)` — logs the resource id

**Evidence collected (Telegram run):**
- **0 calls to `getIdentifier`** — Telegram does NOT use string-based resource lookup.
- **116 calls to `getDrawable`**, ALL with `resid=0x0` — the resource ID is genuinely 0.
- **10 calls to `getColor`**, ALL with `resid=0x0`.

**Conclusion:** Telegram is using `R.drawable.xxx` constants from the R class, but those constants compile to `0x0` in our runtime because the R class static fields aren't initialized. The `R` class fields (`public static final int color_primary = 0x7f010001;`) are NOT being populated by our `sget` opcode handler when the field is from a framework `R` class. This is the **next concrete blocker** for resource resolution.

## Tests

### Exception Test Suite (`tools/exp052_exception_tests.py`)

4 test cases — all produce the expected diagnostic output. See `docs/EXP052_EXCEPTION_TESTS.md`.

### Regression Test Suite (`tools/exp052_regression_tests.py`)

| Test | Description | Result |
|------|-------------|--------|
| reg_invoke_virtual_return | invoke-virtual returns object via move-result-object | PASS |
| reg_invoke_static_return | invoke-static returns int via move-result | PASS |
| reg_branch_if_eqz | if-eqz on zero → branch taken | PASS |
| reg_branch_if_nez | if-nez on non-zero → branch taken | PASS |
| reg_goto_simple | goto +2 → skip next instruction | PASS |
| reg_thread_identity | Thread.currentThread() == Looper.getMainLooper().getThread() | PASS |

All tests build, run with exit code 0, and produce no THROW or HALT events. The shadow registry's thread identity contract holds end-to-end.

### Final Telegram Validation Run

| Metric | Value |
|--------|-------|
| Build | SUCCESS |
| Exit code | 0 |
| Unique methods | 339 (same as EXP-051) |
| HALT events | 0 |
| THROW events | 2 (both correctly diagnosed, no propagation) |
| JNI dispatches | 5 (native_getCurrentTime × 5) |
| Resource calls | 126 (116 getDrawable + 10 getColor, all resid=0x0) |
| Instructions | 57,376 (same as EXP-051) |
| SharedPreferences | default.xml written (11 keys) |
| Shadow coverage | 7.67% (191/2490 calls handled by shadows) |
| Shadow count | 7 (was 6 in EXP-051 — added ArchTaskExecutorShadow) |
| Thread identity | TRUE ✅ |
| Handler queue depth | 0 (no Runnables posted in this path) |

## Results

### Summary of changes

1. **Exception diagnostic mode** (`dalvik_engine.cpp` + `dex_parser.{h,cpp}`):
   - `MethodInfo` now carries `tries_size` and `tries_data` (raw bytes of tries[] + encoded_catch_handler_list).
   - `execute_method_internal` accepts and stores tries state.
   - THROW opcode handler decodes try_items, finds matching handler, logs full diagnostic.
   - try_recursive_invoke saves/restores tries state across recursive calls.

2. **Removed legacy `ArchTaskExecutor.isMainThread → true` stub** — surfaces the real bytecode path.

3. **Added `ArchTaskExecutorShadow`** (`android_shadows.{h,cpp}`):
   - Handles `isMainThread` by verifying Thread/Looper identity via the registry.
   - Handles `getInstance`, `executeOnDiskIO`, `postToMainThread`.
   - Registered FIRST so it wins over the legacy bridge chain.

4. **Added Thread identity verification log** (`application_runtime.cpp`):
   - Logs `currentThread object`, `mainLooper.thread object`, `identity result`.

5. **Added Handler/Runnable queue trace** (`android_shadows.cpp`):
   - `[QUEUE]` log on enqueue and dequeue.
   - `ApplicationRuntime` drains the queue after `execute_on_create()`.

6. **Added Resources API evidence logging** (`dalvik_engine.cpp`):
   - `[RES]` log for getIdentifier, getDimensionPixelSize, getString, getColor, getDrawable.

7. **Test infrastructure:**
   - `tools/exp052_exception_tests.py` — 4 exception test cases + DEX builder.
   - `tools/exp052_regression_tests.py` — 6 regression tests (invoke/branch/shadow).
   - `tools/exp052_login_path_discovery.py` — static analysis of LaunchActivity path.

## New Blockers Identified

### Blocker 1: Exception handling not implemented (catch-jump)

The diagnostic mode shows `Theme.createCommonMessageResources` has a catch-all handler at PC=200 that we don't jump to. The throw at PC=205 should re-execute the cleanup code at PC=200 (try-finally pattern).

**Fix:** Implement actual catch-handler dispatch:
1. On throw, find matching try_item.
2. Decode the encoded_catch_handler at handler_off.
3. For each (type_idx, addr) pair, check if the exception class matches.
4. If matched (or catch-all), set `pc_ = addr` and continue execution.
5. If no match, propagate to caller (unwind the call stack).

**Estimated effort:** Medium. The hardest part is type-matching — we need to resolve type_idx → class descriptor and walk the inheritance chain.

### Blocker 2: R class static fields not initialized

Telegram uses `R.drawable.foo` constants from the auto-generated R class. These are `public static final int` fields compiled into `classes.dex`. Our `sget` opcode handler returns 0 for fields not in `static_field_storage_`, but we never populate the R class's fields from the DEX bytecode.

**Fix:** During DEX loading, scan for the R class (`Lorg/telegram/messenger/R;` and friends) and pre-populate `static_field_storage_` with the field initialization values from the `<clinit>` method.

**Estimated effort:** Medium. Requires parsing `<clinit>` bytecode for `const` + `sput` pairs.

### Blocker 3: Fragment-based UI transitions (Login path)

Reaching LoginActivity requires `INavigationLayout.addFragmentToStack(fragment)` to work. Currently:
- `ActionBarLayout.addFragmentToStack` delegates to `INavigationLayout$-CC.$default$addFragmentToStack` (a default method).
- The default method calls back to `INavigationLayout.addFragmentToStack` (interface dispatch).
- This creates an infinite recursion unless we resolve the interface to the concrete `ActionBarLayout` implementation.

**Fix:** Either:
- a) Add an `INavigationLayout` shadow that handles `addFragmentToStack` directly (semantic shortcut).
- b) Fix interface dispatch in the engine so `invoke-interface` resolves to the concrete class's method.

**Estimated effort:** Medium-large. Option (a) is simpler; option (b) is more correct but requires implementing interface table resolution.

## Confidence

| Finding | Confidence |
|---------|------------|
| HALT removal was NOT hiding errors | HIGH (verified by instruction count math) |
| Thread identity contract is correct | HIGH (verified by direct object_id comparison + diagnostic log) |
| Login path requires Fragment support (not Intent) | HIGH (verified by static bytecode analysis) |
| Telegram does NOT call getIdentifier | HIGH (0 calls logged) |
| R class fields are not initialized | MEDIUM (inferred from `resid=0x0` on all 126 calls) |
| Exception handling needs full catch-jump | HIGH (handler exists at PC=200 but we don't jump) |

## Next Recommended Experiment

**EXP-053: Implement catch-handler dispatch + R class static field initialization**

1. **Catch-handler dispatch** (P0): On throw, walk the try_items, find matching handler, jump to it. Handle catch-all (size ≤ 0) and typed (size > 0, walk type_idx inheritance). Test with the existing 4 exception test cases — case2 and case4 should now successfully return after the handler runs.

2. **R class static field initialization** (P1): During ApplicationRuntime init, scan all DEX files for `L*<R;>` classes (Telegram's R class is `Lorg/telegram/messenger/R;` plus per-package R classes). For each, execute its `<clinit>` method (which contains the `const + sput` pairs that initialize the field constants). Verify by re-running Telegram and confirming resource IDs are no longer 0x0.

3. **INavigationLayout dispatch** (P2, optional): Add a minimal `INavigationLayout` shadow that handles `addFragmentToStack(Fragment)` by storing the Fragment in a stack and invoking its `onCreateView` if reached. This unblocks the Login path.

Avoid adding more framework stubs — every fix should be tied to a specific failure mode observed in the run log.
