#!/usr/bin/env python3
"""s156_p4_perfops.py — S156-P4 throughput-surgery verification: PERF-OPS A/B.

Measures the per-opcode tick cost of the interpreter on the dooz E5 protocol
(fresh store, --trace, real-dalvik) with MINIANDROID_PERF_PHASES=1, and
compares iget-object ticks-per-call against the S156 phase-3 baseline
(7,064,565 calls @ ~2,455 ticks/call on binary a793f134, same VM, same
rdtsc clock). The surgery (env-gates static-cached + eager args-copy removed
+ per-instruction operand reserve gated) is byte-inert by construction; the
expected effect is ticks-per-call DROP on the same hardware.

Usage: python3 scripts/s156_p4_perfops.py
Writes: evidence/s156_record_loop/S156_P4_PERFOPS.json + console table.
"""
import json
import os
import re
import subprocess
import sys
import time

BASE = "/home/z/my-project"
BIN = f"{BASE}/miniandroid/build/miniandroid"
APK = f"{BASE}/upload/canonical_apks/io.github.yamin8000.dooz_23.apk"
OUT = f"{BASE}/run/s156_p4"
EVDIR = f"{BASE}/evidence/s156_record_loop"
BASELINE_TPC = 2455.0          # S156-P3: iget-object ~2,455 ticks/call
BASELINE_CALLS = 7064565       # 120s window on the pin binary, same VM

def sh(cmd, **kw):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, **kw)

def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(EVDIR, exist_ok=True)
    store = f"{OUT}/store_dooz"
    if not os.path.isdir(store):
        r = sh(f"{BIN} install {APK} --data-root {store}")
        if r.returncode != 0:
            print("INSTALL FAIL", r.stderr[-300:]); sys.exit(1)
    rundir = f"{OUT}/perfops_run"
    subprocess.run(["rm", "-rf", rundir], check=False)
    os.makedirs(rundir, exist_ok=True)
    env = dict(os.environ)
    env["MINIANDROID_PERF_PHASES"] = "1"
    env.pop("MINIANDROID_S155_APPLY", None)
    t0 = time.time()
    r = subprocess.run(
        [BIN, "run", "--package", "io.github.yamin8000.dooz",
         "--data-root", store, "--trace", "--max-seconds", "120",
         "--frames", "30", "-o", rundir],
        env=env, capture_output=True, text=True, timeout=180)
    wall = time.time() - t0
    stderr = r.stderr
    open(f"{OUT}/perfops_stderr.log", "w").write(stderr)
    shot = f"{rundir}/screenshot.png"
    face = subprocess.run(["sha256sum", shot], capture_output=True,
                          text=True).stdout.split()[0][:16] \
        if os.path.exists(shot) else "NO_SCREENSHOT"
    # parse [PERF-OPS] rows: "  op=0x54 calls=7064565  ticks=17335056645 est_ms=..."
    OPNAMES = {0x54: "iget-object", 0x52: "iget", 0x62: "sget",
               0x22: "new-instance", 0x70: "invoke-direct",
               0x6e: "invoke-virtual", 0x6f: "invoke-super",
               0x71: "invoke-static", 0x72: "invoke-interface",
               0x58: "iput-object", 0x56: "iput", 0x63: "sget-object"}
    rows = {}
    for op, calls, ticks in re.findall(
            r"op=(0x[0-9a-fA-F]+)\s+calls=(\d+)\s+ticks=(\d+)", stderr):
        oi = int(op, 16)
        name = OPNAMES.get(oi, f"op{op}")
        c = int(calls)
        if c > 0:
            t = int(ticks)
            if name not in rows or rows[name]["calls"] < c:
                rows[name] = {"op": op, "calls": c,
                              "tpc": round(t / c, 0)}
    if not rows:
        # fall back: raw histogram lines if format differs
        print("[WARN] no PERF-OPS rows parsed; stderr tail:")
        print("\n".join(stderr.splitlines()[-30:]))
    ig = rows.get("iget-object")
    result = {
        "binary": subprocess.run(["sha256sum", BIN], capture_output=True,
                                 text=True).stdout.split()[0][:16],
        "protocol": {"apk": "io.github.yamin8000.dooz_23", "max-seconds": 120,
                     "frames": 30, "trace": True, "fresh_store": True},
        "wall_s": round(wall, 1),
        "face": face,
        "baseline": {"tpc": BASELINE_TPC, "calls": BASELINE_CALLS,
                     "binary": "a793f134936f7e58",
                     "source": "evidence/s156_record_loop/S156_P3_PERFOPS.txt"},
        "ops": rows,
    }
    if ig:
        ig["tpc_delta_pct"] = round(100.0 * (ig["tpc"] - BASELINE_TPC)
                                    / BASELINE_TPC, 1)
        ig["speedup_x"] = round(BASELINE_TPC / ig["tpc"], 2) if ig["tpc"] else None
    path = f"{EVDIR}/S156_P4_PERFOPS.json"
    json.dump(result, open(path, "w"), indent=1)
    print(f"face={face} wall={wall:.1f}s rc={r.returncode}")
    print(f"{'op':<18}{'calls':>12}{'t/c now':>10}{'t/c base':>10}{'delta':>9}")
    for name, v in sorted(rows.items(), key=lambda kv: -kv[1]["calls"])[:10]:
        d = f"{100.0*(v['tpc']-BASELINE_TPC)/BASELINE_TPC:+.1f}%" if name == "iget-object" else ""
        print(f"{name:<18}{v['calls']:>12,}{v['tpc']:>10.0f}{BASELINE_TPC:>10.0f}{d:>9}")
    print(f"evidence: {path}")

if __name__ == "__main__":
    main()
