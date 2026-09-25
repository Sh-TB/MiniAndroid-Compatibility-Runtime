#!/usr/bin/env python3
"""s80_2048_autoplay.py — 2048 autonomous play driver (S80).

2048 has NO timer: state advances only on taps, so every committed tap
deterministically transforms the board. The driver:
  1. runs the REAL APK from launch with the committed tap schedule (C7:
     pixel-SHA prefix verification up to the first frame a new tap can
     influence — a tap@k is dispatched after frame k renders, so its
     effect appears in frame k+1),
  2. reads the board from rendered pixels (classic palette is unique per
     tile value — C3 vision law),
  3. simulates the 4 moves on the observed board, picks the best by the
     standard weights (empties, merges, monotonicity, max tile corner),
     commits ONE tap,
  4. re-runs. The app's own logic stays authoritative (C4).
"""
import glob
import hashlib
import os
import shutil
import subprocess
import sys

from PIL import Image

ROOT = "/home/z/my-project"
ENG = f"{ROOT}/miniandroid/build/miniandroid"
APK = f"{ROOT}/upload/s80_games/build_2048/g2048_v1.0_vc1.apk"

BTN = {"LEFT": (170, 1826), "UP": (416, 1826), "DOWN": (662, 1826),
       "RIGHT": (909, 1826)}

N = 4
# measured grid (frame probe): board base at (pad-10, boardTop-10) with
# cell/gap computed by the app; derive from constants used in onDraw:
PAD = 30
GAP = 14
# cell = (1080-60-42)/4 = 244 (integer division), boardTop centered
CELL = (1080 - 2 * PAD - 3 * GAP) // N

# classic palette (value -> RGB), mirrors the app's TILE_BG
PALETTE = {
    2: (238, 228, 218), 4: (237, 224, 200), 8: (242, 177, 121),
    16: (245, 149, 99), 32: (246, 124, 95), 64: (246, 94, 59),
    128: (237, 207, 114), 256: (237, 204, 97), 512: (237, 200, 80),
    1024: (237, 197, 63), 2048: (237, 194, 46),
}


def board_top(h=1920, w=1080):
    cell = (w - 2 * PAD - 3 * GAP) // N
    boardH = 4 * cell + 3 * GAP
    return max(140, (h - boardH - 40) // 2)


def read_board(png_path):
    """Sample MULTIPLE points per cell (the digit glyph covers the
    center) and take the first palette hit; strict tolerance."""
    img = Image.open(png_path).convert("RGB")
    px = img.load()
    bt = board_top()
    board = {}
    offs = [(0, -int(CELL * 0.32)), (0, int(CELL * 0.32)),
            (-int(CELL * 0.30), 0), (int(CELL * 0.30), 0),
            (-int(CELL * 0.32), -int(CELL * 0.32)),
            (int(CELL * 0.32), int(CELL * 0.32))]
    for r in range(N):
        for c in range(N):
            cx = PAD + c * (CELL + GAP) + CELL // 2
            cy = bt + r * (CELL + GAP) + CELL // 2
            hit = 0
            for dx, dy in offs:
                p = px[cx + dx, cy + dy]
                for v, col in PALETTE.items():
                    if all(abs(p[k] - col[k]) <= 10 for k in range(3)):
                        hit = v
                        break
                if hit:
                    break
            if hit:
                board[(c, r)] = hit
    return board


def frame_shas(out_dir):
    files = sorted(glob.glob(f"{out_dir}/frames/frame_*.png"))
    return [hashlib.sha256(Image.open(f).convert("RGB").tobytes()).hexdigest()
            for f in files]


def run_engine(taps, n_frames, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    cmd = [ENG, "run", "--execution-mode", "real-dalvik",
           "--frames", str(n_frames), "--frame-delay", str(250),
           "-o", out_dir]
    for (x, y, k) in taps:
        cmd += ["--tap", f"{x},{y}@{k}"]
    cmd += [APK]
    with open(f"{out_dir}.log", "w") as log:
        rc = subprocess.call(cmd, stdout=log, stderr=log, timeout=2400)
    return rc


def to_grid(cells):
    g = [[0] * N for _ in range(N)]
    for (c, r), v in cells.items():
        g[r][c] = v
    return g


def slide_merge(line):
    """Simulate one line: returns (new_line, gained)."""
    vals = [v for v in line if v != 0]
    out = []
    gained = 0
    j = 0
    while j < len(vals):
        if j + 1 < len(vals) and vals[j] == vals[j + 1]:
            out.append(vals[j] * 2)
            gained += vals[j] * 2
            j += 2
        else:
            out.append(vals[j])
            j += 1
    out += [0] * (N - len(out))
    return out, gained


def sim_move(g, dir_):
    """0=left 1=up 2=right 3=down; returns (new_grid, gained, changed)."""
    n = N
    ng = [[0] * n for _ in range(n)]
    gained_total = 0
    changed = False
    for i in range(n):
        line = []
        for j in range(n):
            if dir_ == 0: line.append(g[i][j])
            elif dir_ == 2: line.append(g[i][n - 1 - j])
            elif dir_ == 1: line.append(g[j][i])
            else: line.append(g[n - 1 - j][i])
        merged, gained = slide_merge(line)
        gained_total += gained
        for j in range(n):
            if dir_ == 0: ng[i][j] = merged[j]
            elif dir_ == 2: ng[i][n - 1 - j] = merged[j]
            elif dir_ == 1: ng[j][i] = merged[j]
            else: ng[n - 1 - j][i] = merged[j]
    changed = ng != g
    return ng, gained_total, changed


def empties(g):
    return sum(1 for r in range(N) for c in range(N) if g[r][c] == 0)


def monotonicity(g):
    best = 0
    for orient in (0, 1):
        for rev in (False, True):
            s = 0
            for i in range(N):
                row = [g[i][j] for j in range(N)] if orient == 0 else \
                      [g[j][i] for j in range(N)]
                if rev: row = row[::-1]
                for j in range(N - 1):
                    a = row[j] if row[j] else 1
                    b = row[j + 1] if row[j + 1] else 1
                    if a >= b: s += 1
            best = max(best, s)
    return best


def evaluate(g):
    e = empties(g)
    mono = monotonicity(g)
    mx = max(max(row) for row in g)
    corner = 1 if (g[N - 1][0] == mx or g[N - 1][N - 1] == mx or
                   g[0][0] == mx or g[0][N - 1] == mx) else 0
    return e * 270 + mono * 32 + corner * 200 + mx


def choose(g):
    best, bestd = None, None
    for d in range(4):
        ng, gained, changed = sim_move(g, d)
        if not changed:
            continue
        sc = evaluate(ng) + gained * 12
        if bestd is None or sc > bestd:
            bestd, best = sc, d
    return best


def main():
    moves_target = int(os.environ.get("G2048_MOVES", "60"))
    OUT = f"{ROOT}/run/s80_2048_autoplay"
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(OUT, exist_ok=True)

    taps = []
    base_shas = None
    prev_f1 = None
    score_seen = 0
    moves = 0
    cycle = 0

    while moves < moves_target:
        last_tap = max((t[2] for t in taps), default=-1)
        n_frames = last_tap + 8
        run_dir = f"{OUT}/cycle_{cycle:02d}"
        rc = run_engine(taps, n_frames, run_dir)
        if rc != 0:
            print(f"cycle {cycle}: engine rc={rc}")
            sys.exit(1)
        shas = frame_shas(run_dir)

        if base_shas:
            k = min(len(base_shas), prev_f1 if prev_f1 is not None
                    else len(shas))
            mism = [i for i in range(k) if base_shas[i] != shas[i]]
            assert not mism, f"prefix SHA mismatch at {mism[:3]}"
        base_shas = shas

        frames = sorted(glob.glob(f"{run_dir}/frames/frame_*.png"))
        obs_frame = min(last_tap + 2 if last_tap >= 0 else 3, len(frames) - 1)
        cells = read_board(frames[obs_frame])
        g = to_grid(cells)
        if sum(sum(row) for row in g) == 0:
            print(f"cycle {cycle}: board unreadable at frame {obs_frame}")
            sys.exit(3)

        d = choose(g)
        if d is None:
            print(f"cycle {cycle}: NO MOVES LEFT — game over at move {moves}")
            break
        name = ["LEFT", "UP", "RIGHT", "DOWN"][d]
        tap_frame = last_tap + 4
        new_taps = [(BTN[name][0], BTN[name][1], tap_frame)]
        taps += new_taps
        prev_f1 = tap_frame
        moves += 1
        cycle += 1
        ng, gained, _ = sim_move(g, d)
        score_seen += gained
        print(f"cycle {cycle}: move {moves} {name} gained={gained} "
              f"score~{score_seen} board_max={max(max(r) for r in g)}")

    # final continuous evidence run
    final_dir = f"{OUT}/final_run"
    last_tap = max((t[2] for t in taps), default=-1)
    rc = run_engine(taps, last_tap + 12, final_dir)
    shas = frame_shas(final_dir)
    k = min(len(base_shas), prev_f1 if prev_f1 is not None else len(shas),
            len(shas))
    mism = [i for i in range(k) if base_shas[i] != shas[i]]
    assert not mism, f"final prefix mismatch at {mism[:3]}"
    print(f"final continuous run: {len(shas)} frames, prefix verified {k}, "
          f"moves={moves} rc={rc}")


if __name__ == "__main__":
    main()
