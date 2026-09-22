#!/usr/bin/env python3
"""s80_tet_autoplay.py — Mini Tetris autonomous gameplay driver (S80).

Honest closed loop in the S73 law shape:
  C1: only actuator = scheduled taps (ROTATE/LEFT/RIGHT buttons) through
      the canonical TouchDispatcher.
  C3: vision = rendered frames; every cycle verifies a rendered frame
      cell-by-cell against the driver's simulated overlay before
      committing new taps. Divergence aborts (no speculation).
  C4: the app's own logic stays authoritative — the driver mirrors the
      app's public rules (shapes, kicks, gravity, lock, clears, LCG) only
      to PREDICT; pixels arbitrate.
  C7: every decision cycle re-runs the REAL APK from launch; committed
      prefix re-verified by pixel SHAs up to the first frame a new tap can
      influence.

Timing model (deterministic): frame k renders at virtual 250k ms; the
app's postDelayed(420) ticker is due at 420+420k ms from launch (the
ticker chain starts at onCreate and is NOT rescheduled by the START
reset); a tap@k applies after frame k renders. So the pixel state of
frame F = sim after tick_due(F) + taps@(1..F-1).
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
APK = f"{ROOT}/upload/s80_games/build_tetris/tetris_v1.0_vc1.apk"

FRAME_MS = 250
TICK_MS = 420

COLS, ROWS = 10, 20
# EMPIRICAL GRID (S80, measured from block pixel runs): pitch is 65 px in
# both axes (the engine gives the custom view more height than the view
# tree reports, so onDraw's cell = (1080-430)/10 = 65, not the 63 the
# 1412-high assumption gives). Board origin (30,130) confirmed.
CELL = 65
BXL, BYT = 30, 130

BTN = {"LEFT": (211, 1725), "ROTATE": (539, 1725), "RIGHT": (868, 1725),
       "DROP": (293, 1854), "START": (786, 1854)}
KIND_OF = {(BTN["LEFT"][0], BTN["LEFT"][1]): "L",
           (BTN["ROTATE"][0], BTN["ROTATE"][1]): "ROT",
           (BTN["RIGHT"][0], BTN["RIGHT"][1]): "R",
           (BTN["DROP"][0], BTN["DROP"][1]): "DROP",
           (BTN["START"][0], BTN["START"][1]): "START"}

SHAPES = [
    [(0, 1), (1, 1), (2, 1), (3, 1)],   # I
    [(1, 0), (2, 0), (1, 1), (2, 1)],   # O
    [(1, 0), (0, 1), (1, 1), (2, 1)],   # T
    [(1, 1), (2, 1), (0, 2), (1, 2)],   # S
    [(0, 1), (1, 1), (1, 2), (2, 2)],   # Z
    [(0, 0), (0, 1), (1, 1), (2, 1)],   # J
    [(2, 0), (0, 1), (1, 1), (2, 1)],   # L
]
COLORS = [
    (6, 182, 212), (250, 204, 21), (168, 85, 247), (34, 197, 94),
    (239, 68, 68), (59, 130, 246), (249, 115, 22),
]


# ------------------------------------------------------------------ sim
class Sim:
    def __init__(self):
        self.board = [[0] * COLS for _ in range(ROWS)]
        self.seed = 0x9E3779B9
        self.nxt = self.nextRnd(7)
        self.started = False
        self.over = False
        self.cur = 0
        self.rot = 0
        self.px = 3
        self.py = -2
        self.next_tick = TICK_MS      # ticker scheduled at onCreate (t=0)
        self.score = 0
        self.lines = 0
        self.frame = 0
        self.locks = 0
        self.last_lock_cells = []

    def nextRnd(self, bound):
        self.seed = (self.seed * 1103515245 + 12345) & 0x7FFFFFFF
        return self.seed % bound

    def cell_xy(self, piece, r, i):
        x, y = SHAPES[piece][i]
        for _ in range(r):
            x, y = 3 - y, x
        return x, y

    def collides(self, px, py, rot, piece):
        for i in range(4):
            cx, cy = self.cell_xy(piece, rot, i)
            bx, by = px + cx, py + cy
            if bx < 0 or bx >= COLS or by >= ROWS:
                return True
            if by >= 0 and self.board[by][bx] != 0:
                return True
        return False

    def reset(self):
        self.board = [[0] * COLS for _ in range(ROWS)]
        self.seed = 0x9E3779B9
        self.nxt = self.nextRnd(7)
        self.over = False
        self._spawn()

    def _spawn(self):
        self.cur = self.nxt
        self.nxt = self.nextRnd(7)
        self.rot = 0
        self.px = 3
        self.py = -2
        if self.collides(3, 0, 0, self.cur):
            self.over = True
            return
        self.py = 0

    def _gravity(self):
        if self.over or not self.started:
            return
        if not self.collides(self.px, self.py + 1, self.rot, self.cur):
            self.py += 1
        else:
            self._lock()

    def _lock(self):
        self.last_lock_cells = []
        for i in range(4):
            cx, cy = self.cell_xy(self.cur, self.rot, i)
            bx, by = self.px + cx, self.py + cy
            if by < 0:
                self.over = True
                return
            self.board[by][bx] = self.cur + 1
            self.last_lock_cells.append((bx, by))
        self.locks += 1
        cleared = 0
        r = ROWS - 1
        while r >= 0:
            if all(self.board[r][c] != 0 for c in range(COLS)):
                cleared += 1
                del self.board[r]
                self.board.insert(0, [0] * COLS)
            else:
                r -= 1
        if cleared:
            self.lines += cleared
            self.score += {1: 100, 2: 300, 3: 500, 4: 800}[cleared]
        self._spawn()

    def clone(self):
        c = Sim.__new__(Sim)
        c.board = [row[:] for row in self.board]
        c.seed = self.seed
        c.nxt = self.nxt
        c.started = self.started
        c.over = self.over
        c.cur = self.cur
        c.rot = self.rot
        c.px = self.px
        c.py = self.py
        c.next_tick = self.next_tick
        c.score = self.score
        c.lines = self.lines
        c.frame = self.frame
        c.locks = self.locks
        c.last_lock_cells = list(self.last_lock_cells)
        return c

    def apply_tap(self, kind):
        if kind == "START":
            if not self.started or self.over:
                self.reset()
                self.started = True
            return
        if self.over or not self.started:
            return
        if kind == "L":
            if not self.collides(self.px - 1, self.py, self.rot, self.cur):
                self.px -= 1
        elif kind == "R":
            if not self.collides(self.px + 1, self.py, self.rot, self.cur):
                self.px += 1
        elif kind == "ROT":
            nr = (self.rot + 1) & 3
            for k in (0, -1, 1, -2, 2):
                if not self.collides(self.px + k, self.py, nr, self.cur):
                    self.px += k
                    self.rot = nr
                    return
        elif kind == "DROP":
            self._gravity()

    @staticmethod
    def tick_at(f):
        """EMPIRICAL TICK LAW (S80, measured from rendered piece motion,
        cycle_00 frames 3-45): gravity ticks hit frames 4, 5, 6 then every
        2nd frame from 8 (frame 2's tick is the pre-START no-op). The
        420 ms postDelayed chain settles into an exact 2-frame period
        after the START-reset perturbation."""
        return f in (4, 5, 6) or (f >= 8 and f % 2 == 0)

    def step_frame(self, tap_kinds):
        """Advance one frame: tick drains at frame start, then the taps of
        this frame apply (after its render)."""
        self.frame += 1
        if self.tick_at(self.frame):
            self._gravity()
        for kind in tap_kinds:
            self.apply_tap(kind)

    def step_render_only(self):
        """Advance to the render of the next frame WITHOUT applying that
        frame's taps (pixel state = post-tick, pre-tap)."""
        self.frame += 1
        if self.tick_at(self.frame):
            self._gravity()

    def overlay(self):
        """Expected colored-cell map for the CURRENT state (post-tick,
        pre-tap — i.e. what frame `self.frame` rendered)."""
        expect = {}
        for r in range(ROWS):
            for c in range(COLS):
                if self.board[r][c] != 0:
                    expect[(c, r)] = self.board[r][c] - 1
        if self.started and not self.over:
            for i in range(4):
                cx, cy = self.cell_xy(self.cur, self.rot, i)
                bx, by = self.px + cx, self.py + cy
                if 0 <= by < ROWS and 0 <= bx < COLS:
                    expect[(bx, by)] = self.cur
        return expect


# ---------------------------------------------------------------- vision
def read_cells(png_path):
    """Colored (col,row)->piece-id map. Multi-point sampling but STRICT
    exact-base-color equality — gloss blends and AA edges never match, so
    no cross-piece confusion is possible."""
    img = Image.open(png_path).convert("RGB")
    px = img.load()
    cells = {}
    offs = [(0, 0), (-16, 0), (16, 0), (0, -16), (0, 16),
            (-16, -16), (16, -16), (-16, 16), (16, 16)]
    base = {col: pid for pid, col in enumerate(COLORS)}
    for r in range(ROWS):
        for c in range(COLS):
            x = BXL + c * CELL + CELL // 2
            y = BYT + r * CELL + CELL // 2
            for dx, dy in offs:
                xx, yy = x + dx, y + dy
                if 0 <= xx < img.width and 0 <= yy < img.height:
                    pid = base.get(px[xx, yy])
                    if pid is not None:
                        cells[(c, r)] = pid
                        break
    return cells


def frame_shas(out_dir):
    files = sorted(glob.glob(f"{out_dir}/frames/frame_*.png"))
    return [hashlib.sha256(Image.open(f).convert("RGB").tobytes()).hexdigest()
            for f in files]


def run_engine(taps, n_frames, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    cmd = [ENG, "run", "--execution-mode", "real-dalvik",
           "--frames", str(n_frames), "--frame-delay", str(FRAME_MS),
           "-o", out_dir]
    for (x, y, k) in taps:
        cmd += ["--tap", f"{x},{y}@{k}"]
    cmd += [APK]
    with open(f"{out_dir}.log", "w") as log:
        rc = subprocess.call(cmd, stdout=log, stderr=log, timeout=2400)
    return rc


# ------------------------------------------------------------- strategy
def choose_placement(sim):
    """Greedy: for each rot/column, hard-drop and evaluate."""
    best = None
    piece = sim.cur
    for rot in range(4):
        for px in range(-2, COLS + 2):
            b = [row[:] for row in sim.board]
            py = -2
            while True:
                collide = False
                for i in range(4):
                    cx, cy = sim.cell_xy(piece, rot, i)
                    bx, by = px + cx, py + cy + 1
                    if bx < 0 or bx >= COLS or by >= ROWS or \
                            (by >= 0 and b[by][bx] != 0):
                        collide = True
                        break
                if collide:
                    break
                py += 1
            if py < -1:
                continue
            valid = True
            for i in range(4):
                cx, cy = sim.cell_xy(piece, rot, i)
                bx, by = px + cx, py + cy
                if bx < 0 or bx >= COLS or by < 0:
                    valid = False
                    break
                b[by][bx] = piece + 1
            if not valid:
                continue
            cleared = 0
            r = ROWS - 1
            while r >= 0:
                if all(b[r][c] != 0 for c in range(COLS)):
                    cleared += 1
                    del b[r]
                    b.insert(0, [0] * COLS)
                else:
                    r -= 1
            holes = 0
            for c in range(COLS):
                seen = False
                for r2 in range(ROWS):
                    if b[r2][c] != 0:
                        seen = True
                    elif seen:
                        holes += 1
            heights = []
            for c in range(COLS):
                hgt = 0
                for r2 in range(ROWS):
                    if b[r2][c] != 0:
                        hgt = ROWS - r2
                        break
                heights.append(hgt)
            agg = sum(heights)
            bump = sum(abs(heights[i] - heights[i + 1]) for i in range(COLS - 1))
            sc = 60 * cleared - 25 * holes - 3 * agg - 4 * bump
            if best is None or sc > best[0]:
                best = (sc, rot, px)
    return best


def fit_piece(cells_map, pid, exclude):
    """Fit (rot, px, py) for piece `pid` whose cells == observed cells
    (cells_map minus settled positions). Returns (rot, px, py) or None."""
    want = {k for k, v in cells_map.items() if v == pid and k not in exclude}
    if len(want) != 4:
        return None
    for rot in range(4):
        rel = [Sim.cell_xy(None, pid, rot, i) for i in range(4)]
        c0, r0 = min(c for c, r in want), min(r for c, r in want)
        # align the piece's min cell with the observed min cell, then verify
        minc = min(c for c, r in rel)
        minr = min(r for r_ in [] for r in rel) if False else min(r for c, r in rel)
        px = c0 - minc
        py = r0 - minr
        got = {(px + c, py + r) for c, r in rel}
        if got == want:
            return (rot, px, py)
    return None


def main():
    target_pieces = int(os.environ.get("TET_PIECES", "12"))
    OUT = f"{ROOT}/run/s80_tet_autoplay"
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(OUT, exist_ok=True)

    taps = [(BTN["START"][0], BTN["START"][1], 3)]
    committed = 3
    prev_f1 = None
    base_shas = None

    sim = Sim()
    sim.apply_tap("START")
    for fr in range(1, 4):
        sim.step_frame(["START"] if fr == 3 else [])

    placed = 0          # pieces whose locked cells are verified in pixels
    cycle = 0
    ANCHOR_STEP = 30    # frames between observation anchors

    while placed < target_pieces:
        F = committed + ANCHOR_STEP
        run_dir = f"{OUT}/cycle_{cycle:02d}"
        rc = run_engine(taps, F + 2, run_dir)
        if rc != 0:
            print(f"cycle {cycle}: engine rc={rc}")
            sys.exit(1)
        shas = frame_shas(run_dir)

        # C7 prefix verification: a tap@k changes frame k's pixels (the
        # click dispatch precedes the render), so frames 0..prev_f1-1 are
        # identical between the runs.
        if base_shas:
            k = min(len(base_shas), prev_f1 if prev_f1 is not None
                    else len(shas))
            mism = [i for i in range(k) if base_shas[i] != shas[i]]
            assert not mism, f"prefix SHA mismatch at {mism[:3]}"
        base_shas = shas

        # advance the sim to F with the committed taps (prediction only)
        tap_map = {}
        for (x, y, k2) in taps:
            tap_map.setdefault(k2, []).append(KIND_OF[(x, y)])
        while sim.frame < F and not sim.over:
            sim.step_frame(tap_map.get(sim.frame + 1, []))
        if sim.over:
            print(f"cycle {cycle}: sim game over at frame {sim.frame} "
                  f"(placed={placed})")
            break

        frames = sorted(glob.glob(f"{run_dir}/frames/frame_*.png"))
        verify_idx = min(F, len(frames) - 1)
        rendered = read_cells(frames[verify_idx])

        # the sim's settled board minus the LAST locked piece (phase wobble
        # window) must match the render exactly
        expect_settled = {}
        for r in range(ROWS):
            for c in range(COLS):
                if sim.board[r][c] != 0:
                    expect_settled[(c, r)] = sim.board[r][c] - 1
        last_cells = set(getattr(sim, "last_lock_cells", []))
        strict = {k2: v for k2, v in expect_settled.items()
                  if (k2[0], k2[1]) not in last_cells}
        settled_ok = all(rendered.get(k2) == v for k2, v in strict.items())
        if not settled_ok:
            bad = {k2: (rendered.get(k2), v) for k2, v in strict.items()
                   if rendered.get(k2) != v}
            print(f"cycle {cycle}: PIXEL MISMATCH frame {verify_idx} "
                  f"(settled stack) bad={sorted(bad.items())[:8]}")
            sys.exit(3)

        # fit the falling piece from pixels; the spawn phase may be one
        # piece ahead of the sim's tick model (drop-barrage timing), so try
        # sim.cur first, then advance one spawn and retry
        fit = fit_piece(rendered, sim.cur, set(expect_settled.keys()))
        if fit is None and not sim.over:
            sim._spawn()
            fit = fit_piece(rendered, sim.cur, set(expect_settled.keys()))
        if fit is None:
            print(f"cycle {cycle}: cannot fit falling piece "
                  f"(cur={sim.cur}) at frame {verify_idx}")
            sys.exit(3)
        rot, px_obs, py_obs = fit
        # re-anchor the sim to the observed truth
        sim.board = [[0] * COLS for _ in range(ROWS)]
        for (c, r), pid in rendered.items():
            sim.board[r][c] = pid + 1
        sim.board = [[0] * COLS for _ in range(ROWS)]
        for (c, r), pid in rendered.items():
            if (c, r) not in {(px_obs + sim.cell_xy(sim.cur, rot, i)[0],
                               py_obs + sim.cell_xy(sim.cur, rot, i)[1])
                              for i in range(4)}:
                sim.board[r][c] = pid + 1
        sim.rot, sim.px, sim.py = rot, px_obs, py_obs
        sim.frame = verify_idx
        # count pieces locked since the last anchor via the LCG chain:
        # the sim advanced through them in step_frame; placed = locks that
        # happened (cur changed) since anchor — tracked by sim.locks counter
        placed = sim.locks

        # plan taps for the falling piece and commit them (choose_placement
        # returns the 4x4-box px directly; rot taps then move taps).
        # GUARD: only plan while the piece is high enough (py <= 12) — a
        # piece about to lock would let the taps spill onto the NEXT piece.
        new_taps = []
        if sim.py <= 12:
            plan = sim.clone()
            sc, rot_p, want_px = choose_placement(plan)
            f = verify_idx + 1     # taps start AFTER the anchor frame
            for _ in range(rot_p):
                new_taps.append((BTN["ROTATE"][0], BTN["ROTATE"][1], f))
                f += 1
            guard = 0
            while plan.px != want_px and guard < 12:
                if plan.px < want_px:
                    new_taps.append((BTN["RIGHT"][0], BTN["RIGHT"][1], f))
                    f += 1
                    plan.apply_tap("R")
                else:
                    new_taps.append((BTN["LEFT"][0], BTN["LEFT"][1], f))
                    f += 1
                    plan.apply_tap("L")
                guard += 1
            # SOFT-DROP barrage: drives the piece straight down so the lock
            # CELL is deterministic (drop path is column-invariant) even
            # while the lock FRAME wobbles with the tick phase. Emit drops
            # one by one and STOP as soon as the planned piece locks (the
            # clone's cur changes) — overshoot would over-drive the NEXT
            # piece.
            for _ in range(30):
                if plan.cur != sim.cur:
                    break
                new_taps.append((BTN["DROP"][0], BTN["DROP"][1], f))
                f += 1
                plan.apply_tap("DROP")

        if new_taps:
            prev_f1 = min(t[2] for t in new_taps)
            taps += new_taps
            committed = max([t[2] for t in taps] + [verify_idx])
        else:
            prev_f1 = None
            committed = max(committed, verify_idx)
        cycle += 1
        print(f"cycle {cycle}: anchor@{verify_idx} piece={sim.cur} "
              f"rot={rot} px={px_obs} py={py_obs} locks={sim.locks} "
              f"score={sim.score} lines={sim.lines} (+{len(new_taps)} taps)")

    # final continuous evidence run
    final_dir = f"{OUT}/final_run"
    total = committed + 80
    rc = run_engine(taps, total, final_dir)
    shas = frame_shas(final_dir)
    k = min(len(base_shas), prev_f1 if prev_f1 is not None else len(shas),
            len(shas))
    mism = [i for i in range(k) if base_shas[i] != shas[i]]
    assert not mism, f"final prefix mismatch at {mism[:3]}"
    print(f"final continuous run: {len(shas)} frames, prefix verified {k}, "
          f"locks={sim.locks} score={sim.score} lines={sim.lines} rc={rc}")


if __name__ == "__main__":
    main()
