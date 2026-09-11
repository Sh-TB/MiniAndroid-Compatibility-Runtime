#!/usr/bin/env python3
"""Benchmark BEFORE vs AFTER (brief §38-40, speed-addendum §43).
Real wall-clock measurements, 3 runs each, same machine/input/commit.
NO claimed numbers — everything measured here or marked UNMEASURED."""
import json, os, subprocess, time, zipfile, struct

HERE = os.path.dirname(os.path.abspath(__file__))   # <repo>/tools/verify
PROJ = os.path.dirname(os.path.dirname(HERE))       # repo root
DOOZ = os.path.join(PROJ, "miniandroid", "download", "exp076_corpus", "io.github.yamin8000.dooz_18.apk")

def _find_aapt2():
    env = os.environ.get("MINIAAPT2")
    if env and os.path.exists(env):
        return env
    bootstrap = os.environ.get("MINITOOLS", os.path.join(os.path.dirname(PROJ), "tools"))
    for cand in (os.path.join(PROJ, "tools", "aapt2", "aapt2"),
                 os.path.join(bootstrap, "aapt2", "aapt2")):
        if os.path.exists(cand):
            return cand
    return "aapt2"

AAPT2 = _find_aapt2()

def timeit(fn, n=3):
    ts = []
    for _ in range(n):
        t0 = time.perf_counter()
        fn()
        ts.append(round((time.perf_counter() - t0) * 1000, 1))
    return {"runs_ms": ts, "median_ms": sorted(ts)[len(ts) // 2]}

# ---------- BASELINE (manual path an agent used pre-tooling)
def manual_apk_inspect():
    subprocess.run(["unzip", "-l", DOOZ], capture_output=True)
    subprocess.run([AAPT2, "dump", "badging", DOOZ],
                   capture_output=True, text=True)
    # manual dex header read (the old inline way)
    with zipfile.ZipFile(DOOZ) as z:
        data = z.read("classes.dex")
    counts = struct.unpack_from("<I", data, 88)[0], struct.unpack_from("<I", data, 96)[0]
    return counts

def manual_root_lookup():
    # pre-tooling: agent greps worklog + several docs to assemble the frontier picture
    for f in ("worklog.md", "docs/ROOT_LAW_GLOBAL_AUDIT.md"):
        subprocess.run(["grep", "-n", "first-frame\|frame-pump\|ComposeView", os.path.join(PROJ, f)],
                       capture_output=True)
    subprocess.run(["grep", "-rn", "children=0", os.path.join(PROJ, "miniandroid", "run", "m9_merge_dooz")],
                   capture_output=True)

# ---------- TOOL-ASSISTED
def tool_cold():
    subprocess.run(["python3", "tools/verify/apk_artifacts.py", DOOZ, "--force"],
                   cwd=PROJ, capture_output=True)

def tool_warm():
    subprocess.run(["python3", "tools/verify/apk_artifacts.py", DOOZ],
                   cwd=PROJ, capture_output=True)

def tool_root_lookup():
    subprocess.run(["python3", "tools/verify/verify.py", "--root", "R-NEW-246"],
                   cwd=PROJ, capture_output=True)

def tool_cluster_shot():
    subprocess.run(["python3", "tools/verify/verify.py", "--cluster", "shot"],
                   cwd=PROJ, capture_output=True)

res = {
    "environment": {"commit": subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                       cwd=PROJ, capture_output=True, text=True).stdout.strip(),
                    "cpu_only": True, "runs": 3},
    "apk_inspection_dooz": {
        "A_manual_baseline": timeit(manual_apk_inspect),
        "B_tool_cold": timeit(tool_cold),
        "C_tool_cached": timeit(tool_warm),
    },
    "root_investigation_package_R-NEW-246": {
        "A_manual_baseline": timeit(manual_root_lookup),
        "B_tool_fastpath": timeit(tool_root_lookup),
    },
    "screenshot_validation": {
        "B_tool_probe": timeit(tool_cluster_shot),
    },
}
# speedups
a = res["apk_inspection_dooz"]["A_manual_baseline"]["median_ms"]
c = res["apk_inspection_dooz"]["C_tool_cached"]["median_ms"]
res["apk_inspection_dooz"]["speedup_cached_vs_manual"] = round(a / c, 1) if c else None
r = res["root_investigation_package_R-NEW-246"]
res["root_investigation_package_R-NEW-246"]["speedup_vs_manual"] = round(
    r["A_manual_baseline"]["median_ms"] / r["B_tool_fastpath"]["median_ms"], 1)
print(json.dumps(res, indent=1))
json.dump(res, open(os.path.join(HERE, "benchmark_results.json"), "w"), indent=1)
