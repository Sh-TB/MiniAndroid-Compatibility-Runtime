#!/usr/bin/env python3
"""CONT-83 WS-D — 12-game graphics matrix at the wave binary.

Each game: install → run with MINIANDROID_GFX_TRACE=1 (deferred-drain
budget 24 frames for the veldsoft deferred-launch family) → collect:
  - face sha16 + F-NEW-233 frame-truth verdict (from the run log)
  - gfx summary (gl_frames, events, first_missing_transition)
  - gl.call rows per API (GL10/GLES20/EGL) + native.load/dep rows
Machine-readable output: evidence/cont83/gfx_matrix.json.
"""
import json, os, subprocess, hashlib, sys

ROOT = "/home/z/my-project"
BIN = f"{ROOT}/miniandroid/build/miniandroid"
OUTDIR = f"{ROOT}/evidence/cont83"
os.makedirs(OUTDIR, exist_ok=True)

GAMES = [
    # (name, apk path, frames, budget_s)
    ("dooz",        "upload/canonical_apks/io.github.yamin8000.dooz_23.apk", 8, 40),
    ("g2048",       "upload/s83_games/build_g2048/g2048_v1.0_vc1.apk", 8, 40),
    ("tetris",      "upload/s83_games/build_tetris/tetris_v1.0_vc1.apk", 8, 40),
    ("tttdeluxe",   "upload/s83_games/build_ttt/tictactoe_deluxe_v1.0_vc1.apk", 8, 40),
    ("snakedeluxe", "upload/s83_games/build_sd/snake_deluxe_v1.0_vc1.apk", 8, 40),
    ("flappycow",   "upload/flappycow_rebuilt.apk", 8, 40),
    ("bouncy",      "upload/canonical_apks/com.dozingcatsoftware.bouncy_43.apk", 8, 40),
    ("tower3d",     "upload/canonical_apks/stack.tower3d_1.apk", 8, 40),
    ("fishrings",   "upload/canonical_apks/fishrings_v1.23_vc6.apk", 24, 60),
    ("tripeaks",    "upload/canonical_apks/tripeaks_v1.2.1_vc4.apk", 24, 60),
    ("klondike",    "upload/klondike_veldsoft_3.apk", 24, 60),
    ("chess",       "upload/chess_jwtc_298.apk", 8, 40),
    ("gmdice",      "upload/canonical_apks/de.duenndns.gmdice_8.apk", 8, 40),
    ("memory",      "upload/canonical_apks/org.secuso.privacyfriendlymemory_100.apk", 8, 40),
]

def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, **kw)

def pkg_of(apk):
    r = sh(["tools/toolchain/aapt2", "dump", "badging", apk])
    for line in r.stdout.splitlines():
        if line.startswith("package:"):
            return line.split("name='")[1].split("'")[0]
    return None

def main():
    store = f"{ROOT}/run/cont83/matrixstore"
    os.makedirs(store, exist_ok=True)
    rows = []
    for name, apk, frames, budget in GAMES:
        pkg = pkg_of(apk)
        if not pkg:
            rows.append({"game": name, "error": "no package"}); continue
        r = sh([BIN, "install", apk, "--data-root", store])
        if r.returncode != 0 and "already installed" not in (r.stderr or ""):
            rows.append({"game": name, "error": f"install rc={r.returncode}"})
            continue
        out = f"{ROOT}/run/cont83/matrix/{name}"
        os.makedirs(os.path.dirname(out), exist_ok=True)
        env = dict(os.environ)
        env["MINIANDROID_GFX_TRACE"] = "1"
        env["MINIANDROID_GFX_TRACE_FILE"] = f"{out}/gfx_trace.jsonl"
        cmd = [BIN, "run", "--package", pkg, "--data-root", store,
               "--width", "1080", "--height", "1920", "--frames",
               str(frames), "--max-seconds", str(budget), "-o", out]
        rr = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT,
                            env=env)
        log = rr.stdout + rr.stderr
        face = None
        try:
            face = hashlib.sha256(
                open(f"{out}/screenshot.png", "rb").read()).hexdigest()[:16]
        except FileNotFoundError:
            pass
        verdict, fms = None, None
        for line in log.splitlines():
            if "F-NEW-233 frame truth" in line:
                if "verdict=" in line:
                    verdict = line.split("verdict=")[1].split(",")[0]
                if "first_missing_stage=" in line:
                    fms = line.split("first_missing_stage=")[1].split()[0]
        gsum = None
        try:
            gsum = json.load(open(f"{out}/gfx_trace.jsonl.summary.json"))
        except FileNotFoundError:
            pass
        gl_api = {"GL10": 0, "GLES20": 0, "EGL": 0}
        nload = []
        try:
            for line in open(f"{out}/gfx_trace.jsonl"):
                if not line.strip(): continue
                j = json.loads(line)
                if j.get("type") == "gl.call":
                    gl_api[j.get("api", "?")] = gl_api.get(j.get("api", "?"), 0) + 1
                if j.get("type") == "native.load":
                    nload.append({"lib": j.get("lib"), "ok": j.get("ok")})
        except FileNotFoundError:
            pass
        rows.append({"game": name, "pkg": pkg, "apk_sha16": hashlib.sha256(
            open(apk, "rb").read()).hexdigest()[:16],
            "frames": frames, "rc": rr.returncode, "face16": face,
            "verdict": verdict, "first_missing_stage": fms,
            "gfx_summary": gsum, "gl_calls": gl_api,
            "native_loads": nload})
        print(f"{name}: face={face} verdict={verdict} fms={fms} "
              f"gl={gl_api} rc={rr.returncode}")
    with open(f"{OUTDIR}/gfx_matrix.json", "w") as f:
        json.dump({"instrument": "CONT-83 WS-D matrix",
                   "binary": hashlib.sha256(open(BIN, "rb").read()).hexdigest()[:16],
                   "rows": rows}, f, indent=1)
    real = sum(1 for r in rows if r.get("verdict") in
               ("REAL_APP_CONTENT", "INTERACTIVE_CONTENT_VERIFIED"))
    print(f"\napp-content: {real}/{len(rows)}")

if __name__ == "__main__":
    main()
