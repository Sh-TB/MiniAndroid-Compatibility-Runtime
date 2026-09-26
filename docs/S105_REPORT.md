# S105 REPORT — ROOT-010 WORKER-PARK-DEPTH EXECUTED TO L5

Head at close: see `git log`. All output text English (user directive).
Continuation contract honored: the S104-r3 NEXT ACTION (`Lsr;.run` worker
park/idle semantics) was executed to the full §16 completion standard, the
two companion sub-frontiers closed as downstream cascades, and the queue
advances to DECOR-LINKAGE.

---

## 1. ROOT ATTACKED

`Lsr;.run` worker spin / park-idle semantics (dooz v23; R8-obfuscated
kotlinx.coroutines `CoroutineScheduler.Worker.runLoop`) — the exact
S104-r3 NEXT ROOT.

## 2. BEFORE (honest re-measurement on S104-r3 HEAD `2063a255`)

```text
io.github.yamin8000.dooz v23: 17 errors (rc=1)
  - [HALT-LOOP] Infinite loop at PC=0xb2 in Lsr;.run (50001 visits,
    op 0x54 = iget-object nextParkedWorker) -> F084-HALT-RETURN
    VirtualMachineError -> 9 unwind rows -> onCreate APP BOUNDARY
  - Job double-completion ISE (Loj0;.T) -> onCreate APP BOUNDARY
  - navigation null-route NPE (Lox0;.a -> Leo;.V -> Lnb0;.n -> Lwo;.j
    -> Lfb1;.J) -> onCreate APP BOUNDARY
  - 24x [PARK-DRAIN] park depth=0 work_units=0; 0x [PARK-YIELD]
  - 2.2M+ interpreter instructions burned inside the spin
```

## 3. ROOT CAUSE

The `LockSupport.park` bridge checked the drained-body depth AFTER its own
synchronous queue drain had restored `park_drain_last_depth_` to 0 — the
enclosing worker body's depth (>= 1, set by `run_thread_start_body` for
the whole body) was destroyed before the quiescence check read it, so a
parked worker never suspended and spun park→scan→park until F084.

## 4. SOURCE LAW

kotlinx.coroutines `CoroutineScheduler.Worker`: on empty queue the worker
transitions PARKING and `LockSupport.parkNanos`; a parked worker consumes
no CPU and resumes on unpark (task arrival) or timeout (kotlinx-coroutines
`CoroutineScheduler.kt`; AOSP libcore `LockSupport.park` contract).
Serialized-engine counterpart: park in a drained body with zero work =
deterministic suspension; the body re-drains at the NEXT scheduler
boundary (one bounded rescan per clock tick).

## 5. FIX (law-level, one shared semantic)

1. Save/restore the enclosing drain depth across the park drain (the same
   discipline `run_thread_start_body` applies to the identical variable).
2. Register the parked body due at `now + 1ms` — exactly one park/rescan
   per boundary (0-wake re-pops up to the 8-slice cap in the same
   boundary; observed `resumed=8`, `parks=9`).

No class-name special casing; every parker (coroutines, ArrayBlockingQueue
take, FutureTask.get) shares the law.

## 6. AFTER

```text
io.github.yamin8000.dooz v23: 6 errors, 3/3 identical
  - F084/halt rows: 0; APP BOUNDARY rows: 0; PARK-YIELD fires (depth=1)
  - Job ISE (Loj0;.T): 0 rows  (downstream cascade, closed)
  - nav NPE (Lox0;.a family): 0 rows (chain moved deeper, then closed)
  - remaining 6 rows = EXC-UNWIND bookkeeping of ONE handled
    CancellationException (La; extends j.u.c.CancellationException;
    caught by typed handler at Llo;.B) — Fatal: NO
  - instruction burn in the spin: 2.2M+ -> ~0.1M (22x less work to the
    same end state); setContentView + deferred attach+measure executes
  - screenshot SHA 59fdbfcd60b86a23 x3 (the recorded blank-canvas SHA;
    runtime progress = YES, visual progress = NOT YET PROVEN — honest)
dooz_23_toplevel (same root, independent proof): 17 + HALT -> 6, 3/3
```

## 7. PROBE

`fixtures/s105_park_probe/` + `scripts/s105_park_probe_check.sh`.
Post-fix: ALL PASS (8/8) x3 — active→idle-park→one-rescan-per-boundary→
wake→task-exactly-once→terminate. Pre-fix binary: rc=1 + HALT-LOOP +
frozen screen (the probe DETECTS the spin, not just the error drop).

## 8. FAN-OUT + REGRESSION

```text
bytecode scan:  4/42 corpus APKs carry LockSupport (3 timed park)
execution:      dooz x2 affected+fixed; stopwatch/bouncy controls
                byte-identical behavior before/after (park not on their
                active paths — presence != fan-out, no inflation)
battery:        BATTERY GATE ALL PASS (105 stages, rc=0) on final tree
toolchain:      ecj/r8/d8/aapt2 restored from container remnants
                (hash-verified vs S74/S104-r3 records; EXT-01 fixture
                re-fetched, APK SHA 009b4671 matches the record)
```

## 9. SECOND ROOT THIS WAVE — R-005 DECOR-LINKAGE (auto-continue per §9)

Executed immediately after ROOT-010 per the continuation contract.

```text
ROOT:    Window.setContentView(View) silent no-op + global decor singleton
         cross-activity leak (ballbreak v1.8.1, AppCompat sub-decor family)
LAW:     PhoneWindow.setContentView installs INSIDE the decor hierarchy;
         createSubDecor's mWindow.setContentView(subDecor) must make the
         sub-decor reachable from getDecorView() (WindowDecorActionBar.init
         walks decor_content_parent/action_bar from the DecorView root);
         ONE DecorView per Window per Activity (PhoneWindow.mDecor)
FIX:     Window.setContentView engine law (attach under the current
         activity's decor, [R005-DECOR] row) + per-activity decor map
BEFORE:  ISE "Can't make a decor toolbar out of null" -> GameActivity
         onCreate APP BOUNDARY; Status: PARTIAL SUCCESS
AFTER:   Status: SUCCESS, Errors: 0, 3/3 runs; decor-root walk answers
         FOUND (decor_content_parent, action_bar); 0 APP BOUNDARY rows
3-RUN:   SUCCESS x3 deterministic
REGRESS: battery 105/105 ALL PASS (rc=0); dooz 6 / bouncy 16 / unote 0
         controls unchanged
APK:     de.georgsieber.ballbreak v1.8.1 vc10 (SHA e6e9f372… matches the
         S84 registry record; re-fetched after corpus cleanup)
TICKET:  #348 CLOSED; GR-08 REPRODUCED -> SOLVED-L5
```

## 10. NEXT EXACT ACTION

**Compose host/recomposition frontier** (S104-r3 GR-07 continuation;
now the first unresolved item in the S105 chain): the dooz post-fix trace
shows the composition machinery running (setContentView + deferred
attach+measure executes; remaining 6 error rows are the EXC-UNWIND
bookkeeping of ONE handled kotlinx CancellationException caught at
Llo;.B). First divergence to trace: the handled-cancellation unwind
accounting (caught exceptions recorded as EXC-UNCAUGHT-TOP rows) and the
first non-bookkeeping compose divergence past it — walk the chain APK
bytecode → receiver identity → framework API → state producer → scheduler
→ View/layout → rendering until the first incorrect engine semantic.
