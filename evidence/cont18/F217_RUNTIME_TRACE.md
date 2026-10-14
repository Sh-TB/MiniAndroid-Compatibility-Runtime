# F-NEW-217 T-01 — Waiter-Resume Divergence Formally Reproduced at Current Binary

**Binary:** aed46450c103f2ea (rebuilt from HEAD e99c2fbd; 5 canonical anchors ×3 byte-identical zero-drift)
**Probe:** `fixtures/fnew217_probe` → `upload/fnew217_probe.apk` (build: `scripts/cont18_f217_probe_build.sh`)
**Dependencies:** REAL kotlinx-coroutines-core-jvm **1.9.0** (the exact dooz23 pin) + atomicfu-jvm 0.24.0 + kotlin-stdlib 2.0.20, kotlinc 2.0.20, aapt2+D8 (real toolchain). Non-R8 build — full kotlinx names visible.
**Runs:** `run/cont18/f217_t01_run1..9` (run1/7/8/9 clean ×3 determinism; run2..6 trace-instrumented)

## Reproduction result (3/3 byte-identical)

| Face | Result | Observable |
|---|---|---|
| B — uncontended `withLock` ×2 | **PASS** | `n=2, isLocked=false` — acquire/release CAS + permit bookkeeping + FU laws CORRECT |
| A — Mutex waiter-resume | **FAIL** | `seq=B-try;main-unlock;` — B parked, main's release completed, **B never acquired**; `isLocked=true` after unlock |
| C — Semaphore waiter-resume | **FAIL** | `seq=main-release;` — same starvation shape |

This matches F-NEW-217's recorded spin-state signature exactly: mutex locked-by-nobody (permits consumed), waiter queued, upstream CAS paths all resolving — i.e. the state at the droidify F084 spin (owner=NO_OWNER, `_availablePermits$volatile=0`, head≠null).

## Machine-proven chain (all facts trace-backed, runs 2/5/6)

1. B suspends at `m.lock()` → `CancellableContinuationImpl.trySuspend` (×51) → waiter queued in `SemaphoreAndMutexImpl` (kotlinx 1.9 MutexImpl IS SemaphoreAndMutexImpl-backed).
2. main `m.unlock()` → `release()` → permit CAS OK (FU `_availablePermits$volatile` bound; FACE B proves bookkeeping) → `tryResumeAcquire` → `CancellableContinuationImpl.tryResume` on the parked waiter (state SUSPENDED=0x3FFFFFFF observed) → **token SUCCESS** → `completeResume` → `dispatchResume(mode=1)`.
3. `DispatchedTaskKt.dispatch(task, 1)`:
   - pc=28 `instance-of` delegate → pc=30 `if-eqz` → **direct-resume arm taken** (delegate = the app coroutine state machine, e.g. obj#264 = `Lcom/probe/f217/MainActivity$onCreate$3$1;` — NOT a `DispatchedContinuation`, so this branch is per-contract);
   - `CoroutineDispatcher.isDispatchNeeded` ×0 on this chain (vs ×2 on other continuations' chains — their delegates ARE DispatchedContinuations);
   - `resume(task, delegate, false)` → `BaseContinuationImpl.resumeWith` (×15) → the resumed state machine's `invokeSuspend` **executed and returned COROUTINE_SUSPENDED**.
4. **THE DIVERGENCE:** the resumed coroutine's `invokeSuspend` ran on the resumed stack, but its side effects never landed in the observable state (`C-try;` never appended after resume; `B-acquired;` never appended at all) and the waiter never completed its `withLock`. A resumed continuation re-suspended (COROUTINE_SUSPENDED) **without any registered wakeup carrying the permit back** — the continuation re-enters its suspend point and parks again while the permit it was granted is gone. Result: mutex permanently `isLocked=true`, `jobB.join()` suspends forever, `joinBlocking` poll-spins (`ThreadSafeHeap.isEmpty` ×**50,063** — the recorded F084 spin's engine-side face), `withTimeoutOrNull(5000)` fires → `TimeoutCancellationException` unwinds (crash.log ×2 EXC-UNWIND).

**Law statement (upstream kotlinx 1.9.0 contract, `DispatchedTaskKt.dispatch` + `SemaphoreAndMutexImpl.release` + `BlockingCoroutine.joinBlocking`):**
a waiter granted a permit by `release()` must become runnable at the NEXT event-loop boundary; `joinBlocking` parks only when the loop has no pending work and MUST observe grants that arrive while it polls. MiniAndroid violates this: the direct-arm resume enqueues the waiter's completion, but the parked `joinBlocking` poll loop **never observes it** — the grant is delivered only at a much later unrelated boundary.

## CORRECTED ROOT (run10 decisive evidence)

The waiter's resume is **delivered LATE, not never** — and only by an unrelated boundary:

- `$2$jobB$1.invokeSuspend` (B's body) executed **TWICE** (pc=0 ×2):
  - entry 1: label 0 → appends `"B-try;"` → `m.lock()` suspends (waiter parked);
  - entry 2 (the grant): label 1 → **appends `"B-acquired;"` to the SAME StringBuilder (obj#131)** → `m.unlock()` → returns (completed to pc=62).
- But the FACE A FAIL line (`seq=B-try;main-unlock;|isLocked=true`) was rendered BEFORE entry 2: `isLocked=true` was still true at capture, proving entry 2 ran after the timeout teardown, not before it.
- While the grant sat undelivered, the engine's own loop machinery was polling the whole time: `EventLoopImplBase.processNextEvent` ×4255, `.dequeue` ×2714, `.getNextTime` ×6972, `ThreadSafeHeap.isEmpty` ×50,063 (the F084-spin face), and never dispatched the pending waiter completion.
- The direct-resume arm itself (instance-of → resume(task, delegate, false) → BaseContinuationImpl.resumeWith) is per-contract and NOT the bug.

**Engine law violated (generic):** a resume grant produced while the main thread is parked inside `joinBlocking`'s poll loop must wake/re-drain the loop at the immediate next boundary (the unpark law). MiniAndroid's joinBlocking drain (the R-NEW-345 law site, dalvik_engine.cpp ~23836 "joinBlocking spin — dooz23 runBlocking") covers worker-thread park/wake but NOT the main-thread parked-poll case for direct-arm resumes — the waiter completion sits queued until an unrelated boundary (the withTimeout virtual-time tick / a frame boundary) drains it. In the droidify spin shape this manifests as: unlock's retry loop polls waiter progress that never arrives within the observation window → F084 halt; and when the grant finally lands after an app-level timeout unwind re-runs release/finally, the permit bookkeeping breaks → the recorded `release ISE` family.

## Secondary finding (documented, not the primary root)

`AtomicLongFieldUpdater.get` REC-MISS inside `LockFreeTaskQueueCore.addLast` in **some** runs (run2) while correctly bound (`[ATOMIC-DIAG] bound=_state$volatile`) in others (run3) — non-deterministic FU-binding loss in the same subsystem. FACE results are FAIL in both variants, so the primary divergence is FU-independent. Registry F-NEW-217's historic note "AtomicReferenceFieldUpdater.newUpdater REC-MISS at MutexImpl.<clinit> (fallback path taken)" is consistent with this instability.

## Fix surface (generic; NO kotlinx/app-specific interception)

The `joinBlocking` parked-poll drain law (R-NEW-345 extension): when the main thread's joinBlocking poll loop is active and a resume grant is enqueued (direct-arm or dispatcher-arm), the loop must drain it at the immediate next poll iteration instead of parking/spinning past it. Fix lands at the engine's joinBlocking law site (dalvik_engine.cpp ~23836) + the resume-enqueue hook that marks the loop dirty. Expected probe transition: FACE A/C `seq` complete (`B-acquired;`/`C-acquired;` present, `isLocked=false`), no timeout unwind, no 50k poll-spin; anchors byte-identical.

## Regression guards for the fix

- 5 canonical anchors ×3 (dooz d602648e8e401895, microtimer da73010a37dd0189, unote 4f1a9e4e8f64fae8, chess b5a7a35d5fe0564b, opencalc a976d2f9fb675cb3) — captured at aed46450c103f2ea this session.
- negatives 19/19, skill 13/13, gate A probe.
- This probe must flip A/C to PASS while B stays PASS and anchors stay byte-identical.
