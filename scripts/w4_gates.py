#!/usr/bin/env python3
"""W4 Phase 5: acceptance-gate measurements, 5 reps each, median + range."""
import subprocess, time, statistics, json, os

os.chdir("/home/z/my-project/miniandroid")
RES = {}

def make_time(target_extra=None, reps=5):
    ts = []
    for _ in range(reps):
        t0 = time.monotonic()
        r = subprocess.run(["make", "-j1", "all"] + (target_extra or []),
                           capture_output=True, timeout=560)
        ts.append(time.monotonic() - t0)
        assert r.returncode == 0, r.stderr[-400:]
    return ts

def touch_gate(path, reps=5):
    """touch a source, time the rebuild+link (the ordinary-edit cost)."""
    ts = []
    for _ in range(reps):
        os.utime(path, None)
        t0 = time.monotonic()
        r = subprocess.run(["make", "-j1", "all"], capture_output=True, timeout=560)
        ts.append(time.monotonic() - t0)
        assert r.returncode == 0, r.stderr[-400:]
    return ts

def report(label, ts):
    RES[label] = {"runs": [round(t, 2) for t in ts],
                  "median": round(statistics.median(ts), 2),
                  "min": round(min(ts), 2), "max": round(max(ts), 2)}
    print(f"{label}: median={statistics.median(ts):.2f}s "
          f"range=[{min(ts):.2f},{max(ts):.2f}]")

# G1 no-op build
report("G1_noop_build", make_time(reps=5))

# G2 ordinary rule edit per split TU (touch = same rebuild cost as an edit)
for tu in ["dalvik_opcodes.cpp", "dalvik_engine_invoke.cpp",
           "dalvik_engine_core.cpp", "dalvik_engine_tail.cpp"]:
    report(f"G2_edit_{tu}", touch_gate(f"src/dex/{tu}"))
report("G2_edit_bridge_-Og", touch_gate("src/dex/dalvik_bridge.cpp"))

json.dump(RES, open("evidence/issue612_audit/wave4_gates.json", "w"), indent=1)
print("saved evidence/issue612_audit/wave4_gates.json")
