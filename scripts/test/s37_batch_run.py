#!/usr/bin/env python3
"""S37 corpus batch runner — MASTER CAMPAIGN 3.

Runs every queued APK through the ONE canonical runtime entry point
(./miniandroid run <apk> -o <out>), captures status/screenshot/hashes,
writes /tmp/s37_runs/<name>.result.json. No package branches, no fixture
logic — same law as g09_corpus_runner. Ledger rows get added from results.

Usage: python3 scripts/test/s37_batch_run.py [--timeout 540] [name:apk ...]
Default: runs the full S37 queue (wave-2 pending rows 22-27 + wave-3 new).
"""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MA = REPO / "miniandroid"
BIN = MA / "build" / "miniandroid"
CACHE = Path("/tmp/my-project/apk_cache")
WORK = Path("/tmp/s37_runs")

QUEUE = [
    # wave-2 ledger rows 22-27 (downloaded+hashed in S36, runs pending)
    ("dooz_vc23",      CACHE / "s36new/io.github.yamin8000.dooz_23.apk"),
    ("bouncycastle",   CACHE / "s36new/com.inspiredandroid.braincup_158.apk"),
    ("solitaire",      CACHE / "s36new/de.tobiasbielefeld.solitaire_69.apk"),
    ("secuso_sudoku",  CACHE / "s36new/org.secuso.privacyfriendlysudoku_19.apk"),
    ("bouncy",         CACHE / "s36new/com.dozingcatsoftware.bouncy_39.apk"),
    ("secuso_memory",  CACHE / "s36new/org.secuso.privacyfriendlymemory_8.apk"),
    # wave-3 (S37 new downloads)
    ("minesweep_johnathan", CACHE / "s37new/io.github.johnathan.minesweeper_6.apk"),
    ("game2048",           CACHE / "s37new/org.andstatus.game2048_47.apk"),
    ("diceoverflow",       CACHE / "s37new/eu.veldsoft.dice.overflow_2.apk"),
    ("wordgame_nian",      CACHE / "s37new/com.wordgame.nian_11.apk"),
    ("secuso_yahtzee",     CACHE / "s37new/org.secuso.privacyfriendlyyahtzeedicer_100.apk"),
    ("minesweep_joeld",    CACHE / "s37new/com.joeld.minesweeper_7.apk"),
    ("edgeroll",           CACHE / "s37new/edge.roll_11.apk"),
    ("sidhant_puzzle",     CACHE / "s37new/com.sidhant.puzzle_293.apk"),
    ("thesuncat_sudoku",   CACHE / "s37new/com.thesuncat.sudoku_4.apk"),
    # cached legacy tictactoe/dooz variants (older/simpler models, user priority)
    ("tictactoe_legacy",   CACHE / "corpus/tictactoe.apk"),
    ("tictactoe_classic",  CACHE / "corpus/tictactoeclassic.apk"),
    ("dooz_gvariant",      CACHE / "corpus/dooztictactoegvariant.apk"),
    ("dooz_variant",       CACHE / "corpus/dooztictactoevariant.apk"),
]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def run_one(name: str, apk: Path, timeout: int) -> dict:
    out = WORK / name
    out.mkdir(parents=True, exist_ok=True)
    if not apk.exists():
        return {"name": name, "apk": str(apk), "status": "NO_APK"}
    t0 = time.time()
    log = ""
    rc = -1
    try:
        proc = subprocess.run([str(BIN), "run", str(apk), "-o", str(out)],
                              capture_output=True, text=True, timeout=timeout)
        rc = proc.returncode
        log = (proc.stdout or "") + (proc.stderr or "")
    except subprocess.TimeoutExpired as e:
        log = f"TIMEOUT after {timeout}s\n" + ((e.stdout or b"").decode(errors="ignore")
                                                if isinstance(e.stdout, bytes) else str(e.stdout or ""))
        rc = 124
    except Exception as e:  # noqa: BLE001
        log = f"RUNNER-ERROR {e}"
    (out / "console.log").write_text(log[:200000])
    status = "SUCCESS" if "Status: SUCCESS" in log else (
        "PARTIAL" if "Status:" in log else ("TIMEOUT" if rc == 124 else "CRASH"))
    shot = out / "screenshot.png"
    res = {
        "name": name, "apk": str(apk),
        "apk_sha256": sha256(apk),
        "rc": rc, "status": status, "seconds": round(time.time() - t0, 1),
        "screenshot": bool(shot.exists()),
        "screenshot_sha256": sha256(shot) if shot.exists() else None,
        "console_tail": log[-1200:],
    }
    (WORK / f"{name}.result.json").write_text(json.dumps(res, indent=1))
    return res


def main():
    timeout = 540
    args = sys.argv[1:]
    if args and args[0] == "--timeout":
        timeout = int(args[1]); args = args[2:]
    queue = QUEUE
    if args:
        wanted = set(args)
        queue = [q for q in QUEUE if q[0] in wanted]
    WORK.mkdir(parents=True, exist_ok=True)
    done = {}
    for name, apk in queue:
        r = run_one(name, apk, timeout)
        done[name] = r
        shot = "IMG" if r.get("screenshot") else "---"
        print(f"[{r['status']:>7}] {name:<22} {r.get('seconds','?'):>6}s {shot} "
              f"apk_sha={r.get('apk_sha256','')[:12]}", flush=True)
    (WORK / "s37_results_summary.json").write_text(json.dumps(done, indent=1))
    n_img = sum(1 for r in done.values() if r.get("screenshot"))
    print(f"\nDONE: {len(done)} runs, {n_img} with screenshot, "
          f"{sum(1 for r in done.values() if r['status']=='SUCCESS')} SUCCESS")


if __name__ == "__main__":
    main()
