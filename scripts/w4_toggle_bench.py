#!/usr/bin/env python3
"""W4 Phase 1/2: controlled single-TU compile experiments on dalvik_engine.cpp.
Usage: python3 w4_toggle_bench.py <label> [<label> ...]
Each label = one exact-command compile variant. Resumable: results appended to
evidence/issue612_audit/wave4_toggles.json (completed labels are skipped)."""
import json, os, re, shutil, subprocess, sys, time

os.chdir("/home/z/my-project/miniandroid")
EV = "evidence/issue612_audit"
os.makedirs(EV, exist_ok=True)
RES = f"{EV}/wave4_toggles.json"
res = json.load(open(RES)) if os.path.exists(RES) else {}

# exact production command for the heavy TU (from the Makefile rules)
mk = subprocess.run(["make", "--no-print-directory", "-n",
                     "-W", "src/dex/dalvik_engine.cpp",
                     "build/dex/dalvik_engine.o"],
                    capture_output=True, text=True).stdout
base_cmd = None
for line in mk.splitlines():
    if line.startswith("g++") and "dalvik_engine.cpp" in line:
        base_cmd = line.strip()
        break
if not base_cmd:
    sys.exit("could not resolve production compile command")

VARIANTS = {
    "baseline_prod": [],
    "g0": ["-g0"],                      # no debug info (isolate -g cost)
    "g": ["-g"],                        # WITH debug info (line-map object)
    "no_inline": ["-fno-inline-functions"],
    "no_ipa_cp": ["-fno-ipa-cp"],
    "no_ipa_sra": ["-fno-ipa-sra"],
    "no_ipa_clone": ["-fno-ipa-clone"],
    "no_vec": ["-fno-tree-vectorize"],
    "no_unroll": ["-fno-unroll-loops"],
    "no_icf": ["-fno-ipa-icf"],
    "O1": ["-O1"],                      # replaces -O2 (last flag wins)
    "Og": ["-Og"],
    "O0g": ["-O0"],                     # DEV-like, keep -g
    "g1": ["-g1"],                      # minimal line info for addr2line map
    "no_cp_clone": ["-fno-ipa-cp-clone"],
}

def run(label):
    if label in res:
        print(f"{label}: cached {res[label]['wall']}s")
        return
    extra = VARIANTS[label]
    obj = f"/tmp/w4_{label}.o"
    cmd = base_cmd.replace(" -MMD -MP", "") + f" -o {obj} " + " ".join(extra)
    cmd = cmd.split()
    cmd[0] = shutil.which(cmd[0]) or cmd[0]
    rep = f"{EV}/wave4_ftime_{label}.txt"
    t0 = time.monotonic()
    with open(rep, "w") as rf:
        pid = os.posix_spawn(
            cmd[0], cmd, dict(os.environ),
            file_actions=[(os.POSIX_SPAWN_DUP2, rf.fileno(), 1),
                          (os.POSIX_SPAWN_DUP2, rf.fileno(), 2)])
        _, status, ru = os.wait4(pid, 0)
    dt = time.monotonic() - t0
    rc = os.waitstatus_to_exitcode(status)
    peak = ru.ru_maxrss // 1024
    size = os.path.getsize(obj) if os.path.exists(obj) else 0
    res[label] = {"cmd": " ".join(cmd), "extra_flags": extra, "rc": rc,
                  "wall": round(dt, 2), "peak_rss_mb": peak, "obj_bytes": size}
    json.dump(res, open(RES, "w"), indent=1)
    print(f"{label}: rc={rc} wall={dt:.1f}s peak={peak}MB obj={size/1e6:.2f}MB")

for label in sys.argv[1:]:
    if label not in VARIANTS:
        sys.exit(f"unknown variant {label}")
    run(label)
