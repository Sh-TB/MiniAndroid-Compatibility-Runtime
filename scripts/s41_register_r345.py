#!/usr/bin/env python3
"""S41: register R-NEW-345 (runBlocking/BlockingCoroutine livelock family)
and refresh R-NEW-344 (dooz first-frame blank — refined by S41 forensics)."""
import json

REG = '/home/z/my-project/root_registry.json'
reg = json.load(open(REG))
roots = reg['roots'] if isinstance(reg, dict) else reg
ids = [r.get('id') for r in roots]

R345 = {
    "id": "R-NEW-345",
    "title": "runBlocking/BlockingCoroutine joinBlocking livelock — kotlinx event-loop state machine + worker threads never observed their own work; HALT-LOOP destroyed two coroutine frames; dooz theme-load never completed",
    "status": "implemented",
    "priority": "P0",
    "fg": True,
    "app": "io.github.yamin8000.dooz_23 (dooz, PRIORITY-1) — general: any app calling runBlocking at startup (ViewModel init, DataStore reads)",
    "observed": "S41 reruns (run_a/run_b/run_c with forensic env): dooz23 MainActivity.onCreate runBlocking { theme = settings.getTheme() } (GitHub-first: yamin8000/Dooz master MainActivity.kt L41) NEVER completed. joinBlocking spin = 200k+ F074 lines on Ljf;(BlockingEventLoop)/Lhf;(BlockingCoroutine) receivers, ZERO real work; ended ONLY via 2x [HALT-LOOP] frame destruction (Lqq0;.a @242304, Lvs0;.O @442352 — 50k visits each). After the kills the composition machinery started but produced an EMPTY content composition (root-only LayoutNode tree, 0 content nodes, blank frame) = the downstream face of R-NEW-344. DataStoreImpl (Lh8;) 0 returns; zero Thread.start dispatches; zero scheduler classes executed.",
    "root_cause": "FOUR stacked generic gaps (all fixed): (1) SUPER-DISPATCH IDENTITY: execute_invoke_super appended a '<super>' marker to the declaring class before bridge_to_api, so framework-ancestor super-calls (kotlinx Worker.start{ super.start() } -> Thread.start) never reached ThreadShadow — no worker ever ran. (2) Thread subclasses with NO Runnable ctor target were silent no-ops at ThreadShadow.start (F-THREAD-TICK only handled recorded runnables). (3) LockSupport.park* resolved to silent void: the only yield point never drained cross-queue work, and parked worker loops spun at full interpreter speed (fix_r3: 2.8M instructions inside Lsr;.run). (4) Unsafe get-and-set family MISSING (getAndAddLong/getAndAddInt/getAndSetObject/getAndSetInt/getAndSetLong/compareAndSwapLong) — kotlinx atomicfu compiles AtomicLong/AtomicReference state machines (EventLoopBase useCount/shared packed long, ConcurrentLinkedQueue head/tail unlink) to DIRECT Unsafe ops; missing ops answered silent garbage so the event loop never observed its own enqueued tasks.",
    "fix": "Four generic laws (no class-name hacks): (a) SUPER-DISPATCH IDENTITY — bridge_to_api receives the CLEAN declaring class; '<super>' kept only in the api_trace log. (b) THREAD SELF-RUN — ThreadShadow.start with no recorded Runnable queues a SELF-run (thread,thread); the drain invokes the receiver's own REAL DEX run() (AOSP Thread.start virtual-dispatch law). (c) PARK-DRAIN — LockSupport.park/parkNanos/parkUntil = deterministic yield point: bounded drain (main MessageQueue runnables via REAL DEX run(), Choreographer due doFrame callbacks, pending Thread starts), reentrancy-guarded (depth<=3); unpark = no-op; park at drain depth>=1 with zero work sets park_yield_pending_ -> [PARK-YIELD] graceful frame-chain suspension at the drain boundary (parked-worker law; main-thread park at depth 0 NEVER yields — joinBlocking must re-check isCompleted). (d) UNSAFE FAMILY CLOSURE — compareAndSwapLong/getAndAddLong/getAndAddInt/getAndSetObject/getAndSetInt/getAndSetLong implemented over the SAME heap store as iput/iget (R-NEW-337 one-store law).",
    "evidence": "/tmp/s41/: fix_r1 (park-drain fired, work_units=0 — pre-super-fix), fix_r2 (super-fix, still spin — workers never created), fix_r3 (self-run law: 3x [THREAD-START] Lsr; workers, REAL DEX run() executed, 2.8M ins in worker loop), fix_r4 (FULL PIPELINE COMPLETED: 3x [PARK-YIELD], 0 HALT-LOOP, runBlocking completed, DataStore read REACHED (13 NPEs at Lot;.a/Liu;.d = NEW frontier R-NEW-346), run finished <280s, status SUCCESS). Upstream: kotlinx.coroutines BlockingCoroutine.joinBlocking + EventLoopImplBase (Lo30; fields _queue$volatile@160/_delayed$volatile@168/_isCompleted$volatile@176 proven via [R337-UNSAFE] clinit offsets), dooz sources fetched from github.com/yamin8000/Dooz master.",
    "discovered": "S41",
    "fixed_in": "S41",
    "next": "R-NEW-346: DataStore read NPE chain (Lot;.a invoke_pc=0x18/0x9, Liu;.d — 13 EXC-UNCAUGHT-TOP, non-fatal) — the datastore actor's file-read path hits null; then R-NEW-344 content composition (still root-only tree).",
    "impact": "dooz23: from NEVER-COMPLETING run + 2 destroyed frames + empty composition to full startup pipeline in <280s with clean yields. Generic: every runBlocking caller (ViewModel init, DataStore, settings loads) and every kotlinx scheduler worker benefits."
}

if 'R-NEW-345' not in ids:
    roots.append(R345)
else:
    for i, r in enumerate(roots):
        if r.get('id') == 'R-NEW-345':
            roots[i] = R345

# refresh R-NEW-344
for r in roots:
    if r.get('id') == 'R-NEW-344':
        r['observed'] = (
            "S41 REFINED: r354 await-suspension picture was the DOWNSTREAM face. "
            "True chain: MainActivity.onCreate runBlocking{settings.getTheme()} livelocked (R-NEW-345) "
            "-> 2x HALT-LOOP destroyed coroutine frames -> composition machinery started with the app's "
            "startup sequence corrupted -> composeInitial composed a ROOT-ONLY tree (ComposeView Lho; view "
            "attached, AndroidComposeView Lt4; view=1447 constructed, ComposerImpl Lxk0; active at trace end, "
            "content lambda never produced nodes, 0 nonwhite pixels). Upstream law (compose 1.6.7 exact sources "
            "fetched from Google Maven): AbstractComposeView.Content() = content?.invoke() — empty when content "
            "unset; composeInitial runs synchronously on the setContent caller thread and must produce nodes "
            "BEFORE any frame."
        )
        r['status'] = "OBSERVED-FAIL"
        r['root_cause_hypothesis'] = (
            "R-NEW-345 (runBlocking livelock family) fixed in S41; next blocker = R-NEW-346 DataStore NPE chain, "
            "then re-probe the content composition path (whether the app composable lambda is invoked with a "
            "non-null content holder and whether ComposerImpl.start/end pairs complete)."
        )

reg['roots'] = roots
json.dump(reg, open(REG, 'w'), indent=1, ensure_ascii=False)
print("registered R-NEW-345; refreshed R-NEW-344; total roots:", len(roots))
