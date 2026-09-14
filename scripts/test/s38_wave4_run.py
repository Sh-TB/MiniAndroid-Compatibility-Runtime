#!/usr/bin/env python3
"""S38-C wave 4: re-run the 4 S37 budget-timeout APKs at 900s + hello fixtures
+ the shift-law probe. Re-created after container reset."""
import hashlib
import json
import subprocess
import time
from pathlib import Path

REPO = Path("/home/z/my-project")
BIN = REPO / "miniandroid/build/miniandroid"
CACHE = Path("/tmp/my-project/apk_cache")
WORK = Path("/tmp/s38_runs")

QUEUE = [
    ("secuso_sudoku",  CACHE / "s36new/org.secuso.privacyfriendlysudoku_19.apk"),
    ("secuso_memory",  CACHE / "s36new/org.secuso.privacyfriendlymemory_8.apk"),
    ("wordgame_nian",  CACHE / "s37new/com.wordgame.nian_11.apk"),
    ("minesweep_joeld", CACHE / "s37new/com.joeld.minesweeper_7.apk"),
    # fixture family: probe-click law evidence + NEW shift-law probe
    ("hello_smoke",    Path("/tmp/hello_smoke.apk")),
    ("hello_widgets",  Path("/tmp/hello_widgets.apk")),
    ("s38_shiftlaw",   Path("/tmp/s38_shiftlaw.apk")),
]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def run_one(name, apk, timeout):
    out = WORK / name
    out.mkdir(parents=True, exist_ok=True)
    if not apk.exists():
        return {"name": name, "status": "NO_APK", "apk": str(apk)}
    t0 = time.time()
    rc = -1
    try:
        proc = subprocess.run([str(BIN), "run", str(apk), "-o", str(out)],
                              capture_output=True, text=True, timeout=timeout)
        rc = proc.returncode
        log = (proc.stdout or "") + (proc.stderr or "")
    except subprocess.TimeoutExpired:
        log = f"TIMEOUT after {timeout}s"
        rc = 124
    (out / "console.log").write_text(log[:200000])
    status = ("SUCCESS" if "Status: SUCCESS" in log else
              "PARTIAL" if "Status:" in log else
              ("TIMEOUT" if rc == 124 else "CRASH"))
    shot = out / "screenshot.png"
    return {
        "name": name, "apk": str(apk), "apk_sha256": sha256(apk),
        "rc": rc, "status": status, "seconds": round(time.time() - t0, 1),
        "screenshot": shot.exists(),
        "screenshot_sha256": sha256(shot) if shot.exists() else None,
        "console_tail": log[-800:],
    }


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    res = {}
    # shift-law probe FIRST (fast, decisive for R-NEW-335)
    for name, apk in sorted(QUEUE, key=lambda q: 0 if q[0] == "s38_shiftlaw" else 1):
        r = run_one(name, apk, 900)
        res[name] = r
        print(f"[{r['status']:>7}] {name:<20} {r.get('seconds','?'):>7}s "
              f"{'IMG' if r.get('screenshot') else '---'} "
              f"apk={r.get('apk_sha256','')[:12]}", flush=True)
        (WORK / "s38_wave4_summary.json").write_text(json.dumps(res, indent=1))
    print("DONE", {k: v["status"] for k, v in res.items()})


if __name__ == "__main__":
    main()
