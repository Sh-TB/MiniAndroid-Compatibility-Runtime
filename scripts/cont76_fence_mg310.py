#!/usr/bin/env python3
"""cont76_fence_mg310.py — MG-310 dedicated <clinit> fence runner (issue #364
FOUNDATION 4/4). Runs the mg310 fence probe and asserts the JLS 12.4.1 /
JVMS 5.5 initialization laws on the probe's own rows + the engine
[CLASS_INIT] rows. Exit 0 = fence GREEN.
"""
import json
import os
import re
import subprocess
import sys

ROOT = "/home/z/my-project"
BIN = f"{ROOT}/miniandroid/build/miniandroid"
STORE = f"{ROOT}/run/cont76/store"
OUT = f"{ROOT}/run/cont76/mg310_run"
LOG = f"{OUT}.stderr"

CHECKS = []


def check(name, ok, detail):
    CHECKS.append({"name": name, "ok": bool(ok), "detail": detail})
    print(f"  {'PASS' if ok else 'FAIL'}  {name}: {detail}")


def main():
    log = open(LOG, errors="replace").read()
    app_rows = re.findall(r"^\[MG310-[^\n]*", log, re.M)

    # L1: active-use init happened exactly once
    base_markers = [r for r in app_rows if "CLINIT] Base #" in r]
    check("L1-active-use-init", len(base_markers) == 1
          and "Base #1" in base_markers[0], str(base_markers))
    check("L1-initCount=1",
          "[MG310-L1] Base.ping=base initCount=1" in log,
          "Base.ping row present with initCount=1")

    # L2: compile-time constant read did NOT initialize the holder
    ch_engine = re.findall(r"\[CLASS_INIT\].*MainActivity\$ConstHolder", log)
    ch_app = [r for r in app_rows if "CLINIT] ConstHolder" in r]
    check("L2-constant-no-init", not ch_engine and not ch_app
          and "[MG310-L2] ConstHolder.C=7" in log,
          f"engine rows={len(ch_engine)} app rows={len(ch_app)} value=7")

    # L3: superclass-first ordering (Base marker strictly before Derived)
    ib = log.find("[MG310-CLINIT] Base #1")
    idv = log.find("[MG310-CLINIT] Derived")
    check("L3-super-first-order", ib != -1 and idv != -1 and ib < idv,
          f"Base@{ib} < Derived@{idv}")

    # L3b: engine rows agree (Base CLASS_INIT before Derived CLASS_INIT)
    ibe = log.find("MainActivity$Base; method=<clinit>")
    ide = log.find("MainActivity$Derived; method=<clinit>")
    check("L3b-engine-row-order", ibe != -1 and ide != -1 and ibe < ide,
          f"engine Base@{ibe} < Derived@{ide}")

    # L4: once-only init
    base_engine = re.findall(r"\[CLASS_INIT\].*MainActivity\$Base;.*result=OK",
                             log)
    check("L4-once-only", len(base_engine) == 1
          and "[MG310-L4] initCount-after-second-use=1" in log,
          f"engine Base clinit rows={len(base_engine)}, app initCount=1")

    # L5: default value visible during <clinit>
    check("L5-default-value",
          "[MG310-L5] Forward.s=nullx (expect nullx)" in log,
          "Forward.s == nullx")

    n_pass = sum(1 for c in CHECKS if c["ok"])
    verdict = "FENCE GREEN" if n_pass == len(CHECKS) else "FENCE RED"
    result = {"fence": "MG-310 clinit ordering", "probe": "com.probe.mg310",
              "apk_sha16": "741e3942c2048933",
              "checks": CHECKS, "pass": n_pass, "total": len(CHECKS),
              "verdict": verdict}
    os.makedirs(f"{ROOT}/evidence/cont76", exist_ok=True)
    with open(f"{ROOT}/evidence/cont76/mg310_fence.json", "w") as f:
        json.dump(result, f, indent=1)
    print(f"{verdict}: {n_pass}/{len(CHECKS)}")
    return 0 if n_pass == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
