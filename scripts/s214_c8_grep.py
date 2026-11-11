#!/usr/bin/env python3
"""S214: C8 batch-4 per-item symbol grep battery against the integration-line source."""
import subprocess, os

REPO_SRC = "/home/z/my-project/miniandroid/src"
FILES = [
    "dex/dalvik_engine.cpp", "dex/dalvik_engine.h",
    "framework/android_shadows.cpp", "framework/android_shadows.h",
]

ITEMS = [
    ("D-C8-01", ["postAtTime"]),
    ("D-C8-02", ["sendMessageAtFrontOfQueue"]),
    ("D-C8-03", ["executeOrSendMessage", "postAndReportMessageAtTime"]),
    ("D-C8-04", ["addIdleHandler", "removeIdleHandler", "isIdle"]),
    ("D-C8-05", ["setMessageLogging"]),
    ("D-C8-06", ["peekData", "copyFrom"]),
    ("D-C8-07", ["HandlerThread", "getThreadId", "onLooperPrepared", "quitSafely"]),
    ("D-C8-08", ["getQueueLength", "hasQueuedThread", "getWaitQueueLength", "hasWaiters"]),
    ("D-C8-09", ["awaitUntil"]),
    ("D-C8-10", ["addAllAbsent"]),
    ("D-C8-11", ["replaceAll", "searchKeys", "searchValues", "searchEntries"]),
    ("D-C8-12", ["drainTo"]),
    ("D-C8-13", ["PriorityBlockingQueue", "DelayQueue"]),
    ("D-C8-14", ["LongAccumulator", "getThenReset"]),
    ("D-C8-15", ["Semaphore"]),
    ("D-C8-16", ["newWorkStealingPool", "unconfigurableExecutorService"]),
    ("D-C8-17", ["setCorePoolSize", "prestartAllCoreThreads", "getLargestPoolSize", "allowsCoreThreadTimeOut"]),
    ("D-C8-18", ["completedFuture", "thenCombine", "thenAcceptBoth", "runAfterBoth", "applyToEither", "whenComplete"]),
    ("D-C8-19", ["invokeAll", "invokeAny"]),
    ("D-C8-20", ["scheduledExecutionTime"]),
    ("D-C8-21", ["activeCount", "enumerate"]),
    ("D-C8-22", ["dumpStack"]),
    ("D-C8-23", ["threadId"]),
    ("D-C8-24", ["UnsupportedOperationException"]),
    ("D-C8-25", ["ThreadGroup", "setMaxPriority", "activeGroupCount", "parentOf"]),
    ("D-C8-26", ["currentThreadTimeMicro", "currentGloballyTimeMillis", "currentGloballyTimeNanos"]),
    ("D-C8-27", ["executeOnExecutor", "publishProgress", "onCancelled", "isCancelled"]),
    ("D-C8-28", ["Phaser", "arriveAndDeregister", "awaitAdvance", "forceTermination", "bulkRegister"]),
    ("D-C8-29", ["Exchanger"]),
    ("D-C8-30", ["prepare_thread", "thread_queue_"]),
    ("D-C8-31", ["MINIANDROID_STRICT_LOOPER"]),
    ("D-C8-32", ["IntentService", "onHandleIntent"]),
    ("D-C8-33", ["WorkManager"]),
    ("D-C8-34", ["C8-M10-VOLATILE", "gc_released"]),
    ("D-C8-35", ["newCondition"]),
]

def grep(pattern):
    r = subprocess.run(["rg", "-c", pattern] + [os.path.join(REPO_SRC, f) for f in FILES],
                       capture_output=True, text=True)
    lines = []
    for ln in r.stdout.splitlines():
        if ":" in ln:
            path, cnt = ln.rsplit(":", 1)
            lines.append(f"{os.path.basename(path)}:{cnt}")
    return lines

print(f"grep target: {REPO_SRC} (current integration line = main 34927880 + C7 patch applied)")
present = absent = 0
for item, syms in ITEMS:
    results = []
    for s in syms:
        g = grep(s)
        total = sum(int(x.split(":")[1]) for x in g)
        results.append(f"{s}={total}({','.join(g) if g else '-'})")
    hit = sum(int(r.split("=")[1].split("(")[0]) for r in results)
    tag = "PRESENT" if hit > 0 else "ABSENT"
    if hit > 0:
        present += 1
    else:
        absent += 1
    print(f"{item} [{tag}] " + " | ".join(results))
print(f"\ntally: {present} items with >=1 symbol on integration line, {absent} fully ABSENT")
