#!/usr/bin/env python3
"""s151_trains_batch.py — S151 wave: NEW internet-sourced trains to verdict.
Directive: «ادامه بده قطار های تعداد بالا سورس کد ها اینترنت و سورس».
Runs each F-Droid APK in upload/s151_internet_batch/ (or explicit args):
install -> run real-dalvik -> verdict + screenshot sha16 + uncaught + sqlite count.
Writes evidence/s151_trains/S151_NEWBATCH.json (merge-safe, skip recorded rows).
"""
import hashlib, json, os, re, shutil, subprocess, sys, time

BASE = "/home/z/my-project"
BIN = f"{BASE}/miniandroid/build/miniandroid"
OUTD = f"{BASE}/evidence/s151_trains"
OUT = f"{OUTD}/S151_NEWBATCH.json"
BATCH = f"{BASE}/upload/s151_internet_batch"

def sha16(p):
    try: return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
    except Exception: return None

def load():
    return json.load(open(OUT)) if os.path.exists(OUT) else {"rows": {}}

def save(d):
    tmp = OUT + ".tmp"; json.dump(d, open(tmp, "w"), indent=1); os.replace(tmp, OUT)

def main(apks):
    d = load()
    os.makedirs(OUTD, exist_ok=True)
    for apk in apks:
        name = os.path.basename(apk).replace(".apk", "")
        if name in d["rows"]:
            print(name, "already recorded", flush=True); continue
        st = f"{OUTD}/store_{name}"; shutil.rmtree(st, ignore_errors=True); os.makedirs(st)
        t0 = time.time()
        try:
            r = subprocess.run([BIN, "install", apk, "--data-root", f"{st}/data"],
                               capture_output=True, timeout=240)
        except subprocess.TimeoutExpired:
            d["rows"][name] = {"apk": apk, "install": "TIMEOUT"}; save(d); continue
        rout = (r.stdout or b"").decode("utf-8", "replace") + (r.stderr or b"").decode("utf-8", "replace")
        m = re.search(r'"package":\s*"([\w.]+)"', rout)
        pkg = m.group(1) if m else None
        if not pkg:
            d["rows"][name] = {"apk": apk,
                               "apk_sha16": hashlib.sha256(open(apk,'rb').read()).hexdigest()[:16],
                               "install": "FAIL"}
            save(d); print(name, "install FAIL", flush=True); continue
        o = f"{OUTD}/run_{name}"
        try:
            rr = subprocess.run([BIN, "run", "--package", pkg, "--data-root", f"{st}/data",
                                 "--execution-mode", "real-dalvik", "--dump-view-tree",
                                 "--trace", "--max-seconds", "110", "-o", o],
                                capture_output=True, timeout=240)
        except subprocess.TimeoutExpired:
            d["rows"][name] = {"apk": apk, "package": pkg, "install": "OK", "run": "TIMEOUT"}
            save(d); print(name, pkg, "run TIMEOUT", flush=True); continue
        log = (rr.stdout or b"").decode("utf-8", "replace") + (rr.stderr or b"").decode("utf-8", "replace")
        if os.path.isdir(o):
            open(f"{o}/console.log", "w").write(log)
        m = re.search(r"verdict=([A-Z_]+), first_missing_stage=([A-Z_]+)", log)
        verdict = m.group(1) if m else (re.search(r"verdict=([A-Z_]+)", log).group(1)
                                        if re.search(r"verdict=([A-Z_]+)", log) else None)
        if verdict is None:
            m2 = re.search(r"FRAME_ANALYSIS state=([A-Z_]+)", log)
            verdict = m2.group(1) if m2 else None
        m = re.search(r"([0-9]+) uncaught in-flight exception", log)
        row = {"apk": apk, "apk_sha16": hashlib.sha256(open(apk,'rb').read()).hexdigest()[:16],
               "package": pkg, "seconds": round(time.time() - t0, 1),
               "screenshot_sha16": sha16(f"{o}/screenshot.png"), "verdict": verdict,
               "uncaught": int(m.group(1)) if m else 0,
               "sqlite_mentions": len(re.findall(r'(?i)sqlite', log))}
        d["rows"][name] = row; save(d)
        print(name, pkg, row["screenshot_sha16"], verdict, f'{row["seconds"]}s', flush=True)

def rederive(d):
    """Fill missing verdicts from saved console.log files (current FRAME_ANALYSIS format)."""
    for name, row in d["rows"].items():
        if row.get("verdict"):
            continue
        log_p = f"{OUTD}/run_{name}/console.log"
        if os.path.exists(log_p):
            log = open(log_p, errors="replace").read()
            m = re.search(r"FRAME_ANALYSIS state=([A-Z_]+)", log)
            if m:
                row["verdict"] = m.group(1)
                print(name, "-> rederived", row["verdict"], flush=True)
    save(d)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--rederive":
        rederive(load())
    elif len(sys.argv) > 1:
        main(sys.argv[1:])
    else:
        main(sorted(f"{BATCH}/{f}" for f in os.listdir(BATCH) if f.endswith(".apk")))
