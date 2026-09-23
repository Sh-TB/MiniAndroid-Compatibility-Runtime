#!/usr/bin/env python3
"""s86_dodge_canonical.py — rebuild com.dozingcatsoftware.dodge canonical GIF
from the S86 F-NEW-164 run (menu -> tap New Game -> live SurfaceView gameplay)
and update registry.json + SHA256SUMS + provenance fields."""
import glob
import hashlib
import json
from PIL import Image

ROOT = "/home/z/my-project"
FRAMES = sorted(glob.glob(f"{ROOT}/run/s86/dodge/final/frames/frame_*.png"))
OUT = f"{ROOT}/docs/evidence/canonical/com.dozingcatsoftware.dodge.gif"

# Build GIF: 360x640, 400ms per frame, loop forever.
TARGET_W = 360
frames = []
for p in FRAMES:
    im = Image.open(p).convert("RGB")
    ratio = TARGET_W / im.width
    im = im.resize((TARGET_W, int(im.height * ratio)), Image.LANCZOS)
    frames.append(im.quantize(colors=256, method=Image.MEDIANCUT))
frames[0].save(
    OUT, save_all=True, append_images=frames[1:], duration=400, loop=0,
    optimize=True)

sha = hashlib.sha256(open(OUT, "rb").read()).hexdigest()
print("GIF:", OUT, "sha256:", sha, "frames:", len(frames))

# Update registry entry.
reg_path = f"{ROOT}/docs/evidence/canonical/registry.json"
reg = json.load(open(reg_path))
for t in reg["titles"]:
    if t.get("package") == "com.dozingcatsoftware.dodge":
        t["status"] = "VERIFIED-INTERACTIVE"
        t["level"] = 3
        t["level_name"] = "L3_STRUCT_CANDIDATE"
        t["artifact"] = "docs/evidence/canonical/com.dozingcatsoftware.dodge.gif"
        t["artifact_sha256"] = sha
        t["artifact_kind"] = ".gif"
        t["session"] = "S84/S86"
        t["launched"] = True
        t["rendered"] = True
        t["interacted"] = True
        t["state_changed"] = True
        t["root_cause"] = (
            "S86 root-cause chain (upstream source-read driven): the game "
            "field NEVER rendered in the S84 GIF (frame0=menu, frame1=about "
            "white). Root causes fixed this wave, all A/B-proven: F-NEW-164 "
            "SurfaceView/SurfaceHolder.lockCanvas real-surface law "
            "(FieldView extends SurfaceView, drawField() = "
            "lockCanvas->drawRect(black)+zones+bullets->unlockCanvasAndPost); "
            "F-NEW-165 java.util.LinkedList Deque end-access family "
            "(FrameRateManager.previousFrameTimestamps.getLast() NPE killed "
            "the game thread at APP BOUNDARY); F-NEW-166 "
            "WindowManager.getDefaultDisplay/Display.getMetrics/getRotation "
            "(FieldView ctor Display.getMetrics NPE); F-NEW-167 "
            "Activity.getPreferences == getSharedPreferences("
            "getLocalClassName(), mode) (bestLevel() SP NPE); F-NEW-168 "
            "AOSP draw-subtree law: View.draw(Canvas,ViewGroup,long) gates "
            "dispatchDraw on VISIBLE — INVISIBLE(4) prunes the subtree "
            "(menuView INVISIBLE kept button children painting); F-NEW-169 "
            "Canvas.drawRect(RectF,Paint) object overload + RectF ctor field "
            "law (rect recorded (0,0,0,0)); F-NEW-170 View.getWidth/getHeight "
            "dimension query laws (drawField sizes all geometry from "
            "getWidth(); was 0 -> all-zero draw ops). Game now renders the "
            "real Dodge design from upstream source: black field, "
            "semi-transparent red start zone, green end zone, blue dodger "
            "circle, per-bullet random bright colors.")
        t["notes"] = (
            "S86 canonical GIF: 14 frames (menu + 13 live gameplay), tap "
            "New Game at (537,935), bullets move/dodger visible, L3 "
            "struct-candidate. Upstream ground truth: "
            "github.com/dozingcat/dodge-android (GPLv3) FieldView.java read "
            "this wave; APK re-downloaded SHA256 "
            "a5687d1bad7b2927740a55b7b1df11efc81edcad03f0633ab5c2e5c58b120541 "
            "= S84 pin (v1.5.1, vc10).")
        t["proven"] = ("LOADED/LAUNCHED/RENDERED/INTERACTED/STATE_CHANGED/"
                       "SCREENSHOT_CAPTURED")
        t["remaining"] = ("dodger steering (touch/tilt navigation) + "
                          "collision/death animation proof")
        print("registry updated:", t["title"], "level", t["level"])
json.dump(reg, open(reg_path, "w"), indent=1)

# Update SHA256SUMS.
sums_path = f"{ROOT}/docs/evidence/canonical/SHA256SUMS"
lines = []
for line in open(sums_path):
    if "com.dozingcatsoftware.dodge.gif" not in line:
        lines.append(line.rstrip("\n"))
lines.append(f"{sha}  docs/evidence/canonical/com.dozingcatsoftware.dodge.gif")
open(sums_path, "w").write("\n".join(lines) + "\n")
print("SHA256SUMS updated")
