#!/usr/bin/env python3
"""s73_snake_controller.py — S73 PART C: AUTONOMOUS AndroidGameSnake gameplay.

Constitution compliance:
- C1: controller NEVER mutates game state, injects positions, calls private
  methods, or bypasses Activity/View/input. Its ONLY actuator is scheduled
  taps (x,y@frame) through the canonical TouchDispatcher DOWN/UP law
  pipeline — the same path a user's finger takes.
- C3: vision comes from RENDERED FRAMES ONLY (snake cells #FF4081, food
  #0000ff on the 20x20 / 39px grid of SnakePanelView). Tap targets come from
  legitimate observable View geometry (view_tree.json button centers).
  No hidden game memory is read.
- C4: the app's own game logic stays authoritative (reverse-direction guard,
  walls, growth are the APP's laws; the planner merely chooses legal taps).
- C7: determinism — every decision cycle re-runs the REAL APK from launch;
  prefix frame pixel-SHAs are re-verified against the previous run. The
  final evidence run is one continuous deterministic session, replayed x3.

Movement law (learned from observed frames, S73 sched test):
  head = last-grown cell; initial direction RIGHT after START@1;
  1 cell/frame; a tap scheduled at frame k takes effect on the move
  rendered in frame k+1 (tap fires after frame k renders).
"""
import json
import os
import subprocess
import sys
import hashlib
import glob
from PIL import Image

ROOT = "/home/z/my-project"
ENG = f"{ROOT}/miniandroid/build/miniandroid"
APK = f"{ROOT}/upload/s72_w4_apks/snake_v1.0_vc1.apk"
GRID = 20          # 20x20 cells
CELL = 39          # 39 px/cell (1080x780 panel)
SNAKE_RGB = (255, 64, 129)
FOOD_RGB = (0, 0, 255)

# Button centers — legitimate observable geometry (view_tree.json, EXP-061)
BTN = {"TOP": (539, 860), "LEFT": (220, 999), "RIGHT": (858, 999),
       "BOTTOM": (539, 1457), "START": (98, 839)}
DIRNAME_BTN = {"U": "TOP", "D": "BOTTOM", "L": "LEFT", "R": "RIGHT"}
DIRS = {"U": (0, -1), "D": (0, 1), "L": (-1, 0), "R": (1, 0)}
OPP = {"U": "D", "D": "U", "L": "R", "R": "L"}


# ---------------------------------------------------------------- vision
def frame_cells(png_path):
    """Extract snake/food cell lists from one rendered frame (pixels only)."""
    img = Image.open(png_path).convert("RGB")
    if img.size != (1080, 1920):
        return None, None
    px = img.load()
    snake, food = [], []
    for r in range(GRID):
        for c in range(GRID):
            p = px[c * CELL + 20, r * CELL + 20]
            if p == SNAKE_RGB:
                snake.append((c, r))
            elif p == FOOD_RGB:
                food.append((c, r))
    return snake, food


def analyze_run(run_dir):
    """Per-frame observation list for a completed engine run."""
    frames = sorted(glob.glob(f"{run_dir}/frames/frame_*.png"))
    obs, prev_head = [], None
    for i, f in enumerate(frames):
        snake, food = frame_cells(f)
        img = Image.open(f).convert("RGB")
        psha = hashlib.sha256(img.tobytes()).hexdigest()[:16]
        head = d = None
        if snake:
            # head = the cell just grown this frame = the one absent from
            # the previous frame's set; for the first snake frame it is the
            # observed START-state head (list order: head last).
            if prev_head is None:
                head = snake[-1]
                d = "R"        # observed initial law after START
            else:
                grown = [c for c in snake if not _in_prev(c, obs, i)]
                head = grown[0] if grown else None
                if head and prev_head:
                    delta = (head[0] - prev_head[0], head[1] - prev_head[1])
                    d = {(0, 1): "D", (0, -1): "U", (1, 0): "R",
                         (-1, 0): "L"}.get(delta)
        obs.append({
            "frame_file": os.path.basename(f),
            "frame_index": i,
            "png_sha256": psha,
            "snake": snake,
            "food": food,
            "head": head,
            "dir": d,
            "game_over": i > 1 and snake == [],
        })
        if head:
            prev_head = head
    return obs


def _in_prev(cell, obs, i):
    """Was `cell` part of the snake one observation earlier?"""
    j = i - 1
    return j >= 0 and cell in obs[j]["snake"]


def game_over(obs):
    return any(o["game_over"] for o in obs)


# ---------------------------------------------------------------- engine
def taps_args(taps):
    out = []
    for t in taps:
        out += ["--tap", f"{t[0]},{t[1]}@{t[2]}"]
    return out


def run_engine(taps, n_frames, out_dir, frame_delay=250):
    """One continuous real run from launch. taps: [(x, y, frame)]."""
    os.makedirs(out_dir, exist_ok=True)
    cmd = [ENG, "run", "--execution-mode", "real-dalvik",
           "--frames", str(n_frames), "--frame-delay", str(frame_delay),
           "--dump-view-tree", "-o", out_dir] + taps_args(taps) + [APK]
    with open(f"{out_dir}/engine.log", "w") as log:
        rc = subprocess.call(cmd, stdout=log, stderr=log, timeout=2400)
    return rc


# ---------------------------------------------------------------- planning
def build_path(head, d, food, body, grid=GRID):
    """Exact L-shaped cell path from head to food (axis order chosen by
    safety). Returns list of cells starting at head, or None if unsafe.
    Cells are strictly consecutive (1-cell steps, no duplicates)."""
    fx, fy = food
    hx, hy = head
    if (hx, hy) == (fx, fy):
        return [head]
    vertical_first = d in ("R", "L")
    orders = [True, False] if vertical_first else [False, True]
    for vf in orders:
        cells = [head]
        if vf:
            s = 1 if fy > hy else -1
            cells += [(hx, y) for y in range(hy + s, fy + s, s)]  # to (hx,fy)
            s2 = 1 if fx > hx else -1
            cells += [(x, fy) for x in range(hx + s2, fx + s2, s2)]
        else:
            s = 1 if fx > hx else -1
            cells += [(x, hy) for x in range(hx + s, fx + s, s)]  # to (fx,hy)
            s2 = 1 if fy > hy else -1
            cells += [(fx, y) for y in range(hy + s2, fy + s2, s2)]
        # safety: inside grid; no body collision (body minus the tail cell
        # that will have moved — conservative: full body, minus head)
        blocked = set(body) - {head}
        ok = all(0 <= c[0] < grid and 0 <= c[1] < grid for c in cells) and \
            not any(c in blocked for c in cells[1:])
        if ok:
            return cells
    return None


def plan_taps(head, d, food, body, arrive_frame, capture_guard=True):
    """Convert an L-path into scheduled taps. arrive_frame = frame index at
    which `head` is rendered (i.e. the last OBSERVED frame). Tap for the
    step leaving cell path[j] is scheduled at frame arrive+j-1 ... wait:
    tap@k affects the move rendered in frame k+1 → for the move into
    path[j+1] (frame arrive+j+1), tap at frame arrive+j.
    Returns (taps, capture_frame, escape_tap)."""
    cells = build_path(head, d, food, body)
    if cells is None:
        return None, None, None
    taps, capture_frame = [], None
    prev_dir = d
    for j in range(1, len(cells)):
        step = (cells[j][0] - cells[j - 1][0], cells[j][1] - cells[j - 1][1])
        nd = {v: k for k, v in DIRS.items()}[step]
        tap_frame = arrive_frame + j - 1
        if nd != prev_dir:
            if nd == OPP[prev_dir]:
                return None, None, None       # would be reverse-guarded
            b = BTN[DIRNAME_BTN[nd]]
            taps.append((b[0], b[1], tap_frame))
            prev_dir = nd
        if cells[j] == food:
            capture_frame = arrive_frame + j
            break
    escape = None
    if capture_frame is not None and capture_guard:
        # after capture the head continues in prev_dir — turn away from
        # any wall it would hit next frame (app game-over law)
        fx, fy = food
        danger = (prev_dir == "L" and fx == 0) or \
                 (prev_dir == "R" and fx == GRID - 1) or \
                 (prev_dir == "U" and fy == 0) or \
                 (prev_dir == "D" and fy == GRID - 1)
        if danger:
            esc = ("D" if fy < GRID - 1 else "U") if prev_dir in ("L", "R") \
                else ("R" if fx < GRID - 1 else "L")
            b = BTN[DIRNAME_BTN[esc]]
            escape = (b[0], b[1], capture_frame)
            taps.append(escape)
    return taps, capture_frame, escape


def count_events(obs):
    """moves = frames with a head advance after START; turns = accepted
    direction changes (observed); captures = snake GROWTH events (len
    increase at frames >= 3 — the app grows the snake exactly when food is
    captured; the food teleports to its new spawn in the same render, so
    head-on-food is a weaker signal). Reverse rejections are observed
    separately by the C4 probe."""
    moves = turns = captures = 0
    prev_d, prev_len = None, None
    for idx, o in enumerate(obs):
        if o["head"] is None:
            continue
        if idx >= 2 and o["head"]:
            moves += 1
        if o["dir"] and prev_d and o["dir"] != prev_d:
            turns += 1
        if o["dir"]:
            prev_d = o["dir"]
        if prev_len is not None and len(o["snake"]) > prev_len and idx >= 3:
            captures += 1
        prev_len = len(o["snake"]) if o["snake"] else prev_len
    return {"moves": moves, "turns": turns, "captures": captures}


def plan_zigzag(head, d, arrive_frame, n_taps=8, grid=GRID):
    """Serpentine staircase: alternate two perpendicular directions every
    2 frames (never reverse — the app's guard would reject). Chosen away
    from the nearest walls. Returns taps list."""
    hx, hy = head
    dx = "R" if hx < grid - 6 else "L"
    dy = "D" if hy < grid - 6 else "U"
    first = dy if d in ("R", "L") else dx
    second = dx if first == dy else dy
    taps, f = [], arrive_frame
    for i in range(n_taps):
        nd = first if i % 2 == 0 else second
        b = BTN[DIRNAME_BTN[nd]]
        taps.append((b[0], b[1], f))
        f += 2          # 2 cells between turns (1 cell/frame observed law)
    return taps


# ---------------------------------------------------------------- driver
def pixel_sha(path):
    return hashlib.sha256(
        Image.open(path).convert("RGB").tobytes()).hexdigest()[:16]


def verify_prefix(obs, prev_obs, min_len):
    """C7 determinism guard: the shared prefix of two runs must be
    pixel-identical frame by frame."""
    for i in range(min_len):
        if obs[i]["png_sha256"] != prev_obs[i]["png_sha256"]:
            return False, i
    return True, None


def iterate(max_iters=14, goal_turns=20, goal_moves=20, tail_dir=None):
    work = f"{ROOT}/run/s73_snake_auto"
    os.makedirs(work, exist_ok=True)
    # taps: START at frame 1, then controller taps. N grows each iteration.
    taps = [(BTN["START"][0], BTN["START"][1], 1)]
    n_frames = 8
    prev_obs, prev_n = None, 0
    history = []
    for it in range(1, max_iters + 1):
        rd = f"{work}/iter_{it:02d}"
        rc = run_engine(taps, n_frames, rd)
        obs = analyze_run(rd)
        # determinism guard vs previous iteration prefix
        if prev_obs is not None:
            ok, bad = verify_prefix(obs, prev_obs, min(len(obs), prev_n))
            if not ok:
                return {"status": "NONDETERMINISTIC_PREFIX",
                        "iteration": it, "first_divergence_frame": bad}
        ev = count_events(obs)
        over = game_over(obs)
        history.append({"iteration": it, "frames": len(obs),
                        "taps": len(taps), **ev,
                        "game_over": over, "run_dir": rd})
        print(f"[iter {it:02d}] frames={len(obs)} taps={len(taps)} "
              f"moves={ev['moves']} turns={ev['turns']} "
              f"captures={ev['captures']} game_over={over}", flush=True)
        if over:
            return {"status": "GAME_OVER", "history": history,
                    "last_run": rd}
        if ev["turns"] >= goal_turns and ev["moves"] >= goal_moves \
                and ev["captures"] >= 1:
            return {"status": "GOALS_MET", "history": history,
                    "last_run": rd, "events": ev}
        # ---- plan the next leg from the LAST observed state.
        # Taps already CONSUMED (frame < last observed frame: their effect
        # is visible in rendered frames) stay for prefix stability; every
        # still-future tap is replaced by the fresh plan (self-correction).
        last = None
        for o in reversed(obs):
            if o["head"] is not None and o["food"]:
                last = o
                break
        if last is None:
            return {"status": "NO_STATE", "history": history}
        last_frame_idx = last["frame_index"]
        burned = [t for t in taps if t[2] < last_frame_idx]
        d = last["dir"] or "R"
        if ev["captures"] >= 1 and ev["moves"] >= goal_moves \
                and ev["turns"] < goal_turns:
            # top-up phase: serpentine turns until the turn goal is met
            new_taps = plan_zigzag(last["head"], d, last_frame_idx,
                                   n_taps=min(goal_turns - ev["turns"] + 2,
                                              10))
            cap_f = None
        else:
            new_taps, cap_f, esc = plan_taps(
                last["head"], d, last["food"][0], last["snake"],
                last_frame_idx)
        if new_taps is None:
            # no safe L-path (rare) — serpentine: turn perpendicular and retry
            b = BTN[DIRNAME_BTN["D" if d in ("L", "R") else "R"]]
            new_taps = [(b[0], b[1], last_frame_idx)]
            cap_f = None
        taps = burned + [t for t in new_taps]
        n_frames = max(n_frames,
                       (max(t[2] for t in taps) if taps else 1) + 8)
        prev_obs, prev_n = obs, len(obs)
    return {"status": "MAX_ITERS", "history": history,
            "last_run": history[-1]["run_dir"] if history else None}


if __name__ == "__main__":
    result = iterate()
    print(json.dumps(result, indent=1, default=str)[:4000])
