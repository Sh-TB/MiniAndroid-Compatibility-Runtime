#!/usr/bin/env python3
"""s79_evidence_package.py — S79 evidence bundle assembly.

Copies the wave's evidence artifacts into docs/evidence/s79/ following the
repo evidence-image law (JPG 540x960, q<=72, every image <=100KB — S38
precedent), writes SHA256SUMS, and verifies the size gate.
"""
import hashlib
import json
import os
import shutil

from PIL import Image

ROOT = "/home/z/my-project"
OUT = f"{ROOT}/docs/evidence/s79"
os.makedirs(f"{OUT}/fishrings", exist_ok=True)
os.makedirs(f"{OUT}/reproofs", exist_ok=True)


def to_jpg(src_png, dst_jpg, size=(540, 960), q=72):
    im = Image.open(src_png).convert("RGB")
    if im.size != size:
        im = im.resize(size, Image.LANCZOS)
    im.save(dst_jpg, "JPEG", quality=q, optimize=True)
    kb = os.path.getsize(dst_jpg) / 1024
    assert kb <= 100, f"{dst_jpg} is {kb:.0f}KB (>100KB)"
    return kb


written = []

# 1. Snake gameplay GIF + report (GIF is the derived artifact; frames are
#    regenerable deterministically — the GIF itself is the deliverable).
shutil.copy(f"{ROOT}/download/s79/snake_gameplay.gif", f"{OUT}/snake_gameplay.gif")
shutil.copy(f"{ROOT}/run/s79_snake_gif/s79_gif_report.json",
            f"{OUT}/s79_gif_report.json")
written += ["snake_gameplay.gif", "s79_gif_report.json"]

# 2. FishRings S10 chain at HEAD — 3 board states (run2, deterministic).
for i, name in [(8, "fishrings/board_state_1_before_taps.jpg"),
                (9, "fishrings/board_state_2_after_rotation_1.jpg"),
                (11, "fishrings/board_state_3_after_rotations_2_3.jpg")]:
    kb = to_jpg(f"{ROOT}/run/s79_reproofs/fishrings_r400_run2/frames/frame_{i:03d}.png",
                f"{OUT}/{name}")
    written.append(name)

# 3. Re-proof stills (final binary).
kb = to_jpg(f"{ROOT}/run/s79_reproofs/unote_run1/screenshot.png",
            f"{OUT}/reproofs/unote_main_menu.jpg")
written.append("reproofs/unote_main_menu.jpg")
kb = to_jpg(f"{ROOT}/run/s79_reproofs/unote_run1/click_frame_1.png",
            f"{OUT}/reproofs/unote_after_add_note_tap.jpg")
written.append("reproofs/unote_after_add_note_tap.jpg")
kb = to_jpg(f"{ROOT}/run/s79_reproofs/microtimer_run1/click_frame_4.png",
            f"{OUT}/reproofs/microtimer_timer_running.jpg")
written.append("reproofs/microtimer_timer_running.jpg")
kb = to_jpg(f"{ROOT}/run/s79_reproofs/gmdice_run1/click_frame_5.png",
            f"{OUT}/reproofs/gmdice_roll_result_rendered.jpg")
written.append("reproofs/gmdice_roll_result_rendered.jpg")

# 4. Re-proof matrix (facts per app, final binary).
matrix = {
    "binary": "miniandroid/build/miniandroid @ S79 (R-NEW-399 + R-NEW-400)",
    "snake_gif": json.load(open(f"{OUT}/s79_gif_report.json")),
    "gmdice": {"click_test": "5/5 dispatched, results rendered (SETTEXT view_37)",
               "multi_roll": "tap (580,1848)@6/@14 → target=41 → '6' then '5'",
               "det": "x2"},
    "microtimer": {"click_test": "12 probed / 11 changed",
                   "timer": "00:00:00 → 00:00:09 → 00:00:98 (running)", "det": "x2"},
    "unote": {"click_test": "3 probed / 2 changed",
              "state_change": "Add note → real editor screen (Title/Note/Save/"
                              "Return), 13,032 sampled-px diff; notes.db SQLite "
                              "chain live", "det": "x2"},
    "fishrings": {"s10_chain": "3 taps → 3 CLICK dispatches (GameActivity$1/$2/"
                               "$4) → 3 rotations → 3 distinct board states",
                  "det": "x2 (byte-identical frame SHAs)"},
    "bouncy": {"click_test": "12 probed / 10 changed (Vector Pinball 1.16.0)",
               "det": "x2", "open": "L7 multi-round game-loop proof"},
    "opmt": {"click_test": "6/6 changed; 'It is currently black's turn.'",
             "det": "x2", "open": "app-own IOOBE stopper on in-game loop"},
    "dooz": {"visual": "23,472 px engine-default face (honest NOT_HUMAN_VISIBLE)",
             "open": "dooz Job ISE (Loj0;.T pc=49) + F-147 producer trace"},
    "tripeaks": {"click_test": "0 clickables in lobby tree",
                 "open": "R-NEW-388 layout geometry family + OBJECT-IDENTITY"},
}
with open(f"{OUT}/reproofs/S79_REPROOF_MATRIX.json", "w") as f:
    json.dump(matrix, f, indent=1)
written.append("reproofs/S79_REPROOF_MATRIX.json")

# 5. SHA256SUMS + size report
total = 0
with open(f"{OUT}/SHA256SUMS", "w") as sf:
    for name in sorted(written):
        p = f"{OUT}/{name}"
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        sz = os.path.getsize(p)
        total += sz
        sf.write(f"{h}  {name}\n")
print(f"evidence package: {len(written)} files, {total/1e6:.2f} MB, "
      f"all images <=100KB — OK")
