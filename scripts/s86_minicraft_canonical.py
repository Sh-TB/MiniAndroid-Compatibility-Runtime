#!/usr/bin/env python3
"""s86_minicraft_canonical.py — build the MiniCraft (House Builder) canonical GIF
from the S86 build-loop run (terrain -> taps -> DEMO house -> dig) and add the
registry entry + SHA256SUMS row."""
import glob
import hashlib
import json
from PIL import Image

ROOT = "/home/z/my-project"
FRAMES = sorted(glob.glob(f"{ROOT}/run/s86/minicraft/tap/frames/frame_*.png"))
OUT = f"{ROOT}/docs/evidence/canonical/com.miniandroid.minicraft.gif"

TARGET_W = 360
frames = []
for p in FRAMES:
    im = Image.open(p).convert("RGB")
    ratio = TARGET_W / im.width
    im = im.resize((TARGET_W, int(im.height * ratio)), Image.LANCZOS)
    frames.append(im.quantize(colors=256, method=Image.MEDIANCUT))
frames[0].save(
    OUT, save_all=True, append_images=frames[1:], duration=350, loop=0,
    optimize=True)

sha = hashlib.sha256(open(OUT, "rb").read()).hexdigest()
apk_sha = hashlib.sha256(
    open(f"{ROOT}/upload/s86_games/build_minicraft/minicraft_v1.0_vc1.apk",
         "rb").read()).hexdigest()
print("GIF:", OUT, "sha256:", sha, "frames:", len(frames))

reg_path = f"{ROOT}/docs/evidence/canonical/registry.json"
reg = json.load(open(reg_path))
entry = {
    "title": "MiniCraft (House Builder)",
    "package": "com.miniandroid.minicraft",
    "type": "game",
    "status": "VERIFIED-INTERACTIVE",
    "level": 3,
    "level_name": "L3_STRUCT_CANDIDATE",
    "artifact": "docs/evidence/canonical/com.miniandroid.minicraft.gif",
    "artifact_sha256": sha,
    "artifact_kind": ".gif",
    "session": "S86",
    "launched": True,
    "rendered": True,
    "interacted": True,
    "state_changed": True,
    "apk_sha256": apk_sha,
    "version": "1.0",
    "source": "in-house (games/minicraft)",
    "upstream": "in-house (games/minicraft) — companion to Snake Deluxe / "
                "Mini Tetris / 2048 / TicTacToe Deluxe",
    "root_cause": "none — built on the proven in-house pattern (static "
                  "state law + real Canvas.onDraw + button clicks); renders "
                  "first try at current HEAD with the S86 engine laws",
    "notes": "S86 user-requested house-building game. 2D block "
             "sandbox: LCG terrain (grass/dirt/stone), build cursor walked "
             "with the direction pad, BRICK cycles material (brick/plank/"
             "roof/glass/door), PLACE/DIG edit the world, DEMO auto-builds "
             "a brick cottage (gabled roof + timber ring + glass window + "
             "door). Canonical GIF: 16 frames — terrain, 5 real placements, "
             "material cycle, DEMO house build, 2 digs; stats strip "
             "mutates (Blocks/Dug).",
    "proven": "LOADED/LAUNCHED/RENDERED/INTERACTED/STATE_CHANGED/"
              "SCREENSHOT_CAPTURED",
    "remaining": "freeform multi-story building + world save/restore",
    "last_success_stage": "canonical GIF @S86",
    "first_divergence": "none recorded",
}
reg["titles"] = [t for t in reg["titles"]
                 if t.get("package") != "com.miniandroid.minicraft"]
reg["titles"].append(entry)
reg["count"] = len(reg["titles"])
json.dump(reg, open(reg_path, "w"), indent=1)
print("registry entry added, count:", reg["count"])

sums_path = f"{ROOT}/docs/evidence/canonical/SHA256SUMS"
lines = [l.rstrip("\n") for l in open(sums_path)
         if "com.miniandroid.minicraft.gif" not in l]
lines.append(f"{sha}  docs/evidence/canonical/com.miniandroid.minicraft.gif")
open(sums_path, "w").write("\n".join(lines) + "\n")
print("SHA256SUMS updated")
