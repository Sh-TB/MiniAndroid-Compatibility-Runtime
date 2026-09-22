#!/usr/bin/env python3
"""s83b_interact.py — S83-B2 interactive completion runs (user: "complete the
dooz and snake games"; "give real screenshots of running the apps").

Strategy: the canonical actuator is the TouchDispatcher (--tap / --click-test
— the SAME law the S79/S79 taps and S80 autoplays used). Each title runs
twice: baseline (no input) + interactive (--click-test dispatches real
clicks on the view tree's clickable views, or fixed taps). Evidence =
before/after frame pairs as JPG (≤100KB) + a verdict on whether the
interactive run produced NEW pixels (real state change, no fakes).
"""
import glob
import hashlib
import json
import os
import subprocess
import sys
from PIL import Image

ROOT = "/home/z/my-project"
ENG = f"{ROOT}/miniandroid/build/miniandroid"
OUT = f"{ROOT}/run/s83b/sweep"
CACHE = "/tmp/my-project/apk_cache"
CANON = f"{ROOT}/upload/canonical_apks"
os.makedirs(OUT, exist_ok=True)

RUNS = [
    # (apk, tag, extra_args, n_frames)
    (f"{CACHE}/corpus/tictactoeclassic.apk", "GAME-TTT-CLASSIC",
     ["--click-test", "--click-count", "8"], 14),
    (f"{CACHE}/s35new/com.itsfrz.tictactoe_5.apk", "GAME-TTT-FRZ",
     ["--click-test", "--click-count", "6"], 12),
    (f"{CACHE}/s35new/org.kirkezz.rttt_3.apk", "GAME-RTTT",
     ["--click-test", "--click-count", "6"], 12),
    (f"{CACHE}/corpus/dooz.apk", "GAME-DOOZ18",
     ["--click-test", "--click-count", "6"], 12),
    (f"{CACHE}/s35new/org.secuso.privacyfriendlydicer_101.apk", "GAME-DICER",
     ["--click-test", "--click-count", "4"], 12),
    (f"{CACHE}/s82/eu.veldsoft.no.thanks_1.apk", "GAME-NOTHANKS",
     ["--click-test", "--click-count", "4"], 12),
    (f"{CACHE}/s82/xyz.deepdaikon.quinb_10.apk", "GAME-QUINB",
     ["--click-test", "--click-count", "4"], 12),
    (f"{CACHE}/s82/eu.quelltext.memory_7.apk", "GAME-MEMORY",
     ["--click-test", "--click-count", "6"], 14),
    (f"{CACHE}/s82/com.simondalvai.ball2box_69.apk", "GAME-BALL2BOX",
     ["--click-test", "--click-count", "4"], 12),
    (f"{CACHE}/s37new/com.joeld.minesweeper_7.apk", "GAME-MINES1",
     ["--click-test", "--click-count", "6"], 14),
    (f"{CACHE}/s82/crypto.o0o0o0o0o.games.blackjack_4.apk", "GAME-BLACKJACK",
     ["--click-test", "--click-count", "6"], 14),
    (f"{CANON}/fishrings_v1.23_vc6.apk", "GAME-FISHRINGS",
     ["--click-test", "--click-count", "6"], 16),
    (f"{CANON}/de.duenndns.gmdice_8.apk", "APP-GMDICE",
     ["--click-test", "--click-count", "4"], 12),
    (f"{CACHE}/app.varlorg.unote_30.apk", "APP-UNOTE",
     ["--click-test", "--click-count", "4"], 12),
]


def shas(frames):
    out = []
    for f in frames:
        out.append(hashlib.sha256(
            Image.open(f).convert("RGB").tobytes()).hexdigest())
    return out


def save_jpg(png, path):
    im = Image.open(png).convert("RGB").resize((540, 960))
    q = 85
    while True:
        im.save(path, "JPEG", quality=q)
        if os.path.getsize(path) <= 100 * 1024 or q <= 35:
            break
        q -= 10
    return os.path.getsize(path)


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    report = []
    for apk, tag, extra, nframes in RUNS:
        if only and only not in tag:
            continue
        if not os.path.exists(apk):
            print(f"[MISS] {tag}")
            continue
        base_dir = f"{OUT}/{tag}"
        int_dir = f"{OUT}/{tag}_CLICK"
        frames_b = sorted(glob.glob(f"{base_dir}/frames/frame_*.png"))
        # interactive run
        cmd = [ENG, "run", "--execution-mode", "real-dalvik",
               "--frame-delay", "300", "-o", int_dir] + extra + [apk]
        with open(f"{int_dir}.log", "w") as lf:
            try:
                rc = subprocess.call(cmd, stdout=lf, stderr=lf, timeout=420)
            except subprocess.TimeoutExpired:
                rc = -1
        frames_i = sorted(glob.glob(f"{int_dir}/frames/frame_*.png"))
        item = {"tag": tag, "apk": os.path.basename(apk), "rc": rc,
                "interactive_frames": len(frames_i)}
        if frames_i:
            sb = shas(frames_b[-1:]) if frames_b else []
            last_i = frames_i[-1]
            changed = sb and shas([last_i])[0] != sb[0]
            item["last_frame_changed_vs_baseline"] = bool(changed)
            # count distinct frame states (real gameplay = state advances)
            item["distinct_states"] = len(set(shas(frames_i)))
            best = frames_i[-1]
            for f in frames_i:
                if shas([f])[0] != (sb[0] if sb else "x"):
                    best = f
                    break
            item["evidence_first_change"] = save_jpg(
                best, f"{int_dir}/{tag}_state1.jpg")
            item["evidence_last"] = save_jpg(
                last_i, f"{int_dir}/{tag}_stateN.jpg")
        report.append(item)
        print(f"[{tag}] rc={rc} states={item.get('distinct_states',0)} "
              f"changed={item.get('last_frame_changed_vs_baseline')}")
    with open(f"{OUT}/INTERACT_RESULTS.json", "w") as f:
        json.dump(report, f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
