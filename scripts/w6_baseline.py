#!/usr/bin/env python3
"""W6 Phase 0: baseline snapshot -> evidence/wave6/w6_baseline.json
Records HEAD, tree status, safety tags, build mode, compiler version,
per-TU flag samples, RAM limit, build command, linker configuration.
No compilation is triggered (read-only probe)."""
import json, os, re, subprocess

os.chdir("/home/z/my-project/miniandroid")
EV = "evidence/wave6"
os.makedirs(EV, exist_ok=True)

def run(cmd, timeout=120):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return (r.stdout + r.stderr).strip()

b = {}
b["git_head"] = run(["git", "rev-parse", "HEAD"])
b["git_head_short"] = b["git_head"][:8]
b["git_status"] = run(["git", "status", "--porcelain"]).splitlines()
b["safety_tags"] = [t for t in run(["git", "tag", "-l", "safety/*"]).splitlines()]
b["wave5_commits_present"] = {
    "0a03944b": run(["git", "log", "--oneline", "-9"]).count("0a03944b") > 0,
    "a4d38745": run(["git", "log", "--oneline", "-9"]).count("a4d38745") > 0,
    "9983941b": run(["git", "log", "--oneline", "-9"]).count("9983941b") > 0,
}
b["build_scripts_present"] = {
    f: os.path.exists(f"/home/z/my-project/scripts/{f}")
    for f in ["w4_split.py", "w5_gates.py", "w5_dev_loop.py", "w5_roundtrip.py"]}
b["build_mode"] = {
    "DALVIK_SPLIT": "1 (default in Makefile)",
    "split_parts": 7,
    "DEV": "0 (production); DEV=1 writes to build_dev/ (verified wave-5)",
    "binary_mtime": run(["bash", "-c", "stat -c %y build/miniandroid 2>/dev/null"]),
}
b["compiler"] = run(["g++", "--version"]).splitlines()[0]
b["host"] = {
    "cpu_count": os.cpu_count(),
    "mem_total_mb": int(re.search(r"MemTotal:\s+(\d+)",
                                  open("/proc/meminfo").read()).group(1)) // 1024,
    "mem_available_mb": int(re.search(r"MemAvailable:\s+(\d+)",
                                      open("/proc/meminfo").read()).group(1)) // 1024,
}
for cg in ["/sys/fs/cgroup/memory.max", "/sys/fs/cgroup/memory/memory.limit_in_bytes"]:
    if os.path.exists(cg):
        b["host"]["cgroup_memory_max"] = open(cg).read().strip()
        break
mk = run(["make", "--no-print-directory", "-n", "-B", "all"], timeout=180)
comp = sorted(set(l.strip() for l in mk.splitlines() if " -c -o " in l))
link = [l.strip() for l in mk.splitlines() if " -o build/miniandroid" in l
        and " -c " not in l]
b["linker_command"] = link[0] if link else "NOT FOUND"
b["link_summary"] = {
    "driver": "g++",
    "object_count": len([l for l in mk.splitlines() if " -c -o " in l]),
    "static_objects": True,
    "test_binary_link": "same static object set into build/miniandroid_test (115MB, ~11.7s relink)",
}
# per-TU flag samples (exact commands, abbreviated)
def abbrev(cmd):
    return re.sub(r"-I \S+", "-I<inc>", cmd)
b["flag_samples"] = {
    "dalvik_part": abbrev(next((l for l in comp if "dalvik_opcodes.cpp" in l), "")),
    "bridge_-Og": abbrev(next((l for l in comp if "dalvik_bridge.cpp" in l), "")),
    "generic_tu": abbrev(next((l for l in comp if "class_resolver.cpp" in l), "")),
    "quickjs": abbrev(next((l for l in comp if "quickjs" in l and " -c " in l), ""))[:400],
}
b["monolith_fallback"] = {
    "command": "make DALVIK_SPLIT=0 -j1 all",
    "wave5_measured": {"wall_s": 215.1, "peak_mb": 2869, "rc": 0},
    "wave3_mono_binary_leftover": os.path.exists("/tmp/w3_cmake_mono/miniandroid"),
}
b["wave5_gate_reference"] = {
    "noop_s": 1.07, "opcode_field_edit_s": 12.79, "opcode_invoke_edit_s": 17.51,
    "two_opcode_edit_s": 26.35, "interpreter_edit_s": 40.78, "bridge_edit_s": 47.67,
    "header_touch_s": 158.21, "link_only_s": 2.16, "dev_loop_s": 21.36,
    "clean_split_s": 504.3, "clean_split_peak_mb": 2126,
    "screenshot_hashes": {"guess": "87fe26766fc48d06c59d4c15",
                          "tictactoe": "d55056a8928a26ffeb15f66d",
                          "diceroller": "46b07062ba6fe36ca8a6e42d"},
}
json.dump(b, open(f"{EV}/w6_baseline.json", "w"), indent=1)
print(json.dumps({k: b[k] for k in ["git_head_short", "compiler", "host",
                                    "flag_samples"] if k in b}, indent=1)[:1200])
print("baseline written:", f"{EV}/w6_baseline.json")
