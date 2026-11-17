#!/usr/bin/env python3
"""W6 Phase 1/3: bridge compile-flag experiments (measured, temp objects).
GGC tuning params change NO generated code (compile-time memory manager
only) — verified by object sha256 equality vs the baseline -Og object."""
import hashlib, json, os, re, subprocess, sys

os.chdir("/home/z/my-project/miniandroid")
EV = "evidence/wave6"; PROF = "/tmp/w6prof"
RESF = f"{EV}/w6_flag_experiments.json"
RES = json.load(open(RESF)) if os.path.exists(RESF) else {}

MEASURE = '''
import subprocess, resource, sys, time
t0 = time.monotonic()
r = subprocess.run(sys.argv[1:], capture_output=True, timeout=540)
dt = time.monotonic() - t0
ru = resource.getrusage(resource.RUSAGE_CHILDREN)
print(f"RESULT {r.returncode} {dt:.2f} {ru.ru_maxrss // 1024}")
'''

def measure(cmd):
    r = subprocess.run([sys.executable, "-I", "-c", MEASURE] + cmd,
                       capture_output=True, text=True, timeout=600)
    lines = [l for l in r.stdout.splitlines() if l.startswith("RESULT")]
    if not lines:
        return -1, 0.0, 0
    _, rc, dt, peak = lines[-1].split()
    return int(rc), float(dt), int(peak)

mk = subprocess.run(["make", "--no-print-directory", "-n", "-B", "all"],
                    capture_output=True, text=True, timeout=300).stdout

def base_cmd(src):
    for l in mk.splitlines():
        if f"-c -o build/" in l and l.strip().endswith(src) and "g++" in l:
            return l.strip()
    raise SystemExit(f"no command for {src}")

BR = base_cmd("src/dex/dalvik_bridge.cpp")
INT = base_cmd("src/dex/dalvik_interpreter.cpp")

EXPS = {
    "bridge_Og_ggc10_2048": (BR, "-Og", "--param ggc-min-expand=10 --param ggc-min-heapsize=2048"),
    "bridge_Og_ggc5_1024": (BR, "-Og", "--param ggc-min-expand=5 --param ggc-min-heapsize=1024"),
    "bridge_O2_ggc10_2048": (BR, "-O2", "--param ggc-min-expand=10 --param ggc-min-heapsize=2048"),
    "interp_O2_inline_budget": (INT, "-O2", "--param inline-unit-growth=15 --param large-function-growth=120"),
}

def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16] \
        if os.path.exists(p) else None

base_bridge_sha = sha(f"{PROF}/dalvik_bridge.o")
for tag, (base, level, params) in EXPS.items():
    if tag in RES:
        print(f"{tag}: done, skip"); continue
    cmd = re.sub(r"-o \S+ ", f"-o {PROF}/{tag}.o ", base)
    # swap the optimization level token
    cmd = cmd.replace(" -Og ", f" {level} ", 1) if " -Og " in cmd else \
          cmd.replace(" -O2 ", f" {level} ", 1)
    cmd = cmd + " " + params
    rc, dt, peak = measure(["bash", "-c", cmd])
    rec = {"rc": rc, "wall_s": dt, "peak_mb": peak, "level": level,
           "params": params, "obj_sha16": sha(f"{PROF}/{tag}.o"),
           "codegen_identical_to_baseline": sha(f"{PROF}/{tag}.o") == base_bridge_sha
           if "bridge" in tag else None}
    RES[tag] = rec
    json.dump(RES, open(RESF, "w"), indent=1)
    print(f"{tag}: rc={rc} wall={dt:.1f}s peak={peak}MB "
          f"obj_same={rec['codegen_identical_to_baseline']}")
print("EXPERIMENTS DONE")
