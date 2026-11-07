#!/usr/bin/env python3
"""S192 [C8] — CODER 8 WAVE 9 — androguard-driven concurrency-surface decode
(defects 161–180). Same method as S191 (waves 8): static decode of the
canonical APK corpus → app contract → evidence-backed defect list.

Wave-9 additions to the scan window (carried forward from the S191 ledger):
  - Ljava/util/concurrent/LinkedBlockingDeque (F-C8-158 carried)
  - Looper quit/quitSafely + MessageQueue deeper (wave-7 pending)
  - ExecutorService invokeAll/invokeAny (wave-7 pending)
  - Timer/TimerTask surface detail + CountDownTimer
  - Thread.UncaughtExceptionHandler family
  - Phaser / CompletableFuture deeper / FutureTask cancel
  - ThreadLocal.withInitial / InheritableThreadLocal
  - Atomic*FieldUpdater family (83 sites / 4 APKs in S191 — never enumerated)

Output: evidence/s192_c8/S192_C8_CONCURRENCY_DECODE.json
"""
import glob
import json
import os
import re
import sys

from loguru import logger
logger.remove()

from androguard.misc import AnalyzeAPK

APKS = sorted(glob.glob("/home/z/my-project/upload/canonical_apks/*.apk"))
OUT = "/home/z/my-project/work/miniandroid/evidence/s192_c8/S192_C8_CONCURRENCY_DECODE.json"

CONC = re.compile(
    r"^(?:"
    r"Landroid/os/(?:Handler|Looper|Message|MessageQueue|HandlerThread|"
    r"SystemClock|CountDownTimer|AsyncTask|Messenger|Process);"
    r"|Ljava/lang/(?:Thread|Runnable|ThreadLocal|InheritableThreadLocal|"
    r"ThreadGroup|Object|InterruptedException|IllegalMonitorStateException|"
    r"Thread\$UncaughtExceptionHandler|Thread\$State|AutoCloseable);"
    r"|Ljava/util/concurrent/.+"
    r"|Ljava/util/(?:Timer|TimerTask|concurrent/.+);"
    r"|Lkotlin/concurrent/.+"
    r"|Lkotlinx/coroutines/.+"
    r")$")

INVOKE_RE = re.compile(r"(L[^;]+;)->([^:\s(]+)")


def decode(apk):
    a, d, dx = AnalyzeAPK(apk)
    refs = {}
    monitors = 0
    sync_methods = 0
    total_invokes = 0
    classes_total = set()
    pkg = a.get_package()

    for meth_analysis in dx.get_methods():
        if meth_analysis.is_external():
            continue
        enc = meth_analysis.get_method()
        code = enc.get_code() if enc is not None else None
        if code is None:
            continue
        if enc.get_access_flags() & 0x100:
            sync_methods += 1
        cls = "L" + enc.get_class_name().replace(".", "/") + ";"
        classes_total.add(cls)
        for ins in enc.get_instructions():
            name = ins.get_name()
            if name == "monitor-enter":
                monitors += 1
                continue
            if name == "monitor-exit":
                continue
            if not name.startswith("invoke"):
                continue
            out = ins.get_output()
            mm = INVOKE_RE.search(out)
            if not mm:
                continue
            tcls, tmet = mm.group(1), mm.group(2)
            if not CONC.match(tcls):
                continue
            total_invokes += 1
            refs.setdefault(tcls, {}).setdefault(tmet, 0)
            refs[tcls][tmet] += 1

    return {
        "apk": os.path.basename(apk),
        "pkg": pkg,
        "app_classes": len(classes_total),
        "conc_invoke_sites": total_invokes,
        "monitor_enter": monitors,
        "synchronized_methods": sync_methods,
        "refs": {c: dict(sorted(v.items(), key=lambda kv: -kv[1]))
                 for c, v in sorted(refs.items())},
    }


def main():
    per_apk = []
    for apk in APKS:
        try:
            r = decode(apk)
            per_apk.append(r)
            print(f"[OK] {r['apk']:42s} conc_sites={r['conc_invoke_sites']:5d} "
                  f"monitors={r['monitor_enter']:4d} sync_m={r['synchronized_methods']:3d} "
                  f"classes={r['app_classes']}", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"[FAIL] {apk}: {e}", file=sys.stderr)
            per_apk.append({"apk": os.path.basename(apk), "error": str(e)})

    agg = {}
    for r in per_apk:
        if "error" in r:
            continue
        for c, meths in r["refs"].items():
            for met, n in meths.items():
                e = agg.setdefault(c, {}).setdefault(met, {"apks": [], "total": 0})
                e["apks"].append(r["apk"])
                e["total"] += n

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump({"per_apk": per_apk, "aggregate": agg}, f, indent=1, sort_keys=True)

    print("\n=== TOP consumed concurrency (class · method · #apks · total) ===")
    flat = []
    for c, meths in agg.items():
        for met, e in meths.items():
            flat.append((len(set(e["apks"])), e["total"], c, met))
    flat.sort(reverse=True)
    for napks, tot, c, met in flat[:100]:
        print(f"{napks} apk {tot:5d}x  {c}.{met}")
    print(f"\nunique (class,method) pairs in Coder-8 domain: {len(flat)}")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
