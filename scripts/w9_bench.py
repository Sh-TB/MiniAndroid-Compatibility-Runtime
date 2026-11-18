#!/usr/bin/env python3
"""W9 acceptance: incremental dependency traces (B/C/D) + 5-run benchmarks.
Phase decomposition: stepwise make invocations (compile-only / .so relink-only /
battery-exec-only) whose sum equals the full-cycle wall."""
import subprocess, time, re, os, hashlib, json, statistics

os.chdir("/home/z/my-project/miniandroid")

def run(cmd, timeout=600):
    t0 = time.monotonic()
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return time.monotonic() - t0, r.returncode, r.stdout + r.stderr

def cycle(tu, label):
    """touch TU -> full make dev-so-test; classify work from recipe lines."""
    subprocess.run(["touch", f"src/{tu}.cpp"])
    w, rc, out = run("make --no-print-directory dev-so-test -j1")
    compiles = len(re.findall(r"-c -o build_dev_so/objects/", out))
    srelink = len(re.findall(r"-shared -o build_dev_so/libminiandroid_dalvik\.so", out))
    testlinks = len(re.findall(r"-o build_dev_so/tests/\w+ .*tests/\w+\.cpp", out))
    passes = out.count("[PASS]")
    print(f"{label}: rc={rc} {w:.2f}s compiles={compiles} so_relink={srelink} test_links={testlinks} PASS={passes}")
    return w, rc, compiles, srelink, testlinks, passes

def phases(tu):
    """stepwise: PIC compile-only, then .so relink-only, then battery-exec-only."""
    subprocess.run(["touch", f"src/{tu}.cpp"])
    wc, rc1, _ = run(f"make --no-print-directory build_dev_so/objects/{os.path.basename(tu)}.o -j1")
    ws, rc2, _ = run("make --no-print-directory build_dev_so/libminiandroid_dalvik.so -j1")
    wt, rc3, out3 = run("make --no-print-directory dev-so-test -j1")
    ok = rc1 == 0 and rc2 == 0 and rc3 == 0
    print(f"  phases[{tu}]: compile={wc:.2f}s so={ws:.2f}s battery={wt:.2f}s sum={wc+ws+wt:.2f} ok={ok}")
    return wc, ws, wt

R = {"traces": {}, "cycles": {}, "phases": {}, "noop": [], "apks": {}}

# B/C/D dependency traces
for tu, lbl in [("dex/dalvik_opcodes", "B_opcode"), ("dex/dalvik_interpreter", "C_interpreter"), ("dex/dalvik_bridge", "D_bridge")]:
    w, rc, c, s, t, p = cycle(tu, lbl)
    R["traces"][lbl] = {"wall_s": round(w, 2), "rc": rc, "pic_compiles": c, "so_relink": s, "test_exe_relinks": t, "battery_pass": p}

# 5-run benchmarks: interpreter, opcode; bridge 3 reps (40s each)
for tu, n in [("dex/dalvik_interpreter", 5), ("dex/dalvik_opcodes", 5), ("dex/dalvik_bridge", 3)]:
    cyc = [cycle(tu, f"cycle[{os.path.basename(tu)}] r{i+1}")[0] for i in range(n)]
    ph = [phases(tu) for _ in range(2)]
    R["cycles"][tu] = [round(x, 2) for x in cyc]
    R["phases"][tu] = [[round(v, 2) for v in p] for p in ph]
    print(f"  => {tu}: median={statistics.median(cyc):.2f} min={min(cyc):.2f} max={max(cyc):.2f}")

# no-op x5 (everything fresh)
for i in range(5):
    w, rc, _ = run("make --no-print-directory dev-so-test -j1")
    R["noop"].append(round(w, 2))
print(f"no-op dev-so-test x5: {R['noop']} median={statistics.median(R['noop']):.2f}s")

# Test F: original APKs on the make-built miniandroid_dev
CANON = {"ru.zxalexis.ugaday_15": ("87fe2676", "SUCCESS"), "tech.gaskell.diceroller_1_debug": ("46b07062", "PARTIAL"),
         "com.itsfrz.tictactoe_5": ("d55056a8", "PARTIAL")}
for a, (canon, state) in CANON.items():
    out = f"/tmp/w9_{a}"
    w, rc, _ = run(f"./build_dev_so/miniandroid_dev run --max-seconds 60 --frames 3 -o {out} "
                   f"/home/z/my-project/upload/handoff_apks/{a}.apk > /tmp/w9_{a}.log 2>&1", timeout=120)
    h = hashlib.sha256(open(f"{out}/screenshot.png", "rb").read()).hexdigest()[:24] if os.path.exists(f"{out}/screenshot.png") else ""
    R["apks"][a] = {"rc": rc, "sha256_24": h, "canonical": canon, "match": h.startswith(canon),
                    "state": state if h.startswith(canon) else "MISMATCH", "wall_s": round(w, 2)}
    print(f"APK {a}: rc={rc} sha={h} match={R['apks'][a]['match']} ({state})")

json.dump(R, open("/tmp/w9_results.json", "w"), indent=1)
print("W9RESULTS saved")
