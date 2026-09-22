#!/usr/bin/env python3
"""s83b_sweep.py — S83-B2 graphics sweep: 20 games + 10 apps + 2 high-level.

User directive (2026-09-22): run 10 apps and 20 simple games with the new
graphics base, capture REAL screenshots (no placeholders), classify honestly
via the S81 visual audit (L0-L5), and emit the progress table. Two random
high-level titles (P9 libGDX, TimeLimit) run as stretch gates.

Output: run/s83b/sweep/SWEEP_RESULTS.json + JPG screenshots ≤100KB.
"""
import glob
import hashlib
import json
import os
import subprocess
import sys
from PIL import Image

ROOT = "/home/z/my-project"
sys.path.insert(0, f"{ROOT}/scripts")
from s81_visual_audit import audit_frame, level_of  # noqa: E402

ENG = f"{ROOT}/miniandroid/build/miniandroid"
OUT = f"{ROOT}/run/s83b/sweep"
CACHE = "/tmp/my-project/apk_cache"
CANON = f"{ROOT}/upload/canonical_apks"
GAMES = f"{ROOT}/upload/s80_games"
S72 = f"{ROOT}/upload/s72_w4_apks"
os.makedirs(OUT, exist_ok=True)

GAME_BATCH = [
    (f"{S72}/snake_v1.0_vc1.apk", "GAME-SNAKE1", "Snake (S72)"),
    (f"{GAMES}/build_sd/snake_deluxe_v1.0_vc1.apk", "GAME-SNAKEDX", "Snake Deluxe (S80)"),
    (f"{GAMES}/build_tetris/tetris_v1.0_vc1.apk", "GAME-TETRIS", "Mini Tetris (S80)"),
    (f"{GAMES}/build_2048/g2048_v1.0_vc1.apk", "GAME-2048", "2048 (S80)"),
    (f"{CACHE}/corpus/tictactoeclassic.apk", "GAME-TTT-CLASSIC", "TicTacToe Classic"),
    (f"{CACHE}/corpus/dooz.apk", "GAME-DOOZ18", "Dooz (corpus variant)"),
    (f"{CACHE}/s35new/com.itsfrz.tictactoe_5.apk", "GAME-TTT-FRZ", "TicTacToe (itsfrz)"),
    (f"{CACHE}/s35new/org.kirkezz.rttt_3.apk", "GAME-RTTT", "RealTime TicTacToe"),
    (f"{CACHE}/s35new/org.secuso.privacyfriendly2048_100.apk", "GAME-PF2048", "PrivacyFriendly 2048"),
    (f"{CACHE}/s37new/org.andstatus.game2048_47.apk", "GAME-AS2048", "andstatus 2048"),
    (f"{CACHE}/s35new/org.secuso.privacyfriendlydicer_101.apk", "GAME-DICER", "PrivacyFriendly Dicer"),
    (f"{CACHE}/s36new/org.secuso.privacyfriendlysudoku_19.apk", "GAME-SUDOKU", "PrivacyFriendly Sudoku"),
    (f"{CACHE}/s37new/com.thesuncat.sudoku_4.apk", "GAME-SUDOKU2", "Classic Sudoku"),
    (f"{CACHE}/s37new/com.joeld.minesweeper_7.apk", "GAME-MINES1", "Minesweeper (joeld)"),
    (f"{CACHE}/s37new/io.github.johnathan.minesweeper_6.apk", "GAME-MINES2", "Minesweeper (johnathan)"),
    (f"{CACHE}/s82/eu.veldsoft.no.thanks_1.apk", "GAME-NOTHANKS", "No Thanks!"),
    (f"{CACHE}/s82/eu.quelltext.memory_7.apk", "GAME-MEMORY", "Memory (quelltext)"),
    (f"{CACHE}/s82/com.sidhant.queens_93.apk", "GAME-QUEENS", "Queens (sidhant)"),
    (f"{CACHE}/s82/com.simondalvai.ball2box_69.apk", "GAME-BALL2BOX", "Ball2Box"),
    (f"{CACHE}/s82/crypto.o0o0o0o0o.games.blackjack_4.apk", "GAME-BLACKJACK", "Blackjack"),
    (f"{CACHE}/s82/com.jeffliu.balancetheball_4.apk", "GAME-BALANCE", "Balance the Ball"),
    (f"{CACHE}/s82/xyz.deepdaikon.quinb_10.apk", "GAME-QUINB", "Quinb"),
    (f"{CACHE}/s82/org.secuso.privacyfriendlybattleship_101.apk", "GAME-BATTLE", "PF Battleship"),
    (f"{CACHE}/s37new/edge.roll_11.apk", "GAME-EDGEROLL", "Edge Roll"),
    (f"{CANON}/tripeaks_v1.2.1_vc4.apk", "GAME-TRIPEAKS", "TriPeaks (S65)"),
    (f"{CANON}/fishrings_v1.23_vc6.apk", "GAME-FISHRINGS", "fishrings (S65)"),
]

APP_BATCH = [
    (f"{CANON}/app.varlorg.unote_30.apk", "APP-UNOTE", "uNote"),
    (f"{CACHE}/com.chessclock.android_29.apk", "APP-CHESSCLK", "Chess Clock"),
    (f"{CACHE}/dubrowgn.microtimer_8.apk", "APP-MICROTIMER", "MicroTimer"),
    (f"{CACHE}/omegacentauri.mobi.simplestopwatch_26.apk", "APP-STOPWATCH", "Simple Stopwatch"),
    (f"{CACHE}/com.github.muellerma.stopwatch_6.apk", "APP-STOPWATCH2", "Stopwatch (muellerma)"),
    (f"{CACHE}/org.billthefarmer.notes_139.apk", "APP-NOTES", "Notes (billthefarmer)"),
    (f"{CANON}/de.duenndns.gmdice_8.apk", "APP-GMDICE", "GameMaster Dice"),
    (f"{CACHE}/rkr.simplekeyboard.inputmethod_145.apk", "APP-KEYBOARD", "Simple Keyboard"),
    (f"{CACHE}/simple_flashlight_66.apk", "APP-FLASHLIGHT", "Simple Flashlight"),
    (f"{CACHE}/s82/com.bnyro.clock_24.apk", "APP-BNYROCLK", "Clock (Bnyro)"),
    (f"{CACHE}/s82/foehnix.widget_40.apk", "APP-FOEHNIX", "Foehnix widget"),
    (f"{CACHE}/s82/tibarj.tranquilstopwatch_17.apk", "APP-TRANQUIL", "Tranquil Stopwatch"),
]

HIGH_BATCH = [
    (f"{CACHE}/s82/se.tube42.p9.android_11.apk", "MAND-P9", "P9 (libGDX) [F-NEW-157 gate]"),
    (f"{CACHE}/s82/io.timelimit.android.aosp.direct_231.apk", "MAND-TIMELIMIT", "TimeLimit [ServiceLoader gate]"),
]


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_one(apk, title_id, label, frames=8):
    tag = title_id
    out = f"{OUT}/{tag}"
    os.makedirs(out, exist_ok=True)
    env = dict(os.environ)
    env["MINIANDROID_GFX_PROVENANCE"] = f"{out}/provenance.json"
    cmd = [ENG, "run", "--execution-mode", "real-dalvik",
           "--frames", str(frames), "--frame-delay", "300", "-o", out, apk]
    log = f"{out}.log"
    with open(log, "w") as lf:
        try:
            rc = subprocess.call(cmd, stdout=lf, stderr=lf, timeout=420, env=env)
        except subprocess.TimeoutExpired:
            rc = -1
    item = {"TITLE_ID": title_id, "label": label,
            "apk": os.path.basename(apk), "apk_sha256": sha256(apk),
            "rc": rc, "frames": 0}
    frames_l = sorted(glob.glob(f"{out}/frames/frame_*.png"))
    item["frames"] = len(frames_l)
    if frames_l:
        shot = frames_l[-1]
        m = audit_frame(shot)
        lvl, lname = level_of(m)
        item["visual"] = {k: m[k] for k in
                          ("UNIQUE_COLORS", "NONWHITE_RATIO", "IMAGE_PIXELS",
                           "ICON_PIXELS", "TEXT_PIXELS", "MONOCHROME_LIKE") if k in m}
        item["LEVEL"] = lvl
        item["LEVEL_NAME"] = lname
        item["shot_png"] = shot
        # JPG evidence ≤100KB
        jpg = f"{out}/{tag}.jpg"
        im = Image.open(shot).convert("RGB").resize((540, 960))
        q = 85
        while True:
            im.save(jpg, "JPEG", quality=q)
            if os.path.getsize(jpg) <= 100 * 1024 or q <= 35:
                break
            q -= 10
        item["shot_jpg"] = jpg
        item["shot_jpg_bytes"] = os.path.getsize(jpg)
    # provenance chain summary
    prov = f"{out}/provenance.json"
    if os.path.exists(prov):
        try:
            pj = json.load(open(prov))
            chain = pj.get("chain", pj)
            if isinstance(chain, dict):
                item["PROVENANCE_FIRST_DIVERGENCE"] = chain.get(
                    "first_divergence", pj.get("first_divergence"))
        except Exception:
            pass
    return item


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else "all"
    results = []
    batches = []
    if only in ("all", "games"):
        batches += GAME_BATCH
    if only in ("all", "apps"):
        batches += APP_BATCH
    if only in ("all", "high"):
        batches += HIGH_BATCH
    for apk, tid, label in batches:
        if not os.path.exists(apk):
            results.append({"TITLE_ID": tid, "label": label,
                            "apk": os.path.basename(apk), "error": "APK_MISSING"})
            print(f"[MISS] {tid} {apk}")
            continue
        r = run_one(apk, tid, label)
        results.append(r)
        print(f"[{tid}] rc={r['rc']} frames={r['frames']} "
              f"L{r.get('LEVEL','-')} {r.get('LEVEL_NAME','')} "
              f"uniq={r.get('visual',{}).get('UNIQUE_COLORS','?')}")
    with open(f"{OUT}/SWEEP_RESULTS.json", "w") as f:
        json.dump(results, f, indent=1)
    ok = sum(1 for r in results if r.get("LEVEL", -1) >= 1)
    print(f"SWEEP: {len(results)} titles, {ok} at L1+")
    return 0


if __name__ == "__main__":
    sys.exit(main())
