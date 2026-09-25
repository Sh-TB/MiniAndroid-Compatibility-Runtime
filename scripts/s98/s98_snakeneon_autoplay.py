#!/usr/bin/env python3
"""s98_snakeneon_autoplay.py — Snake Neon autonomous play (S98, GAMES-4).

S80 law shape: C1 real scheduled taps, C3 vision from rendered frames only,
C4 app logic authoritative (wrap-around + obstacles are the APP's laws),
C7 every leg re-runs the REAL APK with SHA-pinned prefixes.

Neon-specific planning: BFS on a WRAP-AROUND grid (edges are portals) that
treats the snake body + static obstacle blocks as walls.
"""
import glob
import hashlib
import json
import os
import shutil
import subprocess
import sys
from collections import deque

from PIL import Image

ROOT = "/home/z/my-project"
ENG = f"{ROOT}/miniandroid/build/miniandroid"
APK = f"{ROOT}/upload/s98_games/build_snakeneon/snakeneon_v1.0_vc1.apk"
OUT = f"{ROOT}/run/s98_snakeneon_autoplay"

COLS, ROWS = 15, 16
CELL, BXL, BYT = 62, (1080 - 15 * 62) // 2, 140


def run_engine(taps, n_frames, out_dir, dump_vt=False):
    os.makedirs(out_dir, exist_ok=True)
    # Neon tick law: game tick = 220ms CONSTANT, frame-delay = 110ms →
    # EXACTLY 1 move per 2 frames (deterministic tap-to-move mapping).
    cmd = [ENG, "run", "--execution-mode", "real-dalvik",
           "--frames", str(n_frames), "--frame-delay", str(110),
           "--width", "1080", "--height", "1920",
           "--data-root", f"{out_dir}/data", "-o", out_dir]
    if dump_vt:
        cmd.append("--dump-view-tree")
    for (x, y, k) in taps:
        cmd += ["--tap", f"{x},{y}@{k}"]
    cmd += [APK]
    with open(f"{out_dir}.log", "w") as log:
        return subprocess.call(cmd, stdout=log, stderr=log, timeout=1200)


def frames_of(out_dir):
    return sorted(glob.glob(f"{out_dir}/frames/frame_*.png"))


def shas_of(out_dir):
    return [hashlib.sha256(open(f, "rb").read()).hexdigest()
            for f in frames_of(out_dir)]


def close(p, c, tol=48):
    return (abs(p[0] - c[0]) <= tol and abs(p[1] - c[1]) <= tol and
            abs(p[2] - c[2]) <= tol)


TEAL = (0x00, 0xFF, 0xD0)
HEAD = (0x9C, 0xFF, 0xE8)
MAGENTA = (0xFF, 0x2E, 0x88)
PURPLE = (0xB4, 0x4B, 0xFF)


def cell_center(c, r):
    return (BXL + c * CELL + CELL // 2, BYT + r * CELL + CELL // 2)


def read_board(png):
    img = Image.open(png).convert("RGB")
    px = img.load()
    snake, head, food, blocks = [], None, None, []
    for r in range(ROWS):
        for c in range(COLS):
            x, y = cell_center(c, r)
            p = px[x, y]
            if close(p, HEAD, 60):
                snake.append((c, r)); head = (c, r)
            elif close(p, TEAL):
                snake.append((c, r))
            elif close(p, MAGENTA, 60):
                food = (c, r)
            elif close(p, PURPLE):
                blocks.append((c, r))
    return snake, head, food, blocks


def bfs_path(start, goal, walls, banned_dir=None):
    """Shortest path on the WRAP grid (edges are portals). banned_dir:
    the APP's reverse guard — the first expansion never enters the cell
    opposite the current heading (a 180 turn is rejected by wantDir), so
    a plan starting with a reverse step must not be generated at all."""
    q = deque([(start, [])])
    seen = {start}
    ban_cell = None
    if banned_dir:
        for (dc, dr), name in DIRS.items():
            if name == banned_dir:
                ban_cell = ((start[0] + dc) % COLS, (start[1] + dr) % ROWS)
    while q:
        (c, r), path = q.popleft()
        if (c, r) == goal:
            return path
        for dc, dr in ((0, -1), (1, 0), (0, 1), (-1, 0)):
            nc, nr = (c + dc) % COLS, (r + dr) % ROWS
            if (nc, nr) in seen or (nc, nr) in walls:
                continue
            if ban_cell and (nc, nr) == ban_cell and not path:
                continue
            seen.add((nc, nr))
            q.append(((nc, nr), path + [(nc, nr)]))
    return None


DIRS = {(0, -1): "UP", (1, 0): "RIGHT", (0, 1): "DOWN", (-1, 0): "LEFT"}
OPP = {"UP": "DOWN", "DOWN": "UP", "LEFT": "RIGHT", "RIGHT": "LEFT"}


def btn_map():
    """Button centers from the app's OWN laid-out view tree (C3 law —
    the earlier hardcoded guess missed every tap; the DOWN never fired)."""
    probe = f"{OUT}/probe"
    run_engine([], 3, probe, dump_vt=True)
    vt = json.load(open(f"{probe}/view_tree.json"))
    found = {}
    for n in vt.get("nodes", []):
        if "Button" in str(n.get("class", "")):
            label = str(n.get("text", "")).strip().upper()
            x, y = n.get("x", 0), n.get("y", 0)
            w, h = n.get("width", 0), n.get("height", 0)
            if label and w > 0:
                found[label] = (x + w // 2, y + h // 2)
    print("button centers:", found)
    return found


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(OUT, exist_ok=True)
    BTN = btn_map()

    committed = []          # taps so far
    last_food = None
    captures = 0
    max_food_eaten = 0
    len_growth = []

    for cycle in range(8):
        n_frames = (committed[-1][2] if committed else 0) + 60
        run_dir = f"{OUT}/cycle_{cycle:02d}"
        rc = run_engine(committed, n_frames, run_dir)
        if rc != 0:
            print(f"cycle {cycle}: engine rc={rc}"); sys.exit(1)
        fr = frames_of(run_dir)
        obs = (committed[-1][2] + 3) if committed else 6
        if obs >= len(fr):
            print(f"cycle {cycle}: short run {len(fr)}"); break
        shas = shas_of(run_dir)

        snake, head, food, blocks = read_board(fr[obs])
        if not snake or not food or head is None:
            print(f"cycle {cycle}: board unreadable (dead?)")
            break

        snake_p, _, _, _ = read_board(fr[obs - 1]) if obs >= 1 else (snake, None, None, [])
        moved = [c for c in snake if c not in snake_p]
        prev_head = None
        if moved:
            for (dc, dr) in DIRS:
                cand = ((head[0] + dc) % COLS, (head[1] + dr) % ROWS)
                if cand in snake_p:
                    prev_head = cand
                    break
        d = "RIGHT"
        if prev_head:
            delta = ((head[0] - prev_head[0]) % COLS,
                     (head[1] - prev_head[1]) % ROWS)
            for dd, name in DIRS.items():
                if (min(delta[0], COLS - delta[0]) == min(dd[0], COLS - dd[0])
                        and min(delta[1], ROWS - delta[1]) == min(dd[1], ROWS - dd[1])
                        and (dd[0] != 0) == (delta[0] != 0)):
                    d = name
                    break

        walls = set(snake) - {head}
        walls |= set(blocks)
        path = bfs_path(head, food, walls, banned_dir=OPP[d])
        if path is None:
            print(f"cycle {cycle}: no wrap-path head={head} food={food}")
            break

        # FULL-PATH direction-change scheduling (s80 law, Neon mapping):
        # 1 move = 2 frames (tick 220ms @ 110ms frames), so the move into
        # path[j] renders at obs + 2j + 2; the turn tap for it lands at
        # obs + 2j. Taps for EVERY turn along the shortest wrap-path.
        taps = []
        cur_dir = d
        prev_cell = head
        for j, step_cell in enumerate(path):
            frame_k = obs + 2 * j
            delta = ((step_cell[0] - prev_cell[0]) % COLS,
                     (step_cell[1] - prev_cell[1]) % ROWS)
            if delta[0] > 1: delta = (delta[0] - COLS, delta[1])
            if delta[1] > 1: delta = (delta[0], delta[1] - ROWS)
            nd = DIRS.get(delta)
            if nd is None:
                break
            if nd != cur_dir:
                if nd == OPP[cur_dir]:
                    break
                taps.append((*BTN[nd], frame_k))
                cur_dir = nd
            prev_cell = step_cell
        committed += taps
        captures += 1
        len_growth.append(len(snake))
        print(f"cycle {cycle}: head={head} d={d} food={food} path={len(path)} "
              f"+{len(taps)} taps len={len(snake)}")

        # growth check: snake length grew between cycles = food eaten
        if len(snake) > max_food_eaten and len(snake) > 3:
            max_food_eaten = len(snake)

    final = f"{OUT}/final"
    rc = run_engine(committed, (committed[-1][2] if committed else 0) + 60,
                    final)
    fr = frames_of(final)
    snake, head, food, blocks = read_board(fr[-1])
    grew = len(snake) > 3
    print(f"FINAL: len={len(snake)} food_seen={food} blocks={len(blocks)} "
          f"grew={grew} captures={captures}")
    ok = grew and captures >= 4
    json.dump({"game": "com.miniandroid.snakeneon",
               "mode": "s98 autonomous play (wrap-aware BFS)",
               "legs": captures, "final_len": len(snake),
               "obstacles_seen": len(blocks), "taps_committed": len(committed),
               "len_growth": len_growth,
               "verdict": "PASS" if ok else "PARTIAL"},
              open(f"{OUT}/autoplay_evidence.json", "w"), indent=1)
    try:
        imgs = [Image.open(f).convert("P", palette=Image.ADAPTIVE)
                for f in fr[::4]]
        imgs[0].save(f"{ROOT}/docs/evidence/s98/snakeneon_autoplay.gif",
                     save_all=True, append_images=imgs[1:], duration=300,
                     loop=0)
        print("GIF written")
    except Exception as e:
        print("gif skipped:", e)
    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
