#!/usr/bin/env python3
"""s80_sd_autoplay.py — Snake Deluxe autonomous gameplay driver (S80).

Vision-based micro-leg planner in the proven S73 law shape:
  C1: only actuator = scheduled taps through the canonical TouchDispatcher.
  C3: vision from RENDERED FRAMES ONLY (board cell centers); no game memory.
  C4: the app's own logic stays authoritative (reverse guard, walls, growth).
  C7: every decision cycle re-runs the REAL APK from launch; the committed
      prefix is re-verified by per-frame pixel SHAs up to the first frame a
      newly added tap can influence (tap@k influences frame k+1 onward).

Leg structure: observe at frame (last_committed_tap + 3) — mid-runway so
the snake is guaranteed alive and has moves left; commit turn taps for the
first min(path_len, runway) cells of the L-path; repeat until capture.
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
APK = f"{ROOT}/upload/s80_games/build_sd/snake_deluxe_v1.0_vc1.apk"

GRID_X, GRID_Y = 15, 16
CELL = 68
BXL, BYT = 30, 132
START_TAP = (540, 1500, 4)

BTN = {"TOP": (539, 1632), "LEFT": (309, 1743), "RIGHT": (834, 1743),
       "BOTTOM": (539, 1854)}
DIRS = {"U": (0, -1), "D": (0, 1), "L": (-1, 0), "R": (1, 0)}
DIRNAME_BTN = {"U": "TOP", "D": "BOTTOM", "L": "LEFT", "R": "RIGHT"}
OPP = {"U": "D", "D": "U", "L": "R", "R": "L"}


# ---------------------------------------------------------------- vision
def cell_center(c, r):
    return (BXL + c * CELL + CELL // 2, BYT + r * CELL + CELL // 2)


def is_green(p):
    r, g, b = p
    return g >= 120 and g > r + 40 and g > b + 20


def is_red(p):
    r, g, b = p
    return r >= 180 and g <= 110 and b <= 110


def read_board(png_path):
    """(snake_cells scan-order, food_cell) from one rendered frame."""
    img = Image.open(png_path).convert("RGB")
    px = img.load()
    snake, food = [], []
    for r in range(GRID_Y):
        for c in range(GRID_X):
            x, y = cell_center(c, r)
            p = px[x, y]
            if is_green(p):
                snake.append((c, r))
            elif is_red(p):
                food.append((c, r))
    return snake, (food[0] if food else None)


def head_of(png_path, snake):
    """Head = the green cell containing pure-white eye pixels."""
    img = Image.open(png_path).convert("RGB")
    px = img.load()
    for (c, r) in snake:
        cx, cy = cell_center(c, r)
        whites = 0
        for ddx in range(-22, 23, 4):
            for ddy in range(-22, 23, 4):
                if px[cx + ddx, cy + ddy] == (255, 255, 255):
                    whites += 1
        if whites >= 4:
            return (c, r)
    return snake[-1] if snake else None


def dialog_visible(png_path):
    """Game-over/pause dialog = white panel across the board mid-band."""
    img = Image.open(png_path).convert("RGB")
    px = img.load()
    hits = 0
    for x in range(200, 900, 50):
        for y in range(860, 1060, 40):
            p = px[x, y]
            if p[0] > 235 and p[1] > 235 and p[2] > 235:
                hits += 1
    return hits >= 20


# ---------------------------------------------------------------- engine
def run_engine(taps, n_frames, out_dir, frame_delay=250):
    os.makedirs(out_dir, exist_ok=True)
    cmd = [ENG, "run", "--execution-mode", "real-dalvik",
           "--frames", str(n_frames), "--frame-delay", str(frame_delay),
           "-o", out_dir]
    for (x, y, k) in taps:
        cmd += ["--tap", f"{x},{y}@{k}"]
    cmd += [APK]
    with open(f"{out_dir}.log", "w") as log:
        rc = subprocess.call(cmd, stdout=log, stderr=log, timeout=2400)
    return rc


def frame_shas(out_dir):
    files = sorted(glob.glob(f"{out_dir}/frames/frame_*.png"))
    return [hashlib.sha256(Image.open(f).convert("RGB").tobytes()).hexdigest()
            for f in files]


# ---------------------------------------------------------------- planning
def l_path(head, d, food, body):
    """Axis-ordered 1-cell path head→food; None when unsafe. Never returns
    a path whose FIRST move reverses d (the app's reverse guard would kill
    the snake — AndroidGameSnake-classic law, kept by Snake Deluxe)."""
    hx, hy = head
    fx, fy = food
    if (hx, hy) == (fx, fy):
        return []
    blocked = set(body) - {head}
    vertical_first = d in ("R", "L")
    orders = [True, False] if vertical_first else [False, True]
    for vf in orders:
        cells = []
        if vf:
            s = 1 if fy > hy else -1
            cells += [(hx, y) for y in range(hy + s, fy + s, s)]
            s2 = 1 if fx > hx else -1
            cells += [(x, fy) for x in range(hx + s2, fx + s2, s2)]
        else:
            s = 1 if fx > hx else -1
            cells += [(x, hy) for x in range(hx + s, fx + s, s)]
            s2 = 1 if fy > hy else -1
            cells += [(fx, y) for y in range(hy + s2, fy + s2, s2)]
        if not cells:
            continue
        first = (cells[0][0] - hx, cells[0][1] - hy)
        opp_vec = DIRS[OPP[d]]
        if first == opp_vec:
            continue
        ok = all(0 <= c[0] < GRID_X and 0 <= c[1] < GRID_Y for c in cells) and \
            not any(c in blocked for c in cells)
        if ok:
            return cells
    return None


def dir_from(h_prev, h_now):
    delta = (h_now[0] - h_prev[0], h_now[1] - h_prev[1])
    return {(0, 1): "D", (0, -1): "U", (1, 0): "R", (-1, 0): "L"}.get(delta, "R")


def runway_moves(head, d):
    """Straight moves left before a wall along current heading."""
    hx, hy = head
    if d == "R":
        return GRID_X - 1 - hx
    if d == "L":
        return hx
    if d == "U":
        return hy
    return GRID_Y - 1 - hy


# ---------------------------------------------------------------- main
def main():
    captures_target = int(os.environ.get("SD_CAPTURES", "7"))
    OUT = f"{ROOT}/run/s80_sd_autoplay"
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(OUT, exist_ok=True)

    taps = [START_TAP]
    committed = START_TAP[2]          # last committed tap frame
    prev_f1 = None                    # min frame of taps added last cycle
    base_shas = None
    captures = 0
    cycle = 0

    while captures < captures_target:
        obs = committed + 3
        n_frames = committed + 48
        run_dir = f"{OUT}/cycle_{cycle:02d}"
        rc = run_engine(taps, n_frames, run_dir)
        if rc != 0:
            print(f"cycle {cycle}: engine rc={rc}")
            sys.exit(1)
        shas = frame_shas(run_dir)

        if obs + 1 >= len(shas):
            print(f"cycle {cycle}: run too short ({len(shas)} frames)")
            sys.exit(1)

        frames = sorted(glob.glob(f"{run_dir}/frames/frame_*.png"))
        snake_obs, food_obs = read_board(frames[obs])
        snake_p, _ = read_board(frames[obs - 1])
        if not snake_obs or not food_obs or dialog_visible(frames[obs]):
            print(f"cycle {cycle}: dead/paused before obs frame {obs}")
            break
        head = head_of(frames[obs], snake_obs)
        head_p = head_of(frames[obs - 1], snake_p)
        d = dir_from(head_p, head)

        # FULL-PATH bend scheduling: taps for EVERY direction change along
        # the L-path, at (obs + j) — the move into cells[j] renders at
        # obs+j+1. The path is in-bounds (l_path validates), so a head
        # following the bends can never hit a wall mid-path; the post-
        # capture direction is handled by the escape tap below.
        plan_cells = l_path(head, d, food_obs, snake_obs)
        if plan_cells is None:
            print(f"cycle {cycle}: no safe path head={head} food={food_obs}")
            sys.exit(2)
        new_taps = []
        prev_dir = d
        for j, cell in enumerate(plan_cells):
            prev_cell = head if j == 0 else plan_cells[j - 1]
            nd = {v: k2 for k2, v in DIRS.items()}[
                (cell[0] - prev_cell[0], cell[1] - prev_cell[1])]
            if nd != prev_dir:
                assert nd != OPP[prev_dir], \
                    f"reverse guard violated: j={j} head={head} d={d} " \
                    f"cells={plan_cells} nd={nd} prev_dir={prev_dir}"
                b = BTN[DIRNAME_BTN[nd]]
                new_taps.append((b[0], b[1], obs + j))
                prev_dir = nd
        capture_frame = obs + len(plan_cells)
        dir_after = prev_dir
        # wall-escape: after capture the head continues in dir_after from
        # the food cell — if within 2 cells of the wall, turn perpendicular
        # inside the safe window
        rw = runway_moves(food_obs, dir_after)
        if rw <= 2:
            if dir_after in ("L", "R"):
                nd = "U" if food_obs[1] >= GRID_Y // 2 else "D"
            else:
                nd = "R" if food_obs[0] <= GRID_X // 2 else "L"
            esc_frame = capture_frame + max(rw - 1, 0)
            while any(t[2] == esc_frame for t in new_taps):
                esc_frame += 1
            new_taps.append((BTN[DIRNAME_BTN[nd]][0],
                             BTN[DIRNAME_BTN[nd]][1], esc_frame))
        captures += 1
        frames_used = sorted({t[2] for t in new_taps})
        assert len(frames_used) == len(new_taps), "duplicate tap frame"
        taps += new_taps
        committed = max([t[2] for t in taps] + [capture_frame + 1])

        # C7 prefix verification: frames 0..prev_f1 are identical — the
        # tap@prev_f1's game-logic effect lands at prev_f1+1 (S73 law).
        if base_shas:
            k = min(len(base_shas), (prev_f1 + 1) if prev_f1 is not None
                    else len(shas))
            mism = [i for i in range(k) if base_shas[i] != shas[i]]
            assert not mism, (f"prefix SHA mismatch at frames {mism[:3]} "
                              f"[prev_f1={prev_f1} k={k} "
                              f"taps={taps[:6]}...]")
        base_shas = shas

        prev_f1 = min(frames_used) if frames_used else None

        cycle += 1
        print(f"cycle {cycle}: head={head} d={d} path={len(plan_cells)} "
              f"captures={captures} +{len(new_taps)} taps "
              f"(committed@{committed})")

    # final continuous evidence run with the full committed schedule
    final_dir = f"{OUT}/final_run"
    total = committed + 60
    rc = run_engine(taps, total, final_dir)
    shas = frame_shas(final_dir)
    k = min(len(base_shas), (prev_f1 + 1) if prev_f1 is not None else len(shas),
            len(shas))
    mism = [i for i in range(k) if base_shas[i] != shas[i]]
    assert not mism, f"final prefix mismatch at {mism[:3]}"
    print(f"final continuous run: {len(shas)} frames, prefix verified {k} "
          f"frames, captures={captures}, rc={rc}")

    frames = sorted(glob.glob(f"{final_dir}/frames/frame_*.png"))
    food_seen = []
    for f in frames:
        _, food = read_board(f)
        if food and (not food_seen or food_seen[-1] != food):
            food_seen.append(food)
    print(f"final run distinct food placements: {len(food_seen)} -> {food_seen}")


if __name__ == "__main__":
    main()
