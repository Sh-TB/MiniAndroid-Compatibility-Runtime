#!/usr/bin/env python3
"""s83_ttt_autoplay.py — TicTacToe Deluxe autonomous gameplay driver (S83).

S80 law shape (C1/C3/C4/C7):
  C1: actuator = scheduled taps through the canonical TouchDispatcher.
  C3: vision from RENDERED FRAMES ONLY (X strokes = cyan, O rings = pink,
      win strike = yellow); no game-state peeking.
  C4: the app's own logic stays authoritative (AI replies via its own
      handler schedule; reverse-guard equivalents untouched).
  C7: every leg re-runs the REAL APK from launch; the committed tap prefix
      is replayed and one new tap is appended per leg.
Deliverable: a complete game — X moves, AI replies, win strike, round-over
dialog, NEXT ROUND tap, second round started — every stage frame-captured.
"""
import glob
import os
import subprocess
import sys

from PIL import Image

ROOT = "/home/z/my-project"
ENG = f"{ROOT}/miniandroid/build/miniandroid"
APK = f"{ROOT}/upload/s83_games/build_ttt/tictactoe_deluxe_v1.0_vc1.apk"
OUT = f"{ROOT}/run/s83_ttt_autoplay"

C_X = (56, 189, 248)      # 0xFF38BDF8
C_O = (244, 114, 182)     # 0xFFF472B6
C_WIN = (250, 204, 21)    # 0xFFFACC15
C_CELL = (17, 27, 49)     # 0xFF111B31 button tile / cell tile


def near(p, c, tol=30):
    return all(abs(p[i] - c[i]) <= tol for i in range(3))


def find_button_grid(png):
    """Locate the 3x3 cell-button rows: scan for horizontal bands where the
    button-tile color dominates in 3 clusters (left/center/right)."""
    img = Image.open(png).convert("RGB")
    W, H = img.size
    px = img.load()
    rows = []
    for y in range(0, H, 8):
        hits = sum(1 for x in range(0, W, 12) if near(px[x, y], C_CELL, 12))
        rows.append((y, hits))
    # bands where tile color is strong
    bands = [y for (y, h) in rows if h > 20]
    return bands


def probe_layout():
    """One engine run, no taps — find button-row y centers by vision."""
    os.makedirs(OUT, exist_ok=True)
    rc = run_engine([], 4, f"{OUT}/probe")
    frames = sorted(glob.glob(f"{OUT}/probe/frames/frame_*.png"))
    png = frames[-1]
    img = Image.open(png).convert("RGB")
    W, H = img.size
    px = img.load()
    # find y bands where the cell-tile color dominates
    band_rows = []
    for y in range(0, H, 4):
        hits = sum(1 for x in range(0, W, 10) if near(px[x, y], C_CELL, 14))
        band_rows.append((y, hits))
    tile_bands = [y for (y, h) in band_rows if h > 30]
    print(f"tile-band rows: {tile_bands[:8]}...{tile_bands[-8:] if len(tile_bands)>8 else ''}")
    # cluster contiguous y's into bands
    bands = []
    for y in tile_bands:
        if bands and y - bands[-1][-1] <= 8:
            bands[-1].append(y)
        else:
            bands.append([y])
    centers = [sum(b) // len(b) for b in bands]
    print(f"tile band centers: {centers}")
    # x centers: at the first tile band, scan x for tile-colored runs
    y0 = centers[-1] if centers else H // 2
    xs = [x for x in range(0, W, 6) if near(px[x, y0], C_CELL, 14)]
    xcl = []
    for x in xs:
        if xcl and x - xcl[-1][-1] <= 12:
            xcl[-1].append(x)
        else:
            xcl.append([x])
    xc = [sum(c) // len(c) for c in xcl]
    print(f"x clusters at y={y0}: {xc}")
    return centers, xc


BOARD_REGION = (0, 130, 1080, 820)   # x0,y0,x1,y1 — GameView panel area (S83 canvas law)


def read_board(png, cell_y=None, cell_x=None):
    """Board vision: X/O/win pixel clouds inside the GameView panel region
    (measured 440..930 y-band; button rows start below 955)."""
    img = Image.open(png).convert("RGB")
    W, H = img.size
    px = img.load()
    x0, y0, x1, y1 = BOARD_REGION
    xs_px, o_px, win_px = [], [], []
    for y in range(y0, y1, 2):
        for x in range(x0, x1, 2):
            p = px[x, y]
            if near(p, C_X, 40):
                xs_px.append((x, y))
            elif near(p, C_O, 40):
                o_px.append((x, y))
            elif near(p, C_WIN, 40):
                win_px.append((x, y))
    return xs_px, o_px, win_px, (y1 - y0)


def cluster_to_cells(points, region_h, W):
    """Map pixel clouds to 3x3 grid indices within the fixed board region."""
    if not points:
        return set()
    x0, y0, x1, y1 = BOARD_REGION
    cw = (x1 - x0) / 3.0
    ch = (y1 - y0) / 3.0
    cells = set()
    for (x, y) in points:
        c = min(2, max(0, int((x - x0) / cw)))
        r = min(2, max(0, int((y - y0) / ch)))
        cells.add(r * 3 + c)
    return cells


def run_engine(taps, n_frames, out_dir, frame_delay=420):
    os.makedirs(out_dir, exist_ok=True)
    cmd = [ENG, "run", "--execution-mode", "real-dalvik",
           "--frames", str(n_frames), "--frame-delay", str(frame_delay),
           "-o", out_dir]
    for (x, y, k) in taps:
        cmd += ["--tap", f"{x},{y}@{k}"]
    cmd += [APK]
    with open(f"{out_dir}.log", "w") as log:
        rc = subprocess.call(cmd, stdout=log, stderr=log, timeout=900)
    return rc


def main():
    centers, xc = probe_layout()
    # S83 CALIBRATED GEOMETRY (measured from rendered frames):
    # button x centers [205,540,875] (tile runs split by the digit glyph,
    # pair-merged), button row y centers [1070,1328,1586].
    cell_y = [1070, 1328, 1586]
    cell_x = [205, 540, 875]
    print(f"cell buttons (calibrated): y={cell_y} x={cell_x}")

    # Leg plan: play X: c5(center) then block/win per AI reply; then
    # corners.  Committed prefix + one new tap per leg (C7).
    cell_map = {1: (0, 0), 2: (1, 0), 3: (2, 0),
                4: (0, 1), 5: (1, 1), 6: (2, 1),
                7: (0, 2), 8: (1, 2), 9: (2, 2)}

    def tap_for(cell, k):
        col, row = cell_map[cell]
        return (cell_x[col], cell_y[row], k)

    legs = []          # committed taps
    stage_frames = {}  # stage name -> (leg_dir, last_frame)
    stage = 0
    x_cells = set()
    o_cells = set()
    preferred = [5, 1, 9, 3, 7, 2, 4, 6, 8]

    for leg in range(9):
        leg_dir = f"{OUT}/leg{leg:02d}"
        taps = list(legs)
        # pick next X cell not taken (vision)
        obs_dir = leg_dir
        last_frame_idx = 6 + leg * 2
        new_tap = None
        if leg == 0:
            new_tap = tap_for(5, 4)   # X opens center
        else:
            new_tap = None
        rc = run_engine(taps, 4, leg_dir) if new_tap is None else None

        if leg == 0:
            rc = run_engine([tap_for(5, 4)], 8, leg_dir)
            stage_frames["x1_center"] = f"{leg_dir}/frames"
        elif leg >= 1:
            # vision from previous leg's final frame
            prev = f"{OUT}/leg{leg-1:02d}"
            frames = sorted(glob.glob(f"{prev}/frames/frame_*.png"))
            if not frames:
                print("NO FRAMES in", prev)
                break
            xs_px, o_px, win_px, reg_h = read_board(frames[-1], cell_y, cell_x)
            x_cells = cluster_to_cells(xs_px, reg_h, 1080)
            o_cells = cluster_to_cells(o_px, reg_h, 1080)
            if win_px:
                print(f"WIN STRIKE VISIBLE at leg {leg}")
                stage_frames["win_strike"] = f"{prev}/frames"
                break
            # vision indices are 0-based grid cells; buttons are 1-based
            x_btn = {i + 1 for i in x_cells}
            o_btn = {i + 1 for i in o_cells}
            free = [c for c in preferred
                    if c not in x_btn and c not in o_btn]
            if not free:
                print("board full — draw?")
                break
            nxt = free[0]
            taps.append(tap_for(nxt, 4 + leg * 2))
            rc = run_engine(taps, 8 + leg * 2, leg_dir)
            stage_frames[f"x{leg+1}_{nxt}"] = f"{leg_dir}/frames"
            legs = taps
        if rc != 0:
            print(f"leg {leg} rc={rc}")
        print(f"leg {leg}: X={sorted(x_cells)} O={sorted(o_cells)}")

    # final leg: tap NEXT ROUND on the dialog, capture round 2
    final_dir = f"{OUT}/final"
    # dialog positive button: measured (540,1035) from the rendered dialog
    taps = list(legs)
    taps.append((540, 1035, 4 + len(legs) * 2 + 2))
    rc = run_engine(taps, 8 + len(legs) * 2 + 4, final_dir)
    stage_frames["next_round"] = f"{final_dir}/frames"

    print("\n== STAGE FRAMES ==")
    for k, v in stage_frames.items():
        fs = sorted(glob.glob(f"{v}/frame_*.png"))
        print(k, "->", fs[-1] if fs else "NONE")


if __name__ == "__main__":
    main()
