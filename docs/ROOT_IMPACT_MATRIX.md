# ROOT IMPACT MATRIX — MASTER CAMPAIGN 3/M8 (2026-09-10)

Per-root impact record. Loading-impact scale L0–L5:
L0 = blocks APK parse, L1 = blocks DEX load, L2 = blocks class linking,
L3 = blocks Java/Kotlin core execution, L4 = blocks framework path,
L5 = blocks Compose/scheduler/rendering. Evidence classes: LIVE > LOCAL >
UPSTREAM > CLAIM (a CLAIM row is a summary-vs-ledger reconciliation and
carries NO fix status).

| Root | Semantic law | Upstream source | MiniAndroid source | Trigger | Loading impact | Runtime/framework impact | Compose/UI impact | Affected APKs | Measured improvement | Proof |
|---|---|---|---|---|---|---|---|---|---|---|
| F-050a | Choreographer: thread-local singleton, FIFO frame callbacks, one shared monotonic frame time per vsync tick; the runtime pumps doFrame(J) at frame boundaries and drains resumptions on the same MessageQueue | AOSP frameworks/base Choreographer.java; AndroidX AndroidUiDispatcher.android.kt | src/framework/choreographer_shadow.{h,cpp}; src/runtime/execution_engine.cpp (pump_compose_frames/invoke_choreographer_do_frame; pumps at launch/frame-sequence/tap) | withFrameNanos parks; AndroidUiDispatcher posts J$c via Choreographer + Handler; nothing ever fired doFrame | L5 | Recomposer/AndroidUiDispatcher frame machinery now resumable; 0 doFrame in the whole 14.6 MB trace before | withFrameNanos can now resume; first-frame chain advanced to the Job-active frontier | dooz (any Compose APK) | 0→fired frame ticks in micro-proof; launch pump bound 8 frames | LIVE trace + f050 fixture 7/7 + 3-run |
| F-050c | AtomicLongFieldUpdater getAnd* / *AndGet: exact-name dispatch; getAndIncrement = getAndAdd(1) returns OLD | OpenJDK AtomicLongFieldUpdater.java / AtomicLong.java | src/framework/atomic_shadow.cpp (increment family) | any getAndIncrement through a field updater (kotlinx scheduler hot path) | L3→L5 | kotlinx.coroutines scheduler state machines (SegmentedList close-status, BufferedChannel counters) now advance | dooz Recomposer channel state no longer corrupts | dooz, any Kotlin coroutine app | sendersAndCloseStatus 0→-1 corruption GONE (0 occurrences post-fix); ISE eliminated | LIVE trace + f050 L1/L2 bands |
| F-050d | Boolean.TRUE/FALSE are non-null singleton boxed constants (R8 rewrites valueOf(true) into the sget) | OpenJDK Boolean.java | src/dex/dalvik_engine.cpp (sget synthesis, identity-cached) | sget-object Boolean.TRUE/FALSE in real DEX | L3 | boxed-boolean consumers (channel iterators, boxed predicates) unbox correctly | dooz channel iterator no longer false-exits → no cancelConsumed | dooz, any R8 app | "Channel was cancelled" CancellationException cascade eliminated (0 occurrences post-fix) | LIVE trace + f050 L3/L4 bands |
| F-050b | Throwable(String) stores detailMessage; getMessage() returns it | OpenJDK Throwable.java | src/dex/dalvik_engine.cpp (ctor bridge + [EXCEPTION] message log) | every DEX-constructed exception with a message | L3 | exception forensics unblocked (messages visible in [EXCEPTION] logs); no behavior change for passing apps | — | all APKs | f050-msg round-trip proven; campaign diagnostics upgraded | f050 L5 band |
| F-050e | §6 invariant count law 19 canonical / 21 visible | repo architectural invariant | miniandroid/tests/shadow_registry_invariant_test.cpp | registry growth check | — | registry ownership model preserved | — | — | 24 checks 0 failures | battery stage 34 |

## CLAIM-vs-LEDGER reconciliation (summary hygiene)

The session directive summary listed F-046..F-052 as fixed roots
(ActivityLifecycleCallbacks, Choreographer, AtomicLongFieldUpdater,
WeakReference, Arrays.copyOf, android.R.id.content/DecorView, coroutine
re-entry bound=4). Reconciliation against the repo (local + remote HEAD
6ff11eb2) at session start:

| Summary claim | Ledger truth at HEAD | Session outcome |
|---|---|---|
| F-046 ActivityLifecycleCallbacks | NOT FOUND in any HEAD; roadmap reserves F-046 for system-service completion (queued) | Claim rejected; ID stays reserved |
| F-047 Choreographer | NOT FOUND; roadmap reserves F-047 for bit methods | Choreographer root landed as F-050a instead |
| F-048 AtomicLongFieldUpdater getAndIncrement | NOT FOUND as a fix — but the BUG IS REAL at HEAD | Bug verified live and fixed as F-050c |
| F-049 WeakReference | NOT FOUND | No evidence hunted this session; stays open |
| F-050 Arrays.copyOf | NOT FOUND (ID was free) | ID F-050 consumed by the Choreographer family per ledger discipline |
| F-051 android.R.id.content/DecorView | NOT FOUND | Stays open |
| F-052 coroutine re-entry stub (active-depth bound=4) | NOT FOUND; no anti-loop patch of that shape exists in the engine | Nothing to audit — no such code exists; the campaign red line (no anti-loop patches) remains enforced |

Battery: 88/88 → **91/91** (3 new F-050 stages). dooz 3-run byte-identical
(SHA 31ddd4d5…, honest deterministic BLANK), tictactoe real-APK 3-run
rc=0 byte-identical.
