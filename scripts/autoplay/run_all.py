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

    # §7 batch evidence law (#587 forensic addendum): repeated runs write ONE
    # batch-level runs.jsonl with per-run metrics + SHAs — never one full
    # PNG per run. Each row: run id, apk sha, engine sha, exit, frames,
    # screenshot sha, state-change px, preview path, report-sanity verdict.
    engine_sha = None
    ma_bin = os.path.join(REPO, "miniandroid", "build", "miniandroid")
    if os.path.exists(ma_bin):
        import hashlib
        engine_sha = hashlib.sha256(open(ma_bin, "rb").read()).hexdigest()[:16]
    batch_path = os.path.join(REPO, "run", "autoplay", "runs.jsonl")
    with open(batch_path, "w") as f:
        for title, rc, rec in results:
            row = {
                "run_id": title,
                "apk": rec.get("apk") if rec else None,
                "apk_sha16": rec.get("apk_sha16") if rec else None,
                "engine_sha16": engine_sha,
                "exit": rc,
                "frames": rec.get("frames") if rec else None,
                "screenshot_sha16": rec.get("screenshot_sha16") if rec else None,
                "state_change_px": rec.get("state_change_px") if rec else None,
                "preview": rec.get("preview") if rec else None,
                "full_screenshot_retained":
                    rec.get("full_screenshot_retained") if rec else None,
                "report_sanity_violations":
                    rec.get("report_sanity_violations") if rec else None,
            }
            f.write(json.dumps(row) + "\n")
    print(f"batch evidence: {batch_path} ({len(results)} rows)")
    bad = [t for t, _, rec in results if rec and rec.get("report_sanity_violations")]
    if bad:
        print(f"REPORT-SANITY violations in: {bad}")
        return 1
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
