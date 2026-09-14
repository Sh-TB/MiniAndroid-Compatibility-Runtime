#!/usr/bin/env python3
"""S38 wave-4: re-run 6-APK attack queue (4 corpus retries @900s + 2 hello fixtures).
Outputs /tmp/s38_runs/s38_wave4_summary.json + per-run dirs with screenshot/console."""
import subprocess, os, json, hashlib, time, sys

RUNNER = "/home/z/my-project/miniandroid/build/miniandroid"
OUTBASE = "/tmp/s38_runs/wave4"
QUEUE = [
    ("secuso_sudoku",    "/tmp/my-project/apk_cache/s36new/org.secuso.privacyfriendlysudoku_19.apk", 900),
    ("secuso_memory",    "/tmp/my-project/apk_cache/s36new/org.secuso.privacyfriendlymemory_8.apk", 900),
    ("wordgame_nian",    "/tmp/my-project/apk_cache/s37new/com.wordgame.nian_11.apk", 900),
    ("minesweep_joeld",  "/tmp/my-project/apk_cache/s37new/com.joeld.minesweeper_7.apk", 900),
    ("hello_smoke",      "/tmp/hello_smoke.apk", 120),
    ("hello_widgets",    "/tmp/hello_widgets.apk", 120),
    ("scroll_min",       "/tmp/scroll_min.apk", 120),
]
PHASE = sys.argv[1] if len(sys.argv) > 1 else "all"
if PHASE == "fixtures":
    QUEUE = [q for q in QUEUE if q[2] <= 300]
elif PHASE == "corpus":
    QUEUE = [q for q in QUEUE if q[2] > 300]

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

os.makedirs(OUTBASE, exist_ok=True)
results = []
for i, (name, apk, budget) in enumerate(QUEUE, 1):
    if not os.path.exists(apk):
        results.append({"name": name, "status": "MISSING-APK", "apk": apk})
        continue
    outdir = os.path.join(OUTBASE, name)
    os.makedirs(outdir, exist_ok=True)
    apk_sha = sha256(apk)
    t0 = time.time()
    cmd = [RUNNER, "run", apk, "-o", outdir]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=budget + 90)
        rc = p.returncode
        cout = (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired as e:
        rc = -999
        cout = "RUNNER-TIMEOUT wall=%ds" % (time.time() - t0)
    wall = round(time.time() - t0, 1)
    shot = os.path.join(outdir, "screenshot.png")
    rep = os.path.join(outdir, "report.md")
    con = os.path.join(outdir, "console.log")
    entry = {
        "name": name,
        "apk": apk,
        "apk_sha256": apk_sha,
        "rc": rc,
        "wall_s": wall,
        "budget_s": budget,
        "screenshot": shot if os.path.exists(shot) else None,
        "screenshot_sha256": sha256(shot)[:16] if os.path.exists(shot) else None,
        "report_exists": os.path.exists(rep),
        "console_tail": (open(con).read()[-600:] if os.path.exists(con) else cout[-600:]),
    }
    # status classification
    if rc == 0 and entry["screenshot"]:
        entry["status"] = "SUCCESS"
    elif entry["screenshot"]:
        entry["status"] = "PARTIAL-IMG"
    else:
        entry["status"] = "FAIL"
    results.append(entry)
    print("[%d/%d] %-16s rc=%-5d wall=%-7s %s" % (i, len(QUEUE), name, rc, wall, entry["status"]), flush=True)

summary_path = "/tmp/s38_runs/s38_wave4_summary.json"
with open(summary_path, "w") as f:
    json.dump({"results": results, "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}, f, indent=2)
print("WAVE4-DONE ->", summary_path, flush=True)
