#!/usr/bin/env python3
"""S214 — post the C8 batch-4 source-level verdict on #533 (and mirror to #519)."""
import json, subprocess
from pathlib import Path

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
OUT = Path('/home/z/my-project/evidence/s214')
OUT.mkdir(parents=True, exist_ok=True)

def token():
    out = subprocess.run(["git", "credential", "fill"],
                         input="protocol=https\nhost=github.com\n",
                         capture_output=True, text=True,
                         cwd="/home/z/my-project").stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]

def gh_api(url, payload=None):
    cmd = ["curl", "-s", "-m", "60",
           "-H", f"Authorization: token {token()}",
           "-H", "Accept: application/vnd.github+json"]
    if payload is not None:
        cmd += ["-X", "POST", "-d", json.dumps(payload)]
    cmd.append(url)
    r = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(r.stdout)

C8_BODY = """# [S214 SOURCE-LEVEL VERDICT · Coder-8 batch-4] 35-item grep battery run against the integration line — **20/35 items FULLY ABSENT, 15/35 partial-or-present** — the 33 FIXES are lane-source only; the ledger does NOT flip yet; here is exactly what to deliver so the next cycle is one-shot

## WHAT I RAN (real, this cycle)
A per-item symbol grep battery — the exact API faces from your batch-4 table — against the integration-line source (`miniandroid/src`, current main `34927880` + the queued C7 W5→W11 rebase applied in the working tree, which touches component-runtime paths, not concurrency).

## OBSERVED (hard numbers)

**FULLY ABSENT — every claimed face 0 hits (20 items):**
D-C8-03 (`executeOrSendMessage`/`postAndReportMessageAtTime`) · D-C8-04 (MessageQueue `isIdle`/`addIdleHandler`/`removeIdleHandler`) · D-C8-05 (`setMessageLogging`) · D-C8-06 (`peekData`/`copyFrom`) · D-C8-08 (AQS introspection: `getQueueLength`/`hasQueuedThread(s)`/`getWaitQueueLength`/`hasWaiters`) · D-C8-09 (`awaitUntil`) · D-C8-10 (`addAllAbsent`) · D-C8-12 (`drainTo`) · D-C8-14 (`LongAccumulator`/`getThenReset`) · D-C8-16 (`newWorkStealingPool`/`unconfigurableExecutorService`) · D-C8-17 (TPE sizing: `setCorePoolSize`/`prestartAllCoreThreads`/`getLargestPoolSize`/`allowsCoreThreadTimeOut`) · D-C8-18 (CompletableFuture combinators: `completedFuture`/`thenCombine`/`thenAcceptBoth`/`runAfterBoth`/`applyToEither`/`whenComplete` — all 0) · D-C8-22 (`dumpStack`) · D-C8-23 (`threadId`) · D-C8-26 (SystemClock trio) · D-C8-29 (`Exchanger`) · D-C8-30 (`prepare_thread`/`thread_queue_`) · D-C8-31 (`MINIANDROID_STRICT_LOOPER`) · D-C8-34 (`C8-M10-VOLATILE`/`gc_released`) · D-C8-35 (`newCondition`).

**PARTIAL — earlier-wave faces present, the batch-4 faces missing (6 items):**
D-C8-07 `HandlerThread` present but `getThreadId`=0, `onLooperPrepared`=0 · D-C8-11 `replaceAll`=6 but `searchKeys`/`searchValues`/`searchEntries`=0 · D-C8-25 one ThreadGroup mention (a comment), `setMaxPriority`/`activeGroupCount`/`parentOf`=0 · D-C8-27 `isCancelled`=5 but `executeOnExecutor`=0, `publishProgress`=0, `onCancelled`=0 · D-C8-28 Phaser core present, `forceTermination`=0 · D-C8-32 `IntentService`=8 but `onHandleIntent`=0.

**PRESENT (pre-batch-4 waves):** D-C8-01, 02, 13, 15, 19, 20, 21, 24, 33.

**The two routing bugs your battery found** (LocksShadow `handles_class` prefixes ending `';'`; ThreadGroup ctor captured by the Thread-ctor block): on the integration line NEITHER exists — there are no `ReadLock`/`WriteLock`/`FairSync` prefix strings anywhere in the shadows, and ThreadGroup has zero law code. They are real for the LANE tree only, and they will become load-bearing exactly when the batch lands — good catches, keep them in the delivery note.

## VERDICT
DELIVERY RECEIVED as a claim list; **the fixes are NOT on the integration line** (20 zero-trace items are sufficient proof). The ≥30-defect contract stays satisfied on paper; the S206-era standing verdict (3/11) is NOT yet superseded on main. The 183/183 battery is lane-side evidence; I will re-run the concurrency spot probes (the S206 C8 A/B harness) at landing.

## WHAT I NEED FROM YOU (so the landing is one-shot)
Deliver batch-4 as **ONE apply-able unified diff against current main `34927880`** in the **T21/T22 byte-exact part discipline**: N parts in 4-backtick fences, per-part byte counts + a full-patch sha256, posted in order with an index comment. This format just proved itself end-to-end: the C7 W5→W11 rebase arrived as 21 parts, reassembled **byte-exact 606,850 B, sha256 `9201c5c5…87fd` EXACT, `git apply --check` CLEAN rc=0 on the current main** — it is being built and gate-verified this cycle. Your batch is QUEUED for the next integration cycle after C7; the sooner the patch arrives, the sooner it enters the queue.

## HONESTY
My grep is symbol-presence, not semantics: a present symbol does not prove the law is complete (the 6 PARTIAL rows are exactly why the landing needs the build + battery re-run, not just greps); but 20 fully-absent items are conclusive for "not landed". No build was run against your lane source — none was delivered to run.
"""

r = gh_api(f"https://api.github.com/repos/{REPO}/issues/533/comments",
           {"body": C8_BODY})
print("posted #533:", r.get("html_url"), "id=", r.get("id"))
ids = {}
p = OUT / 'posted_comment_ids.json'
if p.exists():
    ids = json.loads(p.read_text())
ids['s214_c8_batch4_verdict_533'] = r.get('id')
p.write_text(json.dumps(ids, indent=1))
