#!/usr/bin/env python3
"""FINAL Phase 5: execute one original APK through the real runtime with evidence capture.
Usage: f_phase5_run.py <apk-file> <outdir-root> <mode> [tap x y [tap2 x2 y2 ...]]
modes: launch | tap | verify   (tap: taps then captures second screen; verify: repeat launch for reproducibility)
"""
import subprocess, hashlib, json, os, sys, time

BIN = "/home/z/my-project/miniandroid/build_dev_so/miniandroid_dev"
APK = sys.argv[1]
ROOT = sys.argv[2]
MODE = sys.argv[3]
TAPS = sys.argv[4:]
os.makedirs(ROOT, exist_ok=True)

def sh(cmd, timeout=180):
    t0 = time.monotonic()
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return time.monotonic() - t0, r.returncode, (r.stdout + r.stderr)

def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest() if os.path.exists(p) else ""

def metrics(p):
    try:
        from PIL import Image
        im = Image.open(p).convert("L")
        h = im.histogram()
        return {"w": im.size[0], "h": im.size[1],
                "nonwhite": round(1 - h[255] / max(1, sum(h)), 4)}
    except Exception as e:
        return {"err": str(e)}

res = {"apk": os.path.basename(APK), "mode": MODE, "taps": TAPS}

if MODE == "analyze":
    w, rc, out = sh(f"{BIN} analyze {APK}")
    res.update({"wall_s": round(w, 1), "rc": rc, "analyze": out[-2200:]})
else:
    od = os.path.join(ROOT, MODE + ("_" + "_".join(TAPS) if TAPS else ""))
    tapargs = "".join(f" --tap {t}" for t in [",".join(TAPS[i:i+2]) for i in range(0, len(TAPS), 2)]) if MODE == "tap" and TAPS else ""
    click = " --click-test" if MODE == "launch" else ""
    cmd = (f"{BIN} run --max-seconds 150 --frames 60 --trace -o {od} "
           f"--data-root {ROOT}/data --execution-mode real-dalvik{click}{tapargs} {APK}")
    w, rc, out = sh(cmd)
    shot = os.path.join(od, "screenshot.png")
    res.update({"wall_s": round(w, 1), "rc": rc, "outdir": od,
                "screenshot_sha256": sha(shot), "metrics": metrics(shot) if shot else {},
                "log_tail": out[-1600:]})
    tr = os.path.join(od, "trace.jsonl")
    if os.path.exists(tr):
        lines = open(tr, errors="replace").read().splitlines()
        res["trace_lines"] = len(lines)
        exc = [l[:220] for l in lines if any(k in l.lower() for k in
               ("exception", "unimplemented", "not implemented", "stub", "missing", "fail"))][:12]
        res["trace_first_failures"] = exc
        res["trace_events_head"] = [l[:200] for l in lines[:14]]
    files = sorted(os.listdir(od)) if os.path.isdir(od) else []
    res["outdir_files"] = files

print(json.dumps(res, indent=1))
json.dump(res, open(os.path.join(ROOT, f"result_{MODE}.json"), "w"), indent=1)
