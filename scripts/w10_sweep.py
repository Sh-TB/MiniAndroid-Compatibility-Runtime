#!/usr/bin/env python3
"""W10 Phase 2/3 candidate sweep: compiles candidate flag-sets directly to temp
objects (Makefile untouched). Winners get full verification and Makefile adoption."""
import subprocess, re, json, os, time

os.chdir("/home/z/my-project/miniandroid")

def run(cmd, timeout=900, env=None):
    e = dict(os.environ); e.update(env or {})
    t0 = time.monotonic()
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout, env=e)
    return time.monotonic() - t0, r.returncode, r.stdout + r.stderr

def mkcmd(obj):
    out = subprocess.run(f"make --no-print-directory -n -B {obj}", shell=True,
                         capture_output=True, text=True).stdout
    return [l.strip() for l in out.split("\n") if " -c -o " in l][0]

R = {}
# ---------- interpreter candidates ----------
base_i = mkcmd("build_dev_so/objects/dalvik_interpreter.o")
INTERP = [
    ("I1_growth10_80",  base_i.replace("--param inline-unit-growth=15", "--param inline-unit-growth=10")
                              .replace("--param large-function-growth=120", "--param large-function-growth=80"), None),
    ("I2_growth8_60_auto20", base_i.replace("--param inline-unit-growth=15", "--param inline-unit-growth=8")
                              .replace("--param large-function-growth=120", "--param large-function-growth=60")
                              + " --param max-inline-insns-auto=20", None),
    ("I3_growth6_45_auto12", base_i.replace("--param inline-unit-growth=15", "--param inline-unit-growth=6")
                              .replace("--param large-function-growth=120", "--param large-function-growth=45")
                              + " --param max-inline-insns-auto=12", None),
    ("I4_noipa", base_i + " -fno-ipa-cp -fno-ipa-sra", None),
    ("I5_ggc", base_i, {"GGC_MIN_EXPAND": "40", "GGC_MIN_FREEHEAP": "16384"}),
]
R["interpreter"] = {}
for name, cmd, env in INTERP:
    w, rc, _ = run(cmd.replace("build_dev_so/objects/dalvik_interpreter.o",
                               f"/tmp/w10_{name}.o"), env=env)
    R["interpreter"][name] = {"wall_s": round(w, 2), "rc": rc}
    print(f"INTERP {name}: {w:.2f}s rc={rc}", flush=True)

# ---------- bridge candidates ----------
base_b = mkcmd("build_dev_so/objects/dalvik_bridge.o")
BRIDGE = [
    ("B1_ggc30", base_b, {"GGC_MIN_EXPAND": "30", "GGC_MIN_FREEHEAP": "16384"}),
    ("B2_ggc60", base_b, {"GGC_MIN_EXPAND": "60", "GGC_MIN_FREEHEAP": "32768"}),
    ("B3_O1", base_b.replace(" -Og ", " -O1 "), None),
    ("B4_noipa", base_b + " -fno-ipa-cp -fno-ipa-sra -fno-ipa-pure-const", None),
    ("B5_inline_caps", base_b + " --param max-inline-insns-auto=12 --param inline-unit-growth=10", None),
    ("B6_O0", base_b.replace(" -Og ", " -O0 "), None),
]
R["bridge"] = {}
for name, cmd, env in BRIDGE:
    w, rc, _ = run(cmd.replace("build_dev_so/objects/dalvik_bridge.o", f"/tmp/w10_{name}.o"), env=env)
    R["bridge"][name] = {"wall_s": round(w, 2), "rc": rc}
    print(f"BRIDGE {name}: {w:.2f}s rc={rc}", flush=True)

json.dump(R, open("evidence/wave10/w10_sweep_raw.json", "w"), indent=1)
print("SWEEP done")
