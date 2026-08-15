# MiniAndroid Hypotheses

Active and resolved hypotheses about the runtime's behavior and the path to
running Telegram successfully.

## H-001 (RESOLVED — true) — OOM root cause is per-instruction snapshots

**Hypothesis (EXP-042 Phase 1):** The OOM killing Telegram execution is caused
by `result.instruction_traces[].registers_before` and `registers_after`
snapshots retained forever. Each snapshot is `std::map<std::string, DalvikValue>`
≈ 16 × 152 B = 2.4 KB; × 2 snapshots = 4.8 KB; plus trace overhead 400 B
= ~5.2 KB per instruction. At 10 M instructions: ~52 GB.

**Evidence:** Memory probes confirmed RSS growing past 3.6 GB → OOM-killed.
After fix (gated snapshots + ring buffers), RSS flat at 438-440 MB across
2 M+ instructions.

**Resolution:** Confirmed. Fix in commit d48d479.

## H-002 (RESOLVED — true) — Return-opcode bounds check causes infinite loops

**Hypothesis (EXP-042 Phase 2):** `execute_return` and `execute_return_object`
had `if (pc + 1 >= bytecode_.size()) return false;` — for 1-unit instructions
at the LAST PC of a method, `pc+1 == size`, the check failed, `pc_` was not
advanced, and the engine re-fetched the same opcode 50 000 times until the
loop detector halted the method.

**Evidence:** `Util.castNonNull` has 1 instruction (`return-object v0`) at
PC=0 with `bytecode_size=1`. Loop detector fired at PC=0 50 001 times.
After fix (`pc_ = pc + 1`), method exits in 1 instruction.

**Resolution:** Confirmed. Fix in commit d48d479.

## H-003 (RESOLVED — true) — iget/iput returning false causes infinite loops

**Hypothesis (EXP-042 Phase 2):** When `iget-object` failed to resolve a
field or the object register was uninitialized, it returned `false` without
advancing `pc_`. The fetch loop re-fetched the same opcode infinitely.

**Evidence:** `FragmentActivity.onCreate`, `ComponentActivity.onCreate`,
`FlagSecureReason.attach` all looped at PC=0 with `op=0x54/0x55` (iget-*
variants). After making all error paths advance `pc_` and return `true`
with sensible defaults (null/0), execution proceeded past them.

**Resolution:** Confirmed. Fix in commit d48d479.

## H-004 (RESOLVED — true) — Per-frame pc_visit_count_ requires save/restore

**Hypothesis (EXP-042 Phase 2):** The `static thread_local` pc-visit counter
leaked across recursive invocations of `execute_method_internal`. When the
inner method's loop detector fired at PC=X with 50 000 visits, the counts
persisted into the caller's frame. The caller's NEXT instruction at PC=Y
would have its count multiplied by the recursive call count, causing false
loop detection.

**Evidence:** Every Telegram method was exiting at exactly 50 001 instructions
even those with no loops. After saving/restoring `pc_visit_count_` in
`try_recursive_invoke`, methods exit at their natural instruction count.

**Resolution:** Confirmed. Fix in commit d48d479.

## H-005 (ACTIVE) — Intrinsics.createParameterIsNullExceptionMessage loops
because Kotlin NPE path is triggered by null `savedStateRegistry`

**Hypothesis (EXP-043 Phase 1):** The execution path is:
```
LaunchActivity.onCreate
  → super.onCreate (FragmentActivity.onCreate)
    → SavedStateRegistryController.performAttach
      → (reads this.savedStateRegistry which is null)
      → Intrinsics.checkNotNullParameter(null, "savedStateRegistry")
        → throwParameterIsNullNPE
          → createParameterIsNullExceptionMessage
            → iget-object on null `this` (Intrinsics is a static utility class
               but the message builder tries to read instance fields)
            → LOOP at PC=0xf
```

**Experiment:** Dump `Intrinsics.checkNotNullParameter` bytecode. If it has
`if (parameter == null) throwParameterIsNullNPE(...)`, the fix is to stub
`checkNotNullParameter` as a no-op (since the parameter IS null because
`savedStateRegistry` is null, and the NPE path is what's failing).

**Validation:** After fix, execution should proceed past
`SavedStateRegistryController.performAttach` and reach the next blocker.

**Status:** to be verified by dumping bytecode.

## H-006 (PENDING) — First native call requires libtmessages.49.so loading

**Hypothesis (EXP-043 Phase 2):** The first JNI call from Telegram's startup
path is likely `NativeLoader.init()` or `ConnectionsManager.native_*()`. The
number of DEX methods that execute before this call is the "JNI distance".

**Experiment:** Scan all 5 DEX files for `System.loadLibrary("tmessages")`
call sites and for native method declarations that appear in classes on
the current execution path. Measure the call chain depth.

**Validation:** The result is documented in `docs/EXP043_JNI_DISTANCE.md`.
This number determines the remaining difficulty before native code is needed.
