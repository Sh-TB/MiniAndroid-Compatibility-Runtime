#!/usr/bin/env python3
"""W5 Phase 1: DEV (-O0) end-to-end feedback loop, 5 reps.
Loop per rep: touch an opcode rule file -> make DEV=1 -j1 all (recompile
only that TU at -O0 + relink) -> make test (relink test exe + run).
NOTE: DEV=1 compiles into the SAME build/ directory (documented wave-2
behavior); production objects are restored afterwards by make all (SPLIT=1).
"""
import json, os, subprocess, sys, time

os.chdir("/home/z/my-project/miniandroid")
EV = "evidence/wave5"
RESF = f"{EV}/wave5_dev_loop.json"
RES = json.load(open(RESF)) if os.path.exists(RESF) else {}

MEASURE = '''
import subprocess, resource, sys, time
t0 = time.monotonic()
r = subprocess.run(sys.argv[1:], capture_output=True, timeout=560)
dt = time.monotonic() - t0
ru = resource.getrusage(resource.RUSAGE_CHILDREN)
print(f"RESULT {r.returncode} {dt:.3f} {ru.ru_maxrss // 1024}")
'''

def measure(cmd):
    r = subprocess.run([sys.executable, "-I", "-c", MEASURE] + cmd,
                       capture_output=True, text=True, timeout=600)
    _, rc, dt, peak = [l for l in r.stdout.splitlines()
                       if l.startswith("RESULT")][-1].split()
    return int(rc), float(dt), int(peak)

# one-time: enter DEV mode (full tree at -O0; dalvik parts rebuild ~40s total)
if "dev_initial" not in RES:
    os.utime("src/dex/dalvik_opcodes.cpp", None)
    rc, dt, peak = measure(["make", "DEV=1", "-j1", "all"])
    RES["dev_initial"] = {"rc": rc, "wall": round(dt, 2), "peak_mb": peak}
    json.dump(RES, open(RESF, "w"), indent=1)
    print(f"DEV initial build: rc={rc} wall={dt:.1f}s peak={peak}MB")

# 5 reps: edit opcodes rule -> make DEV -> make test
if len(RES.get("loop_reps", [])) < 5:
    for i in range(len(RES.get("loop_reps", [])), 5):
        os.utime("src/dex/dalvik_opcodes.cpp", None)
        t0 = time.monotonic()
        rc1, dt1, pk1 = measure(["make", "DEV=1", "-j1", "all"])
        rc2, dt2, pk2 = measure(["make", "--no-print-directory", "test"])
        total = time.monotonic() - t0
        RES.setdefault("loop_reps", []).append({
            "make_dev": {"rc": rc1, "wall": round(dt1, 2), "peak_mb": pk1},
            "make_test": {"rc": rc2, "wall": round(dt2, 2)},
            "edit_to_test_total": round(total, 2)})
        print(f"  rep{i+1}: make_dev={dt1:.1f}s test={dt2:.1f}s TOTAL={total:.1f}s "
              f"rc=({rc1},{rc2})")
        json.dump(RES, open(RESF, "w"), indent=1)
    walls = [r["edit_to_test_total"] for r in RES["loop_reps"]]
    RES["stats"] = {"median": sorted(walls)[len(walls)//2], "min": min(walls),
                    "max": max(walls)}
    json.dump(RES, open(RESF, "w"), indent=1)
    print(f"DEV loop: median={RES['stats']['median']}s "
          f"min={RES['stats']['min']} max={RES['stats']['max']}")

# restore production objects (same tree, SPLIT=1 -O2)
if "prod_restore" not in RES:
    rc, dt, peak = measure(["make", "-j1", "all"])
    RES["prod_restore"] = {"rc": rc, "wall": round(dt, 2), "peak_mb": peak}
    json.dump(RES, open(RESF, "w"), indent=1)
    print(f"production restore: rc={rc} wall={dt:.1f}s peak={peak}MB")
print("DEV LOOP DONE")
