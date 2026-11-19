#!/usr/bin/env python3
"""w23_chain_results.py — summarize the W23 build-chain logs into a table.

Reads evidence/w23/build_bench.jsonl and maps each record to the chain stage
it measured (by command signature), printing wall/CPU/RSS/rc per stage, plus
the ccache hit/miss stats when present.
"""
import json
import os

REPO = os.environ.get("MINIANDROID_REPO", "/home/z/my-project/miniandroid")
EV = os.path.join(REPO, "evidence/w23")

STAGES = [
    ("ccache_cold", "build_cc"),
    ("ccache_warm", "build_cc"),
    ("g0_profile", "-g0"),
    ("o1g0_profile", "-O1"),
    ("cmake_megabatch", "build_cmake"),
    ("final_prod_clean", "all"),
]

records = [json.loads(l) for l in open(os.path.join(EV, "build_bench.jsonl"))]
records = [r for r in records if r.get("rc") is not None]

def sig(r):
    c = r["cmd"]
    if "BUILDDIR=build_cc" in " ".join(c):
        return "build_cc"
    if "build_cmake" in " ".join(c):
        return "build_cmake"
    joined = " ".join(c)
    if "-g0" in joined and "-O1" not in joined:
        return "-g0"
    if "-O1" in joined:
        return "-O1"
    if c[-1] == "all" and "BUILDDIR" not in joined:
        return "all"
    return "dev-so" if "dev-so" in c else "other"

print("%-22s %9s %9s %9s %6s %s" % ("stage", "wall_s", "cpu_u+s", "rss_mb", "rc", "log"))
seen = {}
for r in records:
    s = sig(r)
    key = (s, r["log"])
    seen.setdefault(s, []).append(r)
# map logs to stage names via filename
for r in records:
    log = r.get("log") or ""
    name = os.path.basename(log).replace(".log", "") if log else "(none)"
    cpu = r["cpu_user_s"] + r["cpu_sys_s"]
    print("%-22s %9.2f %9.1f %9.1f %6d %s" % (
        name, r["wall_s"], cpu, r["maxrss_kb"] / 1024.0, r["rc"], log))

for statf in ("ccache_stats_cold.txt", "ccache_stats_warm.txt"):
    p = os.path.join(EV, statf)
    if os.path.exists(p):
        print("---", statf)
        for ln in open(p):
            if any(k in ln for k in ("hits", "misses", "Hit rate", "Cache size", "Direct")):
                print("   ", ln.rstrip())
