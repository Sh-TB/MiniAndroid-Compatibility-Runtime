#!/usr/bin/env python3
"""W10 Phase 4: unified performance harness. Records revision, compiler, flags,
exact commands, compile/link/test/cycle durations, peak RSS, rebuilt objects,
test relinks, runtime result. x5 reps per gate + stepwise phase decomposition."""
import subprocess, time, json, os, resource, statistics, re, hashlib

os.chdir("/home/z/my-project/miniandroid")
REV = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
GCCV = subprocess.run(["g++", "--version"], capture_output=True, text=True).stdout.split("\n")[0]

def run(cmd, timeout=900):
    before = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    t0 = time.monotonic()
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    rss = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss // 1024
    return time.monotonic() - t0, r.returncode, r.stdout + r.stderr, rss

def flags_for(obj):
    out = subprocess.run(f"make --no-print-directory -n -B {obj}", shell=True,
                         capture_output=True, text=True).stdout
    return [l.strip() for l in out.split("\n") if " -c -o " in l][0]

def full_cycle(tu, rep):
    subprocess.run(["touch", f"src/{tu}.cpp"])
    w, rc, out, rss = run("make --no-print-directory dev-so-test -j1")
    return {"rep": rep, "cycle_s": round(w, 2), "rc": rc, "peak_rss_mb": rss,
            "pic_compiles": len(re.findall(r"-c -o build_dev_so/objects/", out)),
            "so_relink": len(re.findall(r"-shared -o build_dev_so/libminiandroid_dalvik\.so", out)),
            "test_exe_relinks": len(re.findall(r"-o build_dev_so/tests/\w+ .*tests/\w+\.cpp", out)),
            "runtime_result": {"battery_pass": out.count("[PASS]"), "battery_total": 3}}

def phases(tu):
    subprocess.run(["touch", f"src/{tu}.cpp"])
    obj = f"build_dev_so/objects/{os.path.basename(tu)}.o"
    wc, rc1, _, rss1 = run(f"make --no-print-directory {obj} -j1")
    ws, rc2, _, _ = run("make --no-print-directory build_dev_so/libminiandroid_dalvik.so -j1")
    wt, rc3, _, _ = run("make --no-print-directory dev-so-test -j1")
    return {"compile_s": round(wc, 2), "so_link_s": round(ws, 2), "test_exec_s": round(wt, 2),
            "sum_s": round(wc + ws + wt, 2), "compile_rss_mb": rss1,
            "all_rc0": rc1 == 0 and rc2 == 0 and rc3 == 0}

def gate(tu, name, n):
    runs = [full_cycle(tu, i + 1) for i in range(n)]
    cyc = [r["cycle_s"] for r in runs]
    ph = [phases(tu) for _ in range(2)]
    return {"source_file": f"src/{tu}.cpp", "source_revision": REV, "compiler": GCCV,
            "compile_command": flags_for(f"build_dev_so/objects/{os.path.basename(tu)}.o"),
            "runs": runs, "median_s": round(statistics.median(cyc), 2),
            "min_s": round(min(cyc), 2), "max_s": round(max(cyc), 2),
            "phase_decomposition": ph}

R = {"revision": REV, "compiler": GCCV, "host": "2-core, 4GB cgroup"}
R["interpreter"] = gate("dex/dalvik_interpreter", "interpreter", 5)
R["bridge"] = gate("dex/dalvik_bridge", "bridge", 5)
R["opcode"] = gate("dex/dalvik_opcodes", "opcode", 5)
noop = [run("make --no-print-directory dev-so-test -j1") for _ in range(5)]
R["noop"] = {"runs_s": [round(w, 2) for w, _, _, _ in noop],
             "median_s": round(statistics.median([w for w, _, _, _ in noop]), 2),
             "all_rc0": all(rc == 0 for _, rc, _, _ in noop)}
print("interpreter", R["interpreter"]["runs"] and [r["cycle_s"] for r in R["interpreter"]["runs"]],
      "median", R["interpreter"]["median_s"])
print("bridge", [r["cycle_s"] for r in R["bridge"]["runs"]], "median", R["bridge"]["median_s"])
print("opcode", [r["cycle_s"] for r in R["opcode"]["runs"]], "median", R["opcode"]["median_s"])
print("noop", R["noop"])
json.dump(R, open("evidence/wave10/w10_benchmarks.json", "w"), indent=1)
print("HARNESS done")
