#!/usr/bin/env python3
"""cont11_newbatch.py — CONT-11 new-program frontier: install + run arbitrary
fdroid_batch APKs to verdict, one row each (fresh store). Usage:
  python3 scripts/cont11_newbatch.py <apk1> [apk2 ...]
Writes evidence/cont11/CONT11_NEWBATCH.json (merge-safe).
"""
import hashlib, json, os, re, shutil, subprocess, sys, time

BASE = "/home/z/my-project"
BIN = f"{BASE}/miniandroid/build/miniandroid"
OUT = f"{BASE}/evidence/cont11/CONT11_NEWBATCH.json"

def sha16(p):
    try: return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
    except Exception: return None

def load():
    return json.load(open(OUT)) if os.path.exists(OUT) else {"rows": {}}

def save(d):
    tmp = OUT + ".tmp"; json.dump(d, open(tmp, "w"), indent=1); os.replace(tmp, OUT)

def main(apks):
    d = load()
    for apk in apks:
        name = os.path.basename(apk).replace(".apk", "")
        if name in d["rows"]:
            print(name, "already recorded"); continue
        st = f"/tmp/nb/{name}"; shutil.rmtree(st, ignore_errors=True); os.makedirs(st)
        t0 = time.time()
        r = subprocess.run([BIN, "install", apk, "--data-root", f"{st}/data"],
                           capture_output=True, timeout=240)
        rout = (r.stdout or b"").decode("utf-8", "replace") + (r.stderr or b"").decode("utf-8", "replace")
        m = re.search(r'"package":\s*"([\w.]+)"', rout)
        pkg = m.group(1) if m else None
        if not pkg:
            d["rows"][name] = {"apk_sha256": hashlib.sha256(open(apk,'rb').read()).hexdigest(),
                               "install": "FAIL"}
            save(d); print(name, "install FAIL"); continue
        o = f"{st}/run1"
        rr = subprocess.run([BIN, "run", "--package", pkg, "--data-root", f"{st}/data",
                             "--execution-mode", "real-dalvik", "--dump-view-tree",
                             "--trace", "--max-seconds", "110", "-o", o],
                            capture_output=True, timeout=240)
        log = (rr.stdout or b"").decode("utf-8", "replace") + (rr.stderr or b"").decode("utf-8", "replace")
        open(f"{o}/console.log", "w") if os.path.isdir(o) else None
        if os.path.isdir(o):
            open(f"{o}/console.log", "w").write(log)
        m = re.search(r"verdict=([A-Z_]+), first_missing_stage=([A-Z_]+)", log)
        verdict = m.group(1) if m else (re.search(r"verdict=([A-Z_]+)", log).group(1)
                                        if re.search(r"verdict=([A-Z_]+)", log) else None)
        m = re.search(r"([0-9]+) uncaught in-flight exception", log)
        row = {"apk": apk, "apk_sha256": hashlib.sha256(open(apk,'rb').read()).hexdigest(),
               "package": pkg, "seconds": round(time.time() - t0, 1),
               "screenshot_sha16": sha16(f"{o}/screenshot.png"), "verdict": verdict,
               "uncaught": int(m.group(1)) if m else 0,
               "sqlite_mentions": len(re.findall(r'(?i)sqlite', log))}
        d["rows"][name] = row; save(d)
        print(name, pkg, row["screenshot_sha16"], verdict, f'{row["seconds"]}s', flush=True)

if __name__ == "__main__":
    main(sys.argv[1:])
