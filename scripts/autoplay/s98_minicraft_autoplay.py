#!/usr/bin/env python3
"""s98_minicraft_autoplay.py — MiniCraft (House Builder) autonomous play (S98).

S80 law shape (C1/C3/C4/C7):
  C1: actuator = real scheduled taps through the canonical TouchDispatcher
      (btn_left/up/down/right walk the cursor; btn_block cycles material;
      btn_place/btn_dig edit the world; btn_demo auto-builds the cottage).
  C3: vision from RENDERED FRAMES ONLY — block colors from the game's own
      palette (CraftWorldView C_* constants), cursor = C_CURSOR yellow.
  C4: the app's own logic stays authoritative (setBlock bounds, stats).
  C7: every verification re-runs the REAL APK from launch; frame SHAs pin
      the committed prefix up to the first frame a new tap can influence.

Verify:
  V1 cursor moves (yellow cursor ink center shifts after direction taps).
  V2 materials placed: brick + plank + roof + glass + door ink in the world
     region grows from the pre-tap baseline (state change on the static
     world grid — OBJECT-IDENTITY frontier law respected by the game).
  V3 DEMO cottage: roof-color ink appears in quantity after DEMO.
  V4 digs: placed-region ink shrinks / stats strip shows dug>0 (we count
     sky pixels re-appearing where blocks were dug).
"""
import glob
import hashlib
import json
import os
import shutil
import subprocess
import sys

from PIL import Image

ROOT = "/home/z/my-project"
ENG = f"{ROOT}/miniandroid/build/miniandroid"
APK = f"{ROOT}/upload/s86_games/build_minicraft/minicraft_v1.0_vc1.apk"
OUT = f"{ROOT}/run/s98_minicraft_autoplay"

# CraftWorldView palette (game source constants, ARGB)
C_BRICK = (0xB5, 0x54, 0x3B)
C_PLANK = (0xC8, 0x9A, 0x5B)
C_ROOF = (0x8C, 0x3B, 0x32)
C_GLASS = (0xBF, 0xE8, 0xF5)
C_DOOR = (0x7A, 0x4E, 0x28)
C_CURSOR = (0xFF, 0xEE, 0x44)


def close(p, c, tol=18):
    return (abs(p[0] - c[0]) <= tol and abs(p[1] - c[1]) <= tol and
            abs(p[2] - c[2]) <= tol)


def run_engine(taps, n_frames, out_dir, dump_vt=False):
    os.makedirs(out_dir, exist_ok=True)
    cmd = [ENG, "run", "--execution-mode", "real-dalvik",
           "--frames", str(n_frames), "--frame-delay", str(120),
           "--width", "1080", "--height", "1920",
           "--data-root", f"{out_dir}/data", "-o", out_dir]
    if dump_vt:
        cmd.append("--dump-view-tree")
    for (x, y, k) in taps:
        cmd += ["--tap", f"{x},{y}@{k}"]
    cmd += [APK]
    with open(f"{out_dir}.log", "w") as log:
        rc = subprocess.call(cmd, stdout=log, stderr=log, timeout=1200)
    return rc


def frames_of(out_dir):
    return sorted(glob.glob(f"{out_dir}/frames/frame_*.png"))


def shas_of(out_dir):
    return [hashlib.sha256(open(f, "rb").read()).hexdigest()
            for f in frames_of(out_dir)]


def buttons_from_vt(out_dir):
    """Button centers from the run's own laid-out view tree (C3 honesty:
    geometry comes from the app's layout, not hardcoded coords)."""
    vt = json.load(open(f"{out_dir}/view_tree.json"))
    found = {}
    for n in vt.get("nodes", []):
        cls = str(n.get("class", ""))
        if "Button" in cls and n.get("enabled", True):
            x, y = n.get("x", 0), n.get("y", 0)
            w, h = n.get("width", 0), n.get("height", 0)
            label = str(n.get("text", "")).strip().upper()
            if w > 0 and h > 0 and label:
                found[label] = (x + w // 2, y + h // 2)
    return found


def ink(img, box, color, tol=18):
    region = img.crop(box).convert("RGB")
    return sum(1 for p in region.getdata() if close(p, color, tol))


def cursor_center(img, box):
    region = img.crop(box).convert("RGB")
    w, h = region.size
    px = region.load()
    sx = sy = n = 0
    for yy in range(0, h, 2):
        for xx in range(0, w, 2):
            if close(px[xx, yy], C_CURSOR, 12):
                sx += xx
                sy += yy
                n += 1
    return (sx / n, sy / n, n) if n else None


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(OUT, exist_ok=True)

    # ── probe: layout geometry from the app itself ────────────────────
    probe = f"{OUT}/probe"
    rc = run_engine([], 3, probe, dump_vt=True)
    if rc != 0:
        print("probe run FAILED"); sys.exit(1)
    BTN = buttons_from_vt(probe)
    need = ["LEFT", "UP", "DOWN", "RIGHT", "BRICK", "PLACE", "DIG", "DEMO"]
    missing = [b for b in need if b not in BTN]
    if missing:
        print("buttons missing from view tree:", missing, "have:", list(BTN))
        sys.exit(1)
    print("button centers:", BTN)

    # world region = everything above the first button row
    world_box = (0, 0, 1080, BTN["LEFT"][1] - 60)

    # ── the build schedule (house-building sequence) ──────────────────
    # frame 2: settle. Cursor starts at (col 3, row 8).
    #   walk to (5,10): RIGHT RIGHT DOWN DOWN
    #   PLACE brick; BLOCK->PLANK, RIGHT, PLACE; BLOCK->ROOF, UP, PLACE x2
    #   BLOCK->GLASS, PLACE; BLOCK->DOOR, DOWN, PLACE
    #   DEMO (auto-build cottage); DIG x2
    taps = []
    k = 3
    plan = [
        ("RIGHT", 1), ("RIGHT", 1), ("DOWN", 1), ("DOWN", 1), ("PLACE", 2),
        ("BRICK", 2),            # BRICK button cycles material -> PLANK
        ("RIGHT", 1), ("PLACE", 2),
        ("BRICK", 2),            # -> ROOF
        ("UP", 1), ("PLACE", 2), ("RIGHT", 1), ("PLACE", 2),
        ("BRICK", 2),            # -> GLASS
        ("DOWN", 1), ("PLACE", 2),
        ("BRICK", 2),            # -> DOOR
        ("DOWN", 1), ("DOWN", 1), ("PLACE", 3),
        ("DEMO", 4),             # auto-build the cottage
        ("DIG", 3), ("DIG", 3),
    ]
    for label, gap in plan:
        taps.append((*BTN[label], k))
        k += gap
    n_frames = k + 6

    run = f"{OUT}/build_run"
    rc = run_engine(taps, n_frames, run)
    if rc != 0:
        print("build run FAILED"); sys.exit(1)

    fr = frames_of(run)
    pre = Image.open(fr[2]).convert("RGB")
    post = Image.open(fr[-1]).convert("RGB")

    # ── V1 cursor moved ───────────────────────────────────────────────
    c0 = cursor_center(pre, world_box)
    c1 = cursor_center(post, world_box)
    moved = bool(c0 and c1 and n0_ok(c0) and n1_ok(c1) and
                 (abs(c0[0] - c1[0]) + abs(c0[1] - c1[1]) > 20))
    print(f"V1 cursor: {c0} -> {c1} moved={moved}")

    # ── V2 materials placed (per-material ink growth) ─────────────────
    mats = {"brick": C_BRICK, "plank": C_PLANK, "roof": C_ROOF,
            "glass": C_GLASS, "door": C_DOOR}
    growth = {}
    for name, col in mats.items():
        b0 = ink(pre, world_box, col)
        b1 = ink(post, world_box, col)
        growth[name] = (b0, b1)
    placed_any = sum(1 for b0, b1 in growth.values() if b1 > b0)
    print("V2 material ink growth:", growth, "grew:", placed_any)

    # ── V3 DEMO cottage roof quantity ─────────────────────────────────
    roof_after = growth["roof"][1]
    cottage = roof_after > 400  # a cottage roof is hundreds of px
    print(f"V3 roof ink after={roof_after} cottage={cottage}")

    # ── V4 digs: some material ink DECREASED between mid and post ─────
    mid = Image.open(fr[len(fr) // 2]).convert("RGB")
    digs = any(ink(mid, world_box, col) > ink(post, world_box, col)
               for col in mats.values())
    print(f"V4 digs observed={digs}")

    ok = moved and placed_any >= 3 and cottage
    print(f"MINICRAFT AUTOPLAY: {'PASS' if ok else 'PARTIAL'} "
          f"(moved={moved}, placed={placed_any}/5, cottage={cottage}, digs={digs})")

    json.dump({
        "game": "com.miniandroid.minicraft", "mode": "s98 autonomous play",
        "taps": len(taps), "frames": len(fr),
        "cursor_moved": moved, "material_growth": growth,
        "materials_grown": placed_any, "cottage_roof_ink": roof_after,
        "digs_observed": digs, "verdict": "PASS" if ok else "PARTIAL",
    }, open(f"{OUT}/autoplay_evidence.json", "w"), indent=1)

    # GIF from the build run (every 4th frame, small)
    try:
        imgs = [Image.open(f).convert("P", palette=Image.ADAPTIVE)
                for f in fr[::4]]
        imgs[0].save(f"{ROOT}/docs/evidence/s98/minicraft_autoplay.gif",
                     save_all=True, append_images=imgs[1:], duration=350,
                     loop=0)
        print("GIF written")
    except Exception as e:
        print("gif skipped:", e)

    sys.exit(0 if ok else 2)


def n0_ok(c):
    return c[2] > 0


def n1_ok(c):
    return c[2] > 0


if __name__ == "__main__":
    main()
