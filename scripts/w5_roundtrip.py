#!/usr/bin/env python3
"""W5 Phase 1/2: DALVIK_SPLIT=0/1 round-trip verification + clean-build
baselines. Steps (resumable by key):
  roundtrip_split0 : flip to monolith (stamp forces dalvik_engine.cpp -O2
                     rebuild), verify parity + test + Guess hash
  roundtrip_split1 : flip back to 7-TU split, verify parity + test + hash
  clean_split      : make clean + make -j1 all (full production split build)
  j2_probe         : touch two mid-size TUs, make -j2 all (parallelism under
                     the RAM ceiling; bridge -Og excluded from the pair)
"""
import json, os, subprocess, sys, time

os.chdir("/home/z/my-project/miniandroid")
EV = "evidence/wave5"
RESF = f"{EV}/wave5_roundtrip_clean.json"
RES = json.load(open(RESF)) if os.path.exists(RESF) else {}
GUESS = "/home/z/my-project/upload/handoff_apks/ru.zxalexis.ugaday_15.apk"

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
                       capture_output=True, text=True, timeout=590)
    _, rc, dt, peak = [l for l in r.stdout.splitlines()
                       if l.startswith("RESULT")][-1].split()
    return int(rc), float(dt), int(peak)

def guess_hash(tag):
    os.makedirs(f"{EV}/rt_{tag}", exist_ok=True)
    r = subprocess.run(["./build/miniandroid", "run", "--max-seconds", "70",
                        "--frames", "3", "-o", f"{EV}/rt_{tag}", GUESS],
                       capture_output=True, timeout=200)
    ok = b"SUCCESS" in r.stdout + r.stderr
    import hashlib
    h = hashlib.sha256(open(f"{EV}/rt_{tag}/screenshot.png", "rb").read()).hexdigest()[:24]
    return ok, h

def parity():
    r = subprocess.run(["make", "--no-print-directory", "check-source-parity"],
                       capture_output=True, text=True, timeout=120)
    return r.returncode, [l for l in r.stdout.splitlines() if "PARITY" in l][-1]

step = sys.argv[1] if len(sys.argv) > 1 else ""

if step == "roundtrip_split0" and "roundtrip_split0" not in RES:
    rc, dt, peak = measure(["make", "DALVIK_SPLIT=0", "-j1", "all"])
    p = parity()
    RES["roundtrip_split0"] = {"make": {"rc": rc, "wall": round(dt, 2),
                                        "peak_mb": peak},
                               "parity": p[1]}
    json.dump(RES, open(RESF, "w"), indent=1)
    print(f"SPLIT=0 monolith build: rc={rc} wall={dt:.1f}s peak={peak}MB | {p[1]}")

if step == "roundtrip_verify0" and "roundtrip_verify0" not in RES:
    rc2, dt2, _ = measure(["make", "--no-print-directory", "test"])
    ok, h = guess_hash("split0")
    RES["roundtrip_verify0"] = {"make_test": {"rc": rc2, "wall": round(dt2, 2)},
                                "guess_success": ok, "screenshot_sha": h,
                                "hash_is_canonical": h == "87fe26766fc48d06c59d4c15"}
    json.dump(RES, open(RESF, "w"), indent=1)
    print(f"SPLIT=0 verify: test rc={rc2} {dt2:.1f}s | guess={ok} | sha={h}")

if step == "roundtrip_split1" and "roundtrip_split1" not in RES:
    rc, dt, peak = measure(["make", "DALVIK_SPLIT=1", "-j1", "all"])
    p = parity()
    RES["roundtrip_split1"] = {"make": {"rc": rc, "wall": round(dt, 2),
                                        "peak_mb": peak},
                               "parity": p[1]}
    json.dump(RES, open(RESF, "w"), indent=1)
    print(f"SPLIT=1 rebuild: rc={rc} wall={dt:.1f}s peak={peak}MB | {p[1]}")

if step == "roundtrip_verify1" and "roundtrip_verify1" not in RES:
    rc2, dt2, _ = measure(["make", "--no-print-directory", "test"])
    ok, h = guess_hash("split1")
    RES["roundtrip_verify1"] = {"make_test": {"rc": rc2, "wall": round(dt2, 2)},
                                "guess_success": ok, "screenshot_sha": h,
                                "hash_is_canonical": h == "87fe26766fc48d06c59d4c15"}
    json.dump(RES, open(RESF, "w"), indent=1)
    print(f"SPLIT=1 verify: test rc={rc2} {dt2:.1f}s | guess={ok} | sha={h}")

if step == "clean_split" and "clean_split" not in RES:
    subprocess.run(["make", "clean"], capture_output=True, timeout=120)
    t0 = time.monotonic()
    rc, dt, peak = measure(["make", "-j1", "all"])
    RES["clean_split"] = {"rc": rc, "wall": round(dt, 2), "peak_mb": peak,
                          "wall_total": round(time.monotonic() - t0, 2)}
    json.dump(RES, open(RESF, "w"), indent=1)
    print(f"CLEAN split build: rc={rc} wall={dt:.1f}s peak={peak}MB")

if step == "j2_probe" and "j2_probe" not in RES:
    os.utime("src/dex/dalvik_opcodes.cpp", None)
    os.utime("src/dex/dalvik_engine_invoke.cpp", None)
    rc, dt, peak = measure(["make", "-j2", "all"])
    RES["j2_probe"] = {"rc": rc, "wall": round(dt, 2), "peak_mb": peak,
                       "note": "two mid-size TUs (-O2, no bridge) in parallel"}
    json.dump(RES, open(RESF, "w"), indent=1)
    print(f"-j2 probe: rc={rc} wall={dt:.1f}s peak={peak}MB")
print("STEP DONE:", step or "none")
