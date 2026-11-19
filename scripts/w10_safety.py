#!/usr/bin/env python3
"""W10 Phase 6: build safety — production static, monolith fallback, clean dev-so,
no-op, rollback. All timings + battery results recorded."""
import subprocess, time, json, os, resource

os.chdir("/home/z/my-project/miniandroid")

def run(cmd, timeout=900):
    before = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    t0 = time.monotonic()
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    rss = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss // 1024
    return time.monotonic() - t0, r.returncode, r.stdout + r.stderr, rss

R = {}
# 1. production static build (catch-up after harness touches) + battery
w, rc, out, rss = run("make --no-print-directory all -j1")
R["prod_build"] = {"wall_s": round(w, 2), "rc": rc, "peak_rss_mb": rss}
w, rc, out, rss = run("make --no-print-directory test-core -j1")
R["prod_test_core"] = {"wall_s": round(w, 2), "rc": rc, "pass": out.count("[PASS]")}
print("prod", R["prod_build"], R["prod_test_core"], flush=True)

# 2. monolith fallback (live) + battery
w, rc, out, rss = run("make --no-print-directory DALVIK_SPLIT=0 all -j1")
R["monolith_build"] = {"wall_s": round(w, 2), "rc": rc, "peak_rss_mb": rss}
w, rc, out, rss = run("make --no-print-directory DALVIK_SPLIT=0 test-core -j1")
R["monolith_test_core"] = {"wall_s": round(w, 2), "rc": rc, "pass": out.count("[PASS]")}
print("monolith", R["monolith_build"], R["monolith_test_core"], flush=True)

# 3. clean dev-so build with wave-10 profiles
run("make --no-print-directory dev-so-clean")
w, rc, out, rss = run("make --no-print-directory dev-so -j1")
R["devso_clean_build"] = {"wall_s": round(w, 2), "rc": rc, "peak_rss_mb": rss}
w, rc, out, rss = run("make --no-print-directory dev-so-test -j1")
R["devso_battery"] = {"wall_s": round(w, 2), "rc": rc, "pass": out.count("[PASS]")}
w, rc, out, rss = run("make --no-print-directory dev-so-test -j1")
R["devso_noop"] = {"wall_s": round(w, 2), "rc": rc}
print("devso", R["devso_clean_build"], R["devso_battery"], R["devso_noop"], flush=True)

# 4. restore production tree freshness (monolith objects -> split default)
w, rc, out, rss = run("make --no-print-directory all -j1")
R["prod_restore"] = {"wall_s": round(w, 2), "rc": rc}
print("restore", R["prod_restore"], flush=True)

json.dump(R, open("evidence/wave10/w10_build_safety_raw.json", "w"), indent=1)
print("SAFETY done")
