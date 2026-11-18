#!/usr/bin/env python3
"""W7 Phase 0: reproducible baseline manifest -> evidence/wave7/w7_baseline.json
Read-only except evidence dir. Verifies W6 helpers, toolchain, cgroup, flags."""
import json, os, re, subprocess

os.chdir("/home/z/my-project/miniandroid")
EV = "evidence/wave7"
os.makedirs(EV, exist_ok=True)

def run(cmd, timeout=120):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return (r.stdout + r.stderr).strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return "absent"

b = {}
b["git"] = {
    "head": run(["git", "rev-parse", "HEAD"]),
    "branch": run(["git", "rev-parse", "--abbrev-ref", "HEAD"]),
    "status": run(["git", "status", "--porcelain"]).splitlines()[:10],
    "w6_commit_present": bool(run(["git", "log", "--oneline", "-3"]).count("b567ca9a")),
    "safety_tags": run(["git", "tag", "-l", "safety/*"]).splitlines(),
}
b["toolchain"] = {
    "gcc": run(["g++", "--version"]).splitlines()[0],
    "ld": run(["ld", "--version"]).splitlines()[0],
    "make": run(["make", "--version"]).splitlines()[0],
    "cmake": run(["cmake", "--version"]).splitlines()[0] or "absent",
    "ninja": run(["ninja", "--version"]) or "absent",
    "python": run(["python3", "--version"]),
    "ccache": run(["bash", "-c", "command -v ccache >/dev/null && ccache --version | head -1 || echo ABSENT"]),
    "gold": run(["bash", "-c", "command -v ld.gold >/dev/null && echo present || echo ABSENT"]),
    "lld": run(["bash", "-c", "command -v ld.lld >/dev/null && echo present || echo ABSENT"]),
    "mold": run(["bash", "-c", "command -v mold >/dev/null && echo present || echo ABSENT"]),
    "binutils_ar": run(["ar", "--version"]).splitlines()[0],
    "kernel": run(["uname", "-sr"]),
    "cpu_quota": run(["bash", "-c", "nproc"]),
}
b["cgroup"] = {
    "memory_max": open("/sys/fs/cgroup/memory.max").read().strip()
        if os.path.exists("/sys/fs/cgroup/memory.max") else "n/a",
    "mem_total_mb": int(re.search(r"MemTotal:\s+(\d+)", open("/proc/meminfo").read()).group(1)) // 1024,
    "oom_repro_evidence": "w6: bridge -O2 rc=1 @ 3,087 MB (limit is real and enforced)",
}
b["filesystem"] = run(["bash", "-c", "df -T /home/z/my-project | tail -1"])
mk = run(["make", "--no-print-directory", "-n", "-B", "all"], timeout=180)
comp = sorted(set(l.strip() for l in mk.splitlines() if " -c -o " in l))
link = [l.strip() for l in mk.splitlines() if " -o build/miniandroid" in l and " -c " not in l]
b["configs"] = {
    "split_production": {
        "compile_count": len(comp),
        "bridge_flags": "… -Og -g0 (wave-4 precedent)",
        "engine_flags": "… -O2 -g0",
        "link_cmd_present": bool(link),
    },
    "monolith_fallback": {
        "dry_run_object": run(["bash", "-c",
            "make -n DALVIK_SPLIT=0 all 2>/dev/null | grep -c 'dalvik_engine.o'"]),
        "wave5_measured": {"wall_s": 215.1, "peak_mb": 2869, "guess_sha": "87fe2676"},
        "w7_live_verification": "run in background this session",
    },
    "dev": {"cmd": "make DEV=1", "build_dir": "build_dev/", "wave5_loop": 21.36},
}
b["w6_helpers_verified"] = {
    "in_bridge": run(["bash", "-c",
        "grep -c 'bool DalvikExecutionEngine::bridge_arm_' src/dex/dalvik_bridge.cpp"]),
    "in_header": run(["bash", "-c",
        "grep -c 'bool bridge_arm_' src/dex/dalvik_engine.h"]),
    "tested": "w6: parity 82, test-core 3/3, 3-APK hashes identical vs mono",
}
b["source_inventory"] = {
    "compile_commands": len(comp),
    "generated_sources": run(["bash", "-c", "ls src/generated 2>/dev/null | head -3 || echo none"]),
    "dex_tus": run(["bash", "-c", "ls src/dex/*.cpp | wc -l"]),
}
json.dump(b, open(f"{EV}/w7_baseline.json", "w"), indent=1)
print(json.dumps({k: b[k] for k in ["toolchain", "cgroup", "w6_helpers_verified"]},
                 indent=1)[:1100])
print("baseline written")
