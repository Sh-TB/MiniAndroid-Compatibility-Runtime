#!/usr/bin/env python3
"""W10 sweep round 2: interpreter -O1/-O0/-fno-inline + RSS (getrusage children delta)."""
import subprocess, json, os, time, resource

os.chdir("/home/z/my-project/miniandroid")

def rss_delta():
    return resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss // 1024  # MB

def run(cmd, timeout=900, env=None):
    e = dict(os.environ); e.update(env or {})
    before = rss_delta()
    t0 = time.monotonic()
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout, env=e)
    return time.monotonic() - t0, r.returncode, r.stdout + r.stderr, rss_delta()

def mkcmd(obj):
    out = subprocess.run(f"make --no-print-directory -n -B {obj}", shell=True,
                         capture_output=True, text=True).stdout
    return [l.strip() for l in out.split("\n") if " -c -o " in l][0]

base_i = mkcmd("build_dev_so/objects/dalvik_interpreter.o")
base_b = mkcmd("build_dev_so/objects/dalvik_bridge.o")
CANDS = [
    ("I6_O1", base_i.replace(" -O2 ", " -O1 "), None),
    ("I7_O0", base_i.replace(" -O2 ", " -O0 "), None),
    ("I8_noinline", base_i + " -fno-inline-functions -fno-inline-small-functions -fno-inline-functions-called-once", None),
    ("B7_O0_rss", base_b.replace(" -Og ", " -O0 ").replace("build_dev_so/objects/dalvik_bridge.o", "/tmp/w10_B7rss.o"), None),
]
R = {}
for name, cmd, env in CANDS:
    w, rc, out, rss = run(cmd.replace("build_dev_so/objects/dalvik_interpreter.o", f"/tmp/w10_{name}.o")
                          if name.startswith("I") else cmd, env=env)
    R[name] = {"wall_s": round(w, 2), "rc": rc, "rss_mb": rss}
    print(f"{name}: {w:.2f}s rc={rc} rss={rss}MB", flush=True)

json.dump(R, open("evidence/wave10/w10_sweep2_raw.json", "w"), indent=1)
print("SWEEP2 done")
