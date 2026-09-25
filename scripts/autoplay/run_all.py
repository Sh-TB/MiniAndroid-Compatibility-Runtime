#!/usr/bin/env python3
"""run_all.py — batch autoplay runner (one command over the roster).

Optimization law (S100): consistent output layout (run/autoplay/<title>/),
one record per title, summary table at the end. Drivers are invoked with
their documented default schedules; a title whose driver is a specialized
in-process module keeps its own entry point here.

Usage:
  python3 scripts/autoplay/run_all.py [title ...]
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))

# title -> (driver script, argv template) ; drivers using common.py take no
# extra args; specialized drivers keep their internal defaults.
ROSTER = {
    "snake-deluxe": [sys.executable, os.path.join(HERE, "s80_sd_autoplay.py")],
    "2048": [sys.executable, os.path.join(HERE, "s80_2048_autoplay.py")],
    "mini-tetris": [sys.executable, os.path.join(HERE, "s80_tet_autoplay.py")],
    "tictactoe": [sys.executable, os.path.join(HERE, "s83_ttt_autoplay.py")],
    "minicraft": [sys.executable, os.path.join(HERE, "s98_minicraft_autoplay.py")],
    "snake-neon": [sys.executable, os.path.join(HERE, "s98_snakeneon_autoplay.py")],
}


def main():
    wanted = sys.argv[1:] or list(ROSTER)
    results = []
    for title in wanted:
        cmd = ROSTER.get(title)
        if not cmd:
            print(f"SKIP unknown title {title}")
            continue
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
            rc = r.returncode
        except subprocess.TimeoutExpired:
            rc = -9
        rec_path = os.path.join(REPO, "run", "autoplay", title,
                                "autoplay_record.json")
        rec = None
        if os.path.exists(rec_path):
            with open(rec_path) as f:
                rec = json.load(f)
        results.append((title, rc, rec))

    print("\n=== AUTOPLAY SUMMARY ===")
    print(f"{'title':<14} {'rc':>4} {'state-px':>10} {'shot SHA16':<18}")
    for title, rc, rec in results:
        px = rec.get("state_change_px", "n/a") if rec else "n/a"
        sha = (rec.get("screenshot_sha16", "n/a") if rec else "n/a") or "n/a"
        print(f"{title:<14} {rc:>4} {str(px):>10} {sha:<18}")
    ok = sum(1 for _, rc, _ in results if rc == 0)
    print(f"\n{ok}/{len(results)} drivers completed (rc=0)")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
