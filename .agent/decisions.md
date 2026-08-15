# MiniAndroid Decisions Log

Architecture and engineering decisions, with rationale.

## D-001: Single-pass per-DEX method resolution (EXP-038)

**Decision:** Store per-DEX raw bytes in `DalvikExecutionEngine::per_dex_raw_data_`
and resolve `method_idx` against the correct DEX's `method_ids[]` table.

**Rationale:** When merging 5 DEX files, `method_idx` is per-DEX, not global.
A naive merge causes wrong-method-name resolution (BLOCKER-033). The fix is
local to `DalvikExecutionEngine` (not `DexReport`) to avoid struct layout
issues.

**Trade-off:** 80 MB of additional memory for the 5 DEX files. Acceptable
given that memory is otherwise bounded by ring buffers (EXP-042 Phase 1).

## D-002: Per-frame loop detector (EXP-042 Phase 2)

**Decision:** Replace `static thread_local std::map<uint32_t, uint32_t>` with
an instance member `pc_visit_count_` reset in `execute_method_internal()`
and saved/restored in `try_recursive_invoke()`.

**Rationale:** The thread-local counter leaked state across recursive
invocations, causing false-positive loop detection (BLOCKER-036 + EXP-042
Phase 2 bug). The instance member ensures each method invocation has a clean
counter.

**Threshold:** 50 000 visits per PC per frame. Allows legitimate loops
(color table iterations, message list processing) while catching real
`while(true){}` busy-waits.

## D-003: All opcode handlers advance pc_ (EXP-042 Phase 2)

**Decision:** Every opcode handler, even on error paths, MUST advance `pc_`
and return `true` (not `false`).

**Rationale:** Returning `false` without advancing `pc_` causes the
fetch-decode-execute loop to re-fetch the same opcode infinitely. The loop
detector eventually catches it, but only after 50 001 wasted iterations.
This was the root cause of `Util.castNonNull`, `FragmentActivity.onCreate`,
`ComponentActivity.onCreate`, `FlagSecureReason.attach` looping forever.

## D-004: Android framework objects as heap singletons (EXP-042 Phase 4)

**Decision:** `Context.getResources()` returns a heap-allocated object cached
in `api_singletons_[class_desc]`. The same Resources object is returned
across all calls in the APK's lifetime.

**Rationale:** Real Android guarantees `Context.getResources()` returns the
same `Resources` instance. Replicating this prevents heap growth from
repeated calls and matches expected identity semantics.

## D-005: Stub-only methods bypass recursive invoke (EXP-042 Phase 4)

**Decision:** Methods whose bytecode depends on Android system services we
cannot provide (e.g. `DynamiteModule.load` which busy-waits on Play
Services IPC) are short-circuited in `try_recursive_invoke` and routed to
the API bridge, which returns a controlled null.

**Rationale:** Real Android devices without Play Services throw
`LoadingException` from `DynamiteModule.load`, which callers catch and
recover from. Returning null matches the no-Play-Services device behavior
and lets Telegram continue past ML Kit initialization.

## D-006: Bounded ring buffers for all execution logs (EXP-042 Phase 1)

**Decision:** `instruction_traces`, `api_call_traces`, `completed_frames_`,
and `allocation_log_` are all bounded ring buffers with explicit caps
(2 000 / 5 000 / 100 / 1 000 entries respectively).

**Rationale:** Without caps, 100 M instructions × 5 KB per trace = 500 GB
of retained memory → kernel OOM-killer. With caps, peak RSS is bounded at
~440 MB regardless of instruction count.

## D-007: NO BLIND STUBS (EXP-043 rule)

**Decision:** Every stub must be documented in `docs/EXP043_STUB_DEBT.md`
with STUB-ID, class, method, reason, real Android behavior, current fake
behavior, and future implementation plan.

**Rationale:** Blind stubs (returning null/0 without documentation) hide
missing functionality and make future debugging harder. Documented stubs
form a clear migration path toward real Android compatibility.
