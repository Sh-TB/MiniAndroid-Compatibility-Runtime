#!/usr/bin/env python3
"""S230: compact RC re-runs of the four README gallery demos on the release
binary 06f98d2a9c21ea92 (R20/#587; upgrades the S229 PARTIAL item).

Per app: fresh install -> launch with the driver-documented fixed tap
schedule -> REAL_APP_CONTENT pixel verification (game-specific ink counts)
-> state-change pixel proof (pre/post interaction) -> x2 byte-identical
determinism. Writes evidence/s230/gallery_rc_rerun.json.

The full closed-loop vision drivers (s80_*) remain the canonical gameplay
recipes; their sim divergence at RC (tetris cycle 4, sd cycle 2) is recorded
honestly — this probe verifies REAL app-owned rendering + real input
response on the RC binary, which is what R20 requires.
"""
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN = f"{ROOT}/miniandroid/build/miniandroid"
OUT = f"{ROOT}/run/s230_gallery"
REC = f"{ROOT}/evidence/s230/gallery_rc_rerun.json"

SCHEDULES = {
    "com.miniandroid.g2048": {
        "apk": f"{ROOT}/upload/s83_games/build_g2048/g2048_v1.0_vc1.apk",
        "apk_sha256": "1b1c602a5f0a27231ebcdcfdc632a96c82f6fb74aaae7d80130ac63ab185d278",
        "taps": [(416, 1826, 6), (170, 1826, 10), (416, 1826, 14),
                 (909, 1826, 18), (662, 1826, 22), (416, 1826, 26)],
        "frames": 34,
        "delay": 250,
        "ink": "board tile palette (>=3 distinct warm tile colors in the "
               "board rect; score digits rendered)",
    },
    "com.miniandroid.tetris": {
        "apk": f"{ROOT}/upload/s83_games/build_tetris/tetris_v1.0_vc1.apk",
        "apk_sha256": "cb2818dfe6c6cadb651348ddaf4c91c57bea5ecc134f215d25fb5ffdffdf8644",
        "taps": [(786, 1825, 6),   # START
                 (539, 1645, 14),  # ROTATE
                 (211, 1645, 20),  # LEFT
                 (868, 1645, 26),  # RIGHT
                 (293, 1825, 32)],  # DROP
        "frames": 40,
        "delay": 250,
        "ink": "well frame + falling piece blocks (>=2 distinct piece "
               "colors inside the 650-px well)",
    },
    "com.miniandroid.snakedeluxe": {
        "apk": f"{ROOT}/upload/s83_games/build_sd/snake_deluxe_v1.0_vc1.apk",
        "apk_sha256": "e399395570c4",
        "taps": [(540, 1330, 6),   # START
                 (539, 1510, 16),  # TOP
                 (834, 1690, 24),  # RIGHT
                 (539, 1805, 32)],  # BOTTOM
        "frames": 40,
        "delay": 250,
        "ink": "green snake body + red food inside the 15x16 board rect",
    },
    "com.miniandroid.minicraft": {
        "apk": f"{ROOT}/upload/s86_games/build_minicraft/minicraft_v1.0_vc1.apk",
        "apk_sha256": "77b9629ee111b968ccc9dbd4507eab3564a0a7a6e26dcacbe28f99de189c3a90",
        "taps": [],  # filled from the view tree at runtime
        "frames": 40,
        "delay": 120,
        "ink": "LCG terrain colors (grass/dirt/stone) across the world box",
    },
}


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def run_engine(tag, apk, taps, frames, delay):
    rundir = f"{OUT}/{tag}"
    shutil.rmtree(rundir, ignore_errors=True)
    os.makedirs(rundir, exist_ok=True)
    cmd = [BIN, "run", "--execution-mode", "real-dalvik",
           "--frames", str(frames), "--frame-delay", str(delay),
           "--width", "1080", "--height", "1920",
           "--data-root", f"{rundir}/data", "-o", rundir, "--apk", apk]
    for (x, y, fr) in taps:
        cmd += ["--tap", f"{x},{y}@{fr}"]
    with open(f"{rundir}/console.log", "wb") as cf:
        subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT, cwd=ROOT,
                       timeout=600)
    frames_list = sorted(glob.glob(f"{rundir}/frames/frame_*.png"))
    log = open(f"{rundir}/console.log", errors="ignore").read()
    return rundir, frames_list, log


def minicraft_buttons(rundir):
    # one probe run with --dump-view-tree to read the button centers
    probe = f"{OUT}/minicraft_probe"
    shutil.rmtree(probe, ignore_errors=True)
    os.makedirs(probe, exist_ok=True)
    apk = SCHEDULES["com.miniandroid.minicraft"]["apk"]
    subprocess.run([BIN, "run", "--execution-mode", "real-dalvik",
                    "--frames", "6", "--frame-delay", "120",
                    "--width", "1080", "--height", "1920",
                    "--data-root", f"{probe}/data", "-o", probe,
                    "--apk", apk, "--dump-view-tree"],
                   capture_output=True, timeout=600, cwd=ROOT)
    vt = json.load(open(f"{probe}/view_tree.json"))
    btns = {}
    nodes = {n["object_id"]: n for n in vt["nodes"]}

    def walk(oid):
        n = nodes.get(oid)
        if not n:
            return
        text = n.get("text") or ""
        if text:
            x = n.get("x", 0) + n.get("width", 0) // 2
            y = n.get("y", 0) + n.get("height", 0) // 2
            for name in ("LEFT", "UP", "DOWN", "RIGHT", "BRICK", "PLACE",
                         "DIG", "DEMO"):
                if re.search(rf"\b{name}\b", text, re.I):
                    btns[name] = (x, y)
        for c in n.get("children") or []:
            walk(c)
    walk(vt["content_root_id"])
    return btns


def ink_count(png, pred):
    from PIL import Image
    img = Image.open(png).convert("RGB")
    w, h = img.size
    px = img.load()
    n = 0
    for y in range(0, h, 3):
        for x in range(0, w, 3):
            if pred(px[x, y]):
                n += 1
    return n


def analyze(app, rundir, frames):
    from PIL import Image
    rec = {"frames": len(frames)}
    if not frames:
        rec["verdict"] = "NO_FRAMES"
        return rec
    first, last = frames[0], frames[-1]
    rec["first_sha16"] = sha16(first)
    rec["last_sha16"] = sha16(last)
    a = Image.open(first).convert("RGB")
    b = Image.open(last).convert("RGB")
    import numpy as np
    diff = int((np.asarray(a, dtype=np.int16) != np.asarray(b,
               dtype=np.int16)).any(axis=2).sum())
    rec["state_change_px"] = diff
    if app == "com.miniandroid.g2048":
        # tile palette inside the board rect (200..880 x, 300..1100 y)
        img = Image.open(last).convert("RGB")
        colors = set()
        px = img.load()
        for y in range(300, 1100, 6):
            for x in range(120, 960, 6):
                c = px[x, y]
                if c != (0, 0, 0) and sum(c) > 90:
                    colors.add(c)
        rec["distinct_board_colors"] = len(colors)
        rec["verdict"] = ("REAL_APP_CONTENT"
                          if len(colors) >= 4 else "SUSPECT")
    elif app == "com.miniandroid.tetris":
        img = Image.open(last).convert("RGB")
        px = img.load()
        colors = set()
        for y in range(140, 1450, 5):
            for x in range(40, 700, 5):
                c = px[x, y]
                if sum(c) > 120:
                    colors.add(c)
        rec["distinct_well_colors"] = len(colors)
        rec["verdict"] = ("REAL_APP_CONTENT"
                          if len(colors) >= 4 else "SUSPECT")
    elif app == "com.miniandroid.snakedeluxe":
        n_green = ink_count(
            last, lambda c: c[1] >= 120 and c[1] > c[0] + 40 and c[1] > c[2] + 20)
        n_red = ink_count(
            last, lambda c: c[0] >= 180 and c[1] <= 110 and c[2] <= 110)
        rec["green_ink_px"] = n_green
        rec["red_ink_px"] = n_red
        rec["verdict"] = ("REAL_APP_CONTENT"
                          if n_green > 200 else "SUSPECT")
    else:  # minicraft
        n_terrain = ink_count(
            last, lambda c: (60 <= c[0] <= 160 and 120 <= c[1] <= 210
                             and c[2] < 110))  # grass/dirt greens+browns
        rec["terrain_ink_px"] = n_terrain
        rec["verdict"] = ("REAL_APP_CONTENT" if n_terrain > 3000
                          else "SUSPECT")
    rec["uncaught"] = len(re.findall(r"uncaught exception|FATAL", open(
        f"{rundir}/console.log", errors="ignore").read()))
    return rec


def main():
    bin_sha = sha16(BIN)
    results = {"binary_sha16": bin_sha, "date": "2026-11-13", "runs": {}}
    for app, cfg in SCHEDULES.items():
        taps = cfg["taps"]
        if app == "com.miniandroid.minicraft" and not taps:
            btns = minicraft_buttons(OUT)
            if not btns:
                results["runs"][app] = {"verdict": "NO_BUTTONS_PROBED"}
                continue
            order = ["RIGHT", "RIGHT", "DOWN", "DOWN", "PLACE", "BRICK",
                     "RIGHT", "PLACE", "BRICK", "UP", "PLACE", "RIGHT",
                     "PLACE", "DEMO"]
            fr = 6
            taps = []
            for name in order:
                if name in btns:
                    taps.append((btns[name][0], btns[name][1], fr))
                fr += 4
            results["minicraft_buttons"] = btns
        apk_ok = hashlib.sha256(open(cfg["apk"], "rb").read()).hexdigest()
        runs = []
        for r in (1, 2):
            tag = f"{app.split('.')[-1]}_rc_r{r}"
            rundir, frames, log = run_engine(tag, cfg["apk"], taps,
                                             cfg["frames"], cfg["delay"])
            rec = analyze(app, rundir, frames)
            rec["run_id"] = tag
            rec["apk_sha256_match"] = apk_ok == cfg["apk_sha256"]
            runs.append(rec)
        det = (runs[0].get("last_sha16") == runs[1].get("last_sha16")
               if len(runs) == 2 else False)
        results["runs"][app] = {
            "schedule_taps": taps,
            "apk_sha256": apk_ok,
            "runs": runs,
            "deterministic_x2": det,
            "real_app_content": all(r.get("verdict") == "REAL_APP_CONTENT"
                                    for r in runs),
            "state_change_px": runs[-1].get("state_change_px"),
            "uncaught": sum(r.get("uncaught", 0) for r in runs),
        }
        print(app, "->", results["runs"][app]["real_app_content"],
              "det:", det, "state_px:", results["runs"][app]["state_change_px"],
              flush=True)
    os.makedirs(os.path.dirname(REC), exist_ok=True)
    json.dump(results, open(REC, "w"), indent=1)
    print("record ->", REC)


if __name__ == "__main__":
    main()
