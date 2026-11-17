#!/usr/bin/env python3
"""W5 Phase 1/2/6: acceptance gates + incremental baselines, 5 reps each.
Per-rep: wall, exit code, peak RAM (fresh interpreter per rep so
RUSAGE_CHILDREN max = that rep's tree peak), compiler command capture.
Rep-level checkpointing: safe to re-run after a timeout; done reps skipped."""
import json, os, subprocess, sys, time

os.chdir("/home/z/my-project/miniandroid")
EV = "evidence/wave5"
os.makedirs(EV, exist_ok=True)
RESF = f"{EV}/wave5_gates.json"
RES = json.load(open(RESF)) if os.path.exists(RESF) else {}

MEASURE = '''
import subprocess, resource, sys, time
t0 = time.monotonic()
r = subprocess.run(sys.argv[1:], capture_output=True, timeout=560)
dt = time.monotonic() - t0
ru = resource.getrusage(resource.RUSAGE_CHILDREN)
print(f"RESULT {r.returncode} {dt:.3f} {ru.ru_maxrss // 1024}")
'''

def measure_rep(cmd):
    r = subprocess.run([sys.executable, "-I", "-c", MEASURE] + cmd,
                       capture_output=True, text=True, timeout=600)
    lines = [l for l in r.stdout.splitlines() if l.startswith("RESULT")]
    _, rc, dt, peak = lines[-1].split()
    return int(rc), float(dt), int(peak)

def make_n_command():
    r = subprocess.run(["make", "--no-print-directory", "-n", "-B", "all"],
                       capture_output=True, text=True, timeout=120)
    cmds = [l.strip() for l in r.stdout.splitlines() if l.strip().startswith("g++")]
    return cmds[:14]

def run_gate(label, prep=None, reps=5):
    got = RES.get(label, {"reps": []})
    n0 = len(got["reps"])
    if n0 >= reps:
        print(f"{label}: complete ({n0} reps), skip")
        return
    if "cmd" not in got:
        got["cmd"] = make_n_command()
    for i in range(n0, reps):
        if prep:
            prep()
        rc, dt, peak = measure_rep(["make", "-j1", "all"])
        got["reps"].append({"rc": rc, "wall": round(dt, 2), "peak_mb": peak})
        print(f"  {label} rep{i+1}: rc={rc} wall={dt:.1f}s peak={peak}MB")
        json.dump(RES, open(RESF, "w"), indent=1)
    walls = [r["wall"] for r in got["reps"]]
    var = sum((w - sum(walls)/len(walls))**2 for w in walls) / len(walls)
    got["stats"] = {"median": sorted(walls)[len(walls)//2], "min": min(walls),
                    "max": max(walls), "variance": round(var, 3)}
    RES[label] = got
    json.dump(RES, open(RESF, "w"), indent=1)
    s = got["stats"]
    print(f"{label}: median={s['median']}s min={s['min']} max={s['max']} var={s['variance']}")

def touch(p):
    os.utime(p, None)

GATES = [
    ("G1_noop", None),
    ("G2_edit_tail", lambda: touch("src/dex/dalvik_engine_tail.cpp")),
    ("G2_edit_opcodes_field", lambda: touch("src/dex/dalvik_opcodes.cpp")),
    ("G2_edit_interpreter", lambda: touch("src/dex/dalvik_interpreter.cpp")),
    ("G2_edit_opcodes_invoke", lambda: touch("src/dex/dalvik_opcodes_invoke.cpp")),
    ("G2_edit_two_opcodes", lambda: (touch("src/dex/dalvik_opcodes.cpp"),
                                     touch("src/dex/dalvik_opcodes_invoke.cpp"))),
    ("G2_edit_engine_invoke", lambda: touch("src/dex/dalvik_engine_invoke.cpp")),
    ("G2_edit_engine_core", lambda: touch("src/dex/dalvik_engine_core.cpp")),
    ("G2_edit_bridge_-Og", lambda: touch("src/dex/dalvik_bridge.cpp")),
    ("G3_header_touch", lambda: touch("src/dex/dalvik_engine_internal.h")),
    ("G4_link_only", lambda: os.path.exists("build/miniandroid")
        and os.remove("build/miniandroid")),
]

only = sys.argv[1:] if len(sys.argv) > 1 else None
for label, prep in GATES:
    if only and label not in only:
        continue
    run_gate(label, prep)

# targeted test execution: run the test binaries DIRECTLY (make test is
# not phony for the run step — it no-ops once the exe is current)
if not only or "G5_test_bins" in (only or []):
    import glob
    test_bins = sorted(glob.glob("build/*test*"))[:4]
    got = RES.get("G5_test_bins", {"reps": [], "bins": test_bins})
    if len(got["reps"]) < 5:
        for i in range(len(got["reps"]), 5):
            t0 = time.monotonic()
            ok = 0
            for b in test_bins:
                if os.path.isfile(b) and os.access(b, os.X_OK):
                    r = subprocess.run([b], capture_output=True, timeout=120)
                    ok += (r.returncode == 0)
            dt = time.monotonic() - t0
            got["reps"].append({"rc": 0 if ok == len(test_bins) else 1,
                                "wall": round(dt, 3), "peak_mb": 0,
                                "bins_ok": ok})
            print(f"  G5_test_bins rep{i+1}: wall={dt:.2f}s ok={ok}/{len(test_bins)}")
            json.dump(RES, open(RESF, "w"), indent=1)
        walls = [r["wall"] for r in got["reps"]]
        got["stats"] = {"median": sorted(walls)[len(walls)//2], "min": min(walls),
                        "max": max(walls),
                        "variance": round(sum((w-sum(walls)/len(walls))**2
                                              for w in walls)/len(walls), 3)}
        RES["G5_test_bins"] = got
        json.dump(RES, open(RESF, "w"), indent=1)
        print(f"G5_test_bins: median={got['stats']['median']}s")
if False:
    got = RES.get("G5_test_run", {"reps": []})
    if len(got["reps"]) < 5:
        for i in range(len(got["reps"]), 5):
            rc, dt, peak = measure_rep(["make", "--no-print-directory", "test"])
            got["reps"].append({"rc": rc, "wall": round(dt, 2), "peak_mb": peak})
            print(f"  G5_test_run rep{i+1}: rc={rc} wall={dt:.1f}s")
            json.dump(RES, open(RESF, "w"), indent=1)
        walls = [r["wall"] for r in got["reps"]]
        got["stats"] = {"median": sorted(walls)[len(walls)//2], "min": min(walls),
                        "max": max(walls),
                        "variance": round(sum((w-sum(walls)/len(walls))**2
                                              for w in walls)/len(walls), 3)}
        RES["G5_test_run"] = got
        json.dump(RES, open(RESF, "w"), indent=1)
        print(f"G5_test_run: median={got['stats']['median']}s")
print("ALL DONE")
