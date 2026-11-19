#!/usr/bin/env python3
"""W10.1 Phase 3: fresh acceptance reruns on the current branch tip (f727991e)."""
import subprocess, time, json, os, resource, hashlib, re

os.chdir("/home/z/my-project/miniandroid")

def run(cmd, timeout=900):
    before = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    t0 = time.monotonic()
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    rss = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss // 1024
    return time.monotonic() - t0, r.returncode, r.stdout + r.stderr, rss

R = {"branch_tip": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()}

# 1. clean dev build + battery + no-op
run("make --no-print-directory dev-so-clean")
w, rc, out, rss = run("make --no-print-directory dev-so -j1")
R["clean_dev_build"] = {"wall_s": round(w, 2), "rc": rc, "peak_rss_mb": rss}
w, rc, out, rss = run("make --no-print-directory dev-so-test -j1")
R["battery"] = {"wall_s": round(w, 2), "rc": rc, "pass": out.count("[PASS]")}
w, rc, out, rss = run("make --no-print-directory dev-so-test -j1")
R["noop"] = {"wall_s": round(w, 2), "rc": rc}
print("clean_dev", R["clean_dev_build"], "battery", R["battery"], "noop", R["noop"], flush=True)

# 2. incremental cycles (fresh, x1 each)
for tu, k in [("dex/dalvik_interpreter", "interpreter"), ("dex/dalvik_bridge", "bridge"), ("dex/dalvik_opcodes", "opcode")]:
    subprocess.run(["touch", f"src/{tu}.cpp"])
    w, rc, out, rss = run("make --no-print-directory dev-so-test -j1")
    R[f"incr_{k}"] = {"wall_s": round(w, 2), "rc": rc,
                      "pic_compiles": len(re.findall(r"-c -o build_dev_so/objects/", out)),
                      "test_exe_relinks": len(re.findall(r"-o build_dev_so/tests/\w+ .*tests/\w+\.cpp", out)),
                      "pass": out.count("[PASS]")}
    print("incr", k, R[f"incr_{k}"], flush=True)

# 3. production static + battery
w, rc, out, rss = run("make --no-print-directory all -j1")
R["prod_build"] = {"wall_s": round(w, 2), "rc": rc}
w, rc, out, rss = run("make --no-print-directory test-core -j1")
R["prod_test_core"] = {"wall_s": round(w, 2), "rc": rc, "pass": out.count("[PASS]")}
print("prod", R["prod_build"], R["prod_test_core"], flush=True)

# 4. monolith fallback (dry-run freshness + battery)
dry = subprocess.run("make --no-print-directory -n DALVIK_SPLIT=0 all 2>/dev/null | grep -cE ' -c -o | -rdynamic|-o build/test'",
                     shell=True, capture_output=True, text=True).stdout.strip()
w, rc, out, rss = run("make --no-print-directory DALVIK_SPLIT=0 test-core -j1")
R["monolith"] = {"stale_commands": dry, "battery_wall_s": round(w, 2), "rc": rc, "pass": out.count("[PASS]")}
print("monolith", R["monolith"], flush=True)

# 5. APK parity x1 each + .so resolution proof
CANON = {"ru.zxalexis.ugaday_15": "87fe2676", "tech.gaskell.diceroller_1_debug": "46b07062", "com.itsfrz.tictactoe_5": "d55056a8"}
R["apks"] = {}
for a, c in CANON.items():
    od = f"/tmp/w101_{a}"
    w, rc, _, _ = run(f"./build_dev_so/miniandroid_dev run --max-seconds 120 --frames 3 -o {od} "
                   f"/home/z/my-project/upload/handoff_apks/{a}.apk > /tmp/w101_{a}.log 2>&1", timeout=150)
    h = hashlib.sha256(open(f"{od}/screenshot.png", "rb").read()).hexdigest()[:24] if os.path.exists(f"{od}/screenshot.png") else ""
    R["apks"][a] = {"rc": rc, "sha256_24": h, "match": h.startswith(c)}
    print("apk", a, R["apks"][a], flush=True)
ldd = subprocess.run("ldd build_dev_so/tests/test_core | grep miniandroid_dalvik", shell=True,
                     capture_output=True, text=True).stdout.strip()
R["so_resolution"] = ldd or "static-resolved"
print("so_resolution:", R["so_resolution"], flush=True)

json.dump(R, open("evidence/wave10/w101_acceptance.json", "w"), indent=1)
print("ACCEPTANCE done")
