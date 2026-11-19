#!/usr/bin/env python3
"""W10 verification: new dev-so speed profiles -> battery + 3-APK parity x3 + cycle traces."""
import subprocess, time, hashlib, os, json, resource, re

os.chdir("/home/z/my-project/miniandroid")
R = {}

def run(cmd, timeout=900):
    t0 = time.monotonic()
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return time.monotonic() - t0, r.returncode, r.stdout + r.stderr

# A. rebuild dev-so with new flags + battery
w, rc, out = run("make --no-print-directory dev-so -j1")
R["devso_rebuild"] = {"wall_s": round(w, 2), "rc": rc}
w, rc, out = run("make --no-print-directory dev-so-test -j1")
R["battery"] = {"wall_s": round(w, 2), "rc": rc, "pass": out.count("[PASS]")}
print("devso", R["devso_rebuild"], "battery", R["battery"], flush=True)

# B. 3-APK parity x3 reps
CANON = {"ru.zxalexis.ugaday_15": ("87fe2676", "SUCCESS"),
         "tech.gaskell.diceroller_1_debug": ("46b07062", "PARTIAL"),
         "com.itsfrz.tictactoe_5": ("d55056a8", "PARTIAL")}
R["apks"] = {}
for a, (canon, state) in CANON.items():
    reps = []
    for i in range(3):
        od = f"/tmp/w10_{a}_{i}"
        w, rc, _ = run(f"./build_dev_so/miniandroid_dev run --max-seconds 120 --frames 3 -o {od} "
                       f"/home/z/my-project/upload/handoff_apks/{a}.apk > /tmp/w10_{a}_{i}.log 2>&1", timeout=150)
        h = hashlib.sha256(open(f"{od}/screenshot.png", "rb").read()).hexdigest()[:24] \
            if os.path.exists(f"{od}/screenshot.png") else ""
        reps.append({"rc": rc, "sha256_24": h, "match": h.startswith(canon), "wall_s": round(w, 2)})
        print(f"APK {a} r{i+1}: rc={rc} sha={h} match={reps[-1]['match']} {w:.1f}s", flush=True)
    R["apks"][a] = {"canonical": canon, "expected_class": state, "reps": reps,
                    "all_match": all(r["match"] for r in reps),
                    "hashes_identical_across_reps": len({r["sha256_24"] for r in reps}) == 1}
print(json.dumps({a: {"all_match": v["all_match"], "stable": v["hashes_identical_across_reps"]}
                  for a, v in R["apks"].items()}), flush=True)

# C. cycle traces (single run each; x5 in the harness later)
def trace(tu):
    subprocess.run(["touch", f"src/{tu}.cpp"])
    w, rc, out = run("make --no-print-directory dev-so-test -j1")
    return {"wall_s": round(w, 2), "rc": rc,
            "pic_compiles": len(re.findall(r"-c -o build_dev_so/objects/", out)),
            "so_relink": len(re.findall(r"-shared -o build_dev_so/libminiandroid_dalvik\.so", out)),
            "test_exe_relinks": len(re.findall(r"-o build_dev_so/tests/\w+ .*tests/\w+\.cpp", out)),
            "pass": out.count("[PASS]")}
R["traces"] = {}
for tu, k in [("dex/dalvik_interpreter", "interpreter"), ("dex/dalvik_bridge", "bridge"), ("dex/dalvik_opcodes", "opcode")]:
    R["traces"][k] = trace(tu)
    print("trace", k, R["traces"][k], flush=True)

json.dump(R, open("evidence/wave10/w10_verify_raw.json", "w"), indent=1)
print("VERIFY done")
