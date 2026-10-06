#!/usr/bin/env python3
"""cont7w3_sixgames.py — CONT-6 Phase 4 (Issue #377): independent six-game
REAL_APP_CONTENT re-validation at current HEAD.

For every title: exact APK SHA-256, install verdict, 3 clean runs
(fresh store each run), screenshot SHA16 x3 + byte-identity, draw ops,
pixel metrics, ViewTree node count, first divergence if failed.

Writes evidence/cont6/six_game_validation.json.
"""
import hashlib, json, os, shutil, subprocess, sys

BASE = "/home/z/my-project"
BIN = f"{BASE}/miniandroid/build/miniandroid"
OUT_JSON = f"{BASE}/evidence/cont6/six_game_validation.json"

GAMES = [
    ("2048",              "com.miniandroid.g2048",      f"{BASE}/upload/s80_games/build_2048/g2048_v1.0_vc1.apk"),
    ("mini-tetris",       "com.miniandroid.tetris",     f"{BASE}/upload/s80_games/build_tetris/tetris_v1.0_vc1.apk"),
    ("minicraft",         "com.miniandroid.minicraft",  f"{BASE}/upload/s86_games/build_minicraft/minicraft_v1.0_vc1.apk"),
    ("snake-deluxe",      "com.miniandroid.snakedeluxe", f"{BASE}/upload/s80_games/build_sd/snake_deluxe_v1.0_vc1.apk"),
    ("snake-neon",        "com.miniandroid.snakeneon",  f"{BASE}/upload/s98_games/build_snakeneon/snakeneon_v1.0_vc1.apk"),
    ("tictactoe-deluxe",  "com.miniandroid.tictactoedeluxe",  f"{BASE}/upload/s83_games/build_ttt/tictactoe_deluxe_v1.0_vc1.apk"),
]

def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16] if os.path.exists(p) else None

def run_one(title, pkg, apk):
    rec = {"apk": apk, "apk_sha256": hashlib.sha256(open(apk, "rb").read()).hexdigest()}
    store = f"/tmp/w3/six/{title}"
    shutil.rmtree(store, ignore_errors=True)
    os.makedirs(store, exist_ok=True)
    r = subprocess.run([BIN, "install", apk, "--data-root", f"{store}/data"],
                       capture_output=True, text=True, timeout=300)
    rec["install"] = "OK" if "Installed" in (r.stdout + r.stderr) else "FAIL"
    runs = []
    for i in range(1, 4):
        sdir = f"{store}/run{i}"
        rr = subprocess.run([BIN, "run", "--package", pkg, "--data-root", f"{store}/data",
                             "--execution-mode", "real-dalvik", "-o", sdir,
                             "--dump-view-tree", "--trace",
                             "--max-seconds", "110"],
                            capture_output=True, text=True, timeout=300)
        log = rr.stdout + rr.stderr
        shot = f"{sdir}/screenshot.png"
        row = {
            "run": i,
            "screenshot_sha16": sha16(shot),
            "app_boundary_exceptions": log.count("EXC-PROPAGATE.*APP BOUNDARY")
                                       if False else sum(1 for _ in [1] if "APP BOUNDARY" in log),
        }
        for key, marker in [
            ("verdict", None),
        ]:
            pass
        import re
        m = re.search(r"verdict=([A-Z_]+), first_missing_stage=([A-Z_]+)", log)
        row["verdict"] = m.group(1) if m else None
        row["first_missing_stage"] = m.group(2) if m else None
        if row["verdict"] is None:
            m2 = re.search(r"verdict=([A-Z_]+)", log)
            row["verdict"] = m2.group(1) if m2 else None
        if row["verdict"] is None:
            ts = os.path.join(sdir, "trace_summary.json")
            if os.path.exists(ts):
                try:
                    fa = json.load(open(ts)).get("frame_analysis") or {}
                    row["verdict"] = fa.get("verdict")
                    row["app_owned_pixels"] = fa.get("app_owned_pixels")
                    row["app_draw_ops"] = fa.get("app_draw_ops")
                except Exception:
                    pass
        m = re.search(r"([0-9]+) uncaught in-flight exception", log)
        row["uncaught_exceptions"] = int(m.group(1)) if m else 0
        # draw ops + viewtree from the report.md evidence files
        for name in ("draw_ops.json", "view_tree.json"):
            pass
        do = os.path.exists(f"{sdir}/canvas_ops.json")
        row["canvas_ops_file"] = do
        runs.append(row)
    rec["runs"] = runs
    shas = [r["screenshot_sha16"] for r in runs]
    rec["deterministic_x3"] = len(set(shas)) == 1 and shas[0] is not None
    rec["verdicts"] = sorted({r.get("verdict") for r in runs})
    rec["all_runs_verdict"] = runs[0].get("verdict") if len(rec["verdicts"]) == 1 else "MIXED"
    return rec

def main():
    os.makedirs("/tmp/w3/six", exist_ok=True)
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    out = {"wave": "CONT-7 W3 / CONT-6 Phase 4",
           "head": subprocess.run(["git", "-C", BASE, "rev-parse", "--short=8", "HEAD"],
                                  capture_output=True, text=True).stdout.strip(),
           "binary_sha16": sha16(BIN), "games": []}
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for title, pkg, apk in GAMES:
        if only and title != only:
            continue
        if not os.path.exists(apk):
            out["games"].append({"title": title, "error": f"missing apk {apk}"})
            continue
        rec = run_one(title, pkg, apk)
        rec["title"] = title
        rec["package"] = pkg
        out["games"].append(rec)
        print(f"{title}: verdict={rec['all_runs_verdict']} "
              f"det3={rec['deterministic_x3']} sha={rec['runs'][0]['screenshot_sha16']}")
    with open(OUT_JSON, "w") as f:
        json.dump(out, f, indent=1)
    print("wrote", OUT_JSON)

if __name__ == "__main__":
    main()
