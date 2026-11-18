#!/usr/bin/env python3
"""W9.1 Task 4: full re-verification on the CLEAN branch (wave9/dev-so-clean).
Fresh measurements: production static build + test-core, monolith fallback live,
clean dev-so build, incremental traces (work classification), cycles, no-op, APK parity."""
import subprocess, time, re, os, hashlib, json, statistics

os.chdir("/home/z/my-project/miniandroid")
R = {}

def run(cmd, timeout=900, env=None):
    t0 = time.monotonic()
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout, env=env)
    return time.monotonic() - t0, r.returncode, r.stdout + r.stderr

# 1. production static split build (default) + test-core
w, rc, out = run("make --no-print-directory all -j1")
R["prod_build"] = {"wall_s": round(w, 2), "rc": rc}
w, rc, out = run("make --no-print-directory test-core -j1")
R["prod_test_core"] = {"wall_s": round(w, 2), "rc": rc, "pass": out.count("[PASS]")}
print("prod_build", R["prod_build"], "test_core", R["prod_test_core"])

# 2. monolith fallback (DALVIK_SPLIT=0) live
w, rc, out = run("make --no-print-directory DALVIK_SPLIT=0 all -j1")
R["monolith_build"] = {"wall_s": round(w, 2), "rc": rc}
w, rc, out = run("make --no-print-directory DALVIK_SPLIT=0 test-core -j1")
R["monolith_test_core"] = {"wall_s": round(w, 2), "rc": rc, "pass": out.count("[PASS]")}
out_dir = "/tmp/w9c_monolith_guess"
w, rc, _ = run(f"./build/miniandroid run --max-seconds 60 --frames 3 -o {out_dir} "
               f"/home/z/my-project/upload/handoff_apks/ru.zxalexis.ugaday_15.apk > /tmp/w9c_mono.log 2>&1")
h = hashlib.sha256(open(f"{out_dir}/screenshot.png", "rb").read()).hexdigest()[:24] if os.path.exists(f"{out_dir}/screenshot.png") else ""
R["monolith_guess"] = {"rc": rc, "sha256_24": h, "match_canonical": h.startswith("87fe2676")}
print("monolith", R["monolith_build"], R["monolith_test_core"], R["monolith_guess"])

# 3. clean dev-so build + battery
run("make --no-print-directory dev-so-clean")
w, rc, out = run("make --no-print-directory dev-so -j1")
R["devso_clean_build"] = {"wall_s": round(w, 2), "rc": rc}
w, rc, out = run("make --no-print-directory dev-so-test -j1")
R["devso_battery"] = {"wall_s": round(w, 2), "rc": rc, "pass": out.count("[PASS]")}
print("devso", R["devso_clean_build"], R["devso_battery"])

# 4. incremental traces + cycles
def trace(tu):
    subprocess.run(["touch", f"src/{tu}.cpp"])
    w, rc, out = run("make --no-print-directory dev-so-test -j1")
    return {"wall_s": round(w, 2), "rc": rc,
            "pic_compiles": len(re.findall(r"-c -o build_dev_so/objects/", out)),
            "so_relink": len(re.findall(r"-shared -o build_dev_so/libminiandroid_dalvik\.so", out)),
            "test_exe_relinks": len(re.findall(r"-o build_dev_so/tests/\w+ .*tests/\w+\.cpp", out)),
            "pass": out.count("[PASS]")}
R["traces"] = {}
for tu, k in [("dex/dalvik_opcodes", "opcode"), ("dex/dalvik_interpreter", "interpreter"), ("dex/dalvik_bridge", "bridge")]:
    R["traces"][k] = trace(tu)
    print("trace", k, R["traces"][k])

R["cycles"] = {}
for tu, k, n in [("dex/dalvik_opcodes", "opcode", 3), ("dex/dalvik_interpreter", "interpreter", 3), ("dex/dalvik_bridge", "bridge", 2)]:
    cyc = []
    for i in range(n):
        t = trace(tu)
        cyc.append(t["wall_s"])
    R["cycles"][k] = {"reps": cyc, "median_s": round(statistics.median(cyc), 2),
                      "min_s": round(min(cyc), 2), "max_s": round(max(cyc), 2)}
    print("cycles", k, R["cycles"][k])

# 5. dev-so no-op x3
noop = [run("make --no-print-directory dev-so-test -j1")[0] for _ in range(3)]
R["devso_noop"] = [round(x, 2) for x in noop]

# 6. APK parity on miniandroid_dev
CANON = {"ru.zxalexis.ugaday_15": ("87fe2676", "SUCCESS"), "tech.gaskell.diceroller_1_debug": ("46b07062", "PARTIAL"),
         "com.itsfrz.tictactoe_5": ("d55056a8", "PARTIAL")}
R["apks"] = {}
for a, (c, state) in CANON.items():
    out_dir = f"/tmp/w9c_{a}"
    w, rc, _ = run(f"./build_dev_so/miniandroid_dev run --max-seconds 60 --frames 3 -o {out_dir} "
                   f"/home/z/my-project/upload/handoff_apks/{a}.apk > /tmp/w9c_{a}.log 2>&1", timeout=120)
    h = hashlib.sha256(open(f"{out_dir}/screenshot.png", "rb").read()).hexdigest()[:24] if os.path.exists(f"{out_dir}/screenshot.png") else ""
    R["apks"][a] = {"rc": rc, "sha256_24": h, "match": h.startswith(c), "state": state if h.startswith(c) else "MISMATCH"}
    print("apk", a, R["apks"][a])

# 7. leave production tree fresh
run("make --no-print-directory all -j1")
json.dump(R, open("/tmp/w9_clean_results.json", "w"), indent=1)
print("CLEAN_RESULTS saved")
