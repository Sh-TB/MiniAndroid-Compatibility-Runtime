#!/usr/bin/env python3
"""s79_snake_gif.py — S79: Snake gameplay GIF built from REAL APK frames.

User directive: "یک گیف از گیم پلی اسنک برای من ... ببینم تونستی بازی بکنی"
(make a GIF of Snake gameplay so the user can see the game was played).

Chain compliance (S78 §0): every frame is rendered by the real engine
(real-dalvik) executing the real APK; the ONLY actuator is scheduled taps
through the canonical TouchDispatcher DOWN/UP law (S73 controller C1);
vision comes from rendered frames only (C3); the app's own game logic
stays authoritative (C4).

Pipeline (reuses the proven S76 dialog-restart law):
  1. recover the committed 23-tap autonomous schedule (S73 evidence run_01)
  2. + S73 C4B death extension D@90 L@91 U@92 (self-collision game over)
  3. run A: observe Game-Over dialog frame geometry ([DIALOG-LAYOUT]) and
     compute the positive button center by the DialogShadow painter law
  4. run B: same schedule + tap(positive)@99 -> dialog dismiss + RESTART
     + second life
  5. assemble a GIF from run B frames (evidence frames untouched; GIF is
     a downscaled derived artifact) with per-segment durations
"""
import glob
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s73_snake_controller import analyze_run, count_events, run_engine
from PIL import Image

ROOT = "/home/z/my-project"
TRACE = f"{ROOT}/docs/evidence/s73_snake_autoplay/run_01/gameplay_trace.json"
OUT = f"{ROOT}/run/s79_snake_gif"
DL = f"{ROOT}/download/s79"
os.makedirs(OUT, exist_ok=True)
os.makedirs(DL, exist_ok=True)
GIF_ONLY = os.environ.get("S79_GIF_ONLY") == "1"

# ---- 1. recover the committed autonomous schedule -----------------------
taps = []
for line in open(TRACE, encoding="utf-8", errors="replace"):
    m = re.search(r"tap\((\d+),(\d+)\)@frame(\d+)", line)
    if m:
        taps.append((int(m.group(1)), int(m.group(2)), int(m.group(3))))
assert len(taps) == 23, f"expected 23 scheduled taps, got {len(taps)}"

# ---- 2. death extension (S73 C4B, verbatim) -----------------------------
from s73_snake_controller import BTN
taps += [(BTN["BOTTOM"][0], BTN["BOTTOM"][1], 90),   # D
         (BTN["LEFT"][0], BTN["LEFT"][1], 91),       # L
         (BTN["TOP"][0], BTN["TOP"][1], 92)]         # U into body

# ---- 3. run A: dialog geometry ------------------------------------------
rc_a = None
if GIF_ONLY:
    _rep = json.load(open(f"{OUT}/s79_gif_report.json"))
    layout = _rep["run_a"]["dialog_layout"]
    pos_x, pos_y = _rep["run_a"]["positive_btn_center"]
    cjk_px = _rep["run_a"]["cjk_positive_label_blue_px"]
else:
    out_a = f"{OUT}/run_a_dialog"
    rc_a = run_engine(taps, 108, out_a)
    layout = None
    for line in open(f"{out_a}/engine.log", encoding="utf-8", errors="replace"):
        m = re.search(r"\[DIALOG-LAYOUT\] frame=\((-?\d+),(-?\d+) (\d+)x(\d+)\)", line)
        if m:
            layout = dict(l=int(m.group(1)), t=int(m.group(2)),
                          w=int(m.group(3)), h=int(m.group(4)))
    assert layout, "no DIALOG-LAYOUT in run A engine.log"
    PAD, ROW = 24, 112
    l, t, w, h = layout["l"], layout["t"], layout["w"], layout["h"]
    b = t + h
    seg_w = (w - 2 * PAD) // 2                       # 2 buttons: neg + pos
    pos_x = l + PAD + seg_w + seg_w // 2
    pos_y = b - ROW + 62
    print(f"run A rc={rc_a} dialog=({l},{t} {w}x{h}) positive=({pos_x},{pos_y})")

    # CJK positive-label pixel check on the dialog frame (R-NEW-398 law color)
    cjk_px = 0
    _aframes = sorted(glob.glob(f"{out_a}/frames/frame_*.png"),
                      key=lambda p: int(re.search(r"frame_(\d+)\.png", p).group(1)))
    dimg = Image.open(_aframes[94]).convert("RGB")
    for yy in range(max(0, pos_y - 14), min(dimg.height, pos_y + 14)):
        for xx in range(max(0, pos_x - seg_w // 2), min(dimg.width, pos_x + seg_w // 2)):
            r, g, bb = dimg.getpixel((xx, yy))
            if abs(r) < 40 and abs(g - 0x62) < 40 and abs(bb - 0xCC) < 40:
                cjk_px += 1
    print(f"run A: 重新开始 blue px in positive region = {cjk_px}")

# ---- 4. run B: gameplay -> death -> dialog -> restart -> 2nd GAME -------
SHIFT = 98
taps_b = taps + [(pos_x, pos_y, 99)] + [(x, y, k + SHIFT) for (x, y, k) in taps]
out_b = f"{OUT}/run_b_restart"
if GIF_ONLY:
    _rep = json.load(open(f"{OUT}/s79_gif_report.json"))
    rc_b = _rep["run_b"]["rc"]
    obs = analyze_run(out_b)
    ev_full = _rep["run_b"]["total_events"]
    over_idx = _rep["run_b"]["first_game_over_frame"]
    restart_idx = _rep["run_b"]["restart_frame"]
    over2_idx = _rep["run_b"].get("second_game_over_frame")
    second_life_events = _rep["run_b"]["second_life_events"]
    ev_first = _rep["run_b"]["first_life_events"]
else:
    rc_b = run_engine(taps_b, 220, out_b)
    obs = analyze_run(out_b)
    ev_full = count_events(obs)
    over_idx = next((o["frame_index"] for o in obs if o["game_over"]), None)
    restart_idx = None
    if over_idx is not None:
        frozen = obs[over_idx]["snake"]
        for o in obs[over_idx + 1:]:
            if o["snake"] and frozen is not None and o["snake"] != frozen:
                restart_idx = o["frame_index"]
                break
    # second life = from restart to the end of the run
    second_life_events = count_events(obs[restart_idx:]) if restart_idx else {}
    # a second death (replayed schedule ends in the same self-collision) is a
    # VALID observation — find it so the GIF segments stay sane
    over2_idx = None
    if restart_idx is not None:
        over2_idx = next((o["frame_index"] for o in obs[restart_idx:]
                          if o["game_over"] and o["frame_index"] > restart_idx), None)
    # first-life captures (before the scheduled death)
    ev_first = count_events(obs[:90])
    print(f"run B rc={rc_b} frames={len(obs)} over@{over_idx} restart@{restart_idx} over2@{over2_idx}")
    print(f"second life events: {second_life_events}")

report = {
    "apk": "snake_v1.0_vc1.apk",
    "engine_mode": "real-dalvik",
    "actuator": "TouchDispatcher taps only (C1)",
    "schedule": {"autonomous_taps": 23, "death_extension": ["D@90", "L@91", "U@92"],
                 "restart_tap": f"({pos_x},{pos_y})@99"},
    "run_a": {"rc": rc_a, "dialog_layout": layout,
              "positive_btn_center": [pos_x, pos_y],
              "cjk_positive_label_blue_px": cjk_px},
    "run_b": {"rc": rc_b, "frames": len(obs),
              "first_game_over_frame": over_idx,
              "restart_frame": restart_idx,
              "first_life_events": ev_first,
              "second_life_events": second_life_events,
              "second_game_over_frame": over2_idx,
              "total_events": ev_full},
    "verdict": {
        "gameplay_played": ev_first["moves"] > 0 and ev_first["captures"] >= 1,
        "game_over_observed": over_idx is not None,
        "cjk_dialog_painted": cjk_px > 20,
        "restart_observed": restart_idx is not None,
    },
}
with open(f"{OUT}/s79_gif_report.json", "w") as f:
    json.dump(report, f, indent=1)
print(json.dumps(report["verdict"], indent=1))

# ---- 5. GIF assembly (derived, downscaled, captioned) ------------------
GIF_W, GIF_H = 480, 854
frames_dir = f"{out_b}/frames"
pngs = sorted(glob.glob(f"{frames_dir}/frame_*.png"),
              key=lambda p: int(re.search(r"frame_(\d+)\.png", p).group(1)))
assert pngs, "no frames rendered in run B"


def seg_indices(start, end, step, cap=None):
    idx = list(range(start, end + 1, step))
    if cap and len(idx) > cap:                     # sample evenly
        idx = [idx[int(round(i * (len(idx) - 1) / (cap - 1)))]
               for i in range(cap)]
    return idx


play_end2 = (over2_idx if over2_idx is not None else len(obs) - 1) - 2
seq = []            # (frame_index, duration_ms, caption)
S1 = seg_indices(0, max(0, (over_idx or 92) - 2), 3)
S2 = list(range(max(0, (over_idx or 92) - 1),
                min(len(obs) - 1, (over_idx or 92) + 5) + 1))
S3 = seg_indices((over_idx or 92) + 6, max((over_idx or 92) + 6,
                 (restart_idx or len(obs)) - 1), 1, cap=3)
S4 = seg_indices(min(len(obs) - 1, max((restart_idx or 100) + 1, 0)),
                 max(play_end2, (restart_idx or 100)), 3, cap=40)
for i in S1:
    seq.append((i, 190, "GAME 1 - autonomous taps (real APK)"))
for i in S2:
    seq.append((i, 420, "GAME OVER + dialog (CJK labels R-NEW-398)"))
for i in S3:
    seq.append((i, 420, "tap (restart btn) -> dialog dismiss"))
for i in S4:
    seq.append((i, 190, "GAME 2 - after real restart tap"))
print(f"GIF segments: S1={len(S1)} S2={len(S2)} S3={len(S3)} S4={len(S4)} "
      f"total={len(seq)}")

from PIL import ImageDraw, ImageFont
try:
    _f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 17)
except Exception:
    _f = ImageFont.load_default()

gif_path = f"{DL}/snake_gameplay.gif"
pal_imgs = []
for (i, dur, cap) in seq:
    im = Image.open(pngs[i]).convert("RGB").resize((GIF_W, GIF_H), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, GIF_W, 30], fill=(16, 16, 24))
    d.text((8, 6), cap, fill=(240, 240, 240), font=_f)
    pal_imgs.append((im.quantize(colors=256, method=Image.MEDIANCUT,
                                 dither=Image.NONE), dur))
pal_imgs[0][0].save(
    gif_path, save_all=True, append_images=[x[0] for x in pal_imgs[1:]],
    duration=[x[1] for x in pal_imgs], loop=0, optimize=True)
print(f"GIF written: {gif_path} ({os.path.getsize(gif_path)/1e6:.2f} MB, "
      f"{len(seq)} frames)")
report["gif"] = {"path": gif_path, "frames": len(seq),
                 "segments": {"S1_game1": len(S1), "S2_dialog": len(S2),
                              "S3_restart": len(S3), "S4_game2": len(S4)}}
with open(f"{OUT}/s79_gif_report.json", "w") as f:
    json.dump(report, f, indent=1)
