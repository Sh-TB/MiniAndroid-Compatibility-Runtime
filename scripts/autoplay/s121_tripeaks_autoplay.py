#!/usr/bin/env python3
"""s121_tripeaks_autoplay.py — TriPeaks solitaire FULL agent session (S121).

User directive: games must load COMPLETELY and be verified per the rules;
fix pre-existing problems. S120 left "click->card mapping offset" open —
this driver closes it by measurement, then plays a real multi-move session:

  Phase P (probe)   : no taps; confirm splash->lobby->deal timing (C3 vision).
  Phase C (calib)   : one tap at card#4 center (519,215); the EMPTIED SLOT in
                      the bottom row reveals the tap->card mapping (no game
                      peeking — pure render diff, S99 law).
  Phase M (main)    : planned session — legal moves (±1 rank onto the waste)
                      and stock draws (Cards Remaining 23 -> 22 -> ...),
                      HUD counters (Game Winings) as the authority.
  Phase D (det)     : main schedule replayed 3x, frames byte-compared
                      (S100 §25 repeatability law).

C1 actuator: --tap through the canonical TouchDispatcher.
C3 vision: rendered frames only.  C7: every leg is a full launch of the real
APK with the committed tap prefix replayed.
"""
import glob
import os
import subprocess
import sys

from PIL import Image

ROOT = "/home/z/my-project"
ENG = f"{ROOT}/miniandroid/build/miniandroid"
APK = f"{ROOT}/upload/s65_apks/tripeaks_v1.2.1_vc4.apk"
OUT = f"{ROOT}/run/s121_tripeaks"

GREEN = (51, 170, 17)
ROW_Y = 215                 # bottom-row face-up card band center
ROW_X = [172, 290, 401, 519, 644, 762, 880, 998]   # measured card centers
STOCK = (526, 404)
WASTE = (878, 404)
NEW_GAME = (540, 188)


def is_green(p, tol=28):
    return all(abs(p[i] - GREEN[i]) <= tol for i in range(3))


def run_engine(taps, n_frames, out_dir, frame_delay=250):
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


def last_frame(d):
    fs = sorted(glob.glob(f"{d}/frames/frame_*.png"))
    return fs[-1] if fs else None


def frame(d, idx):
    p = f"{d}/frames/frame_{idx:03d}.png"
    return p if os.path.exists(p) else None


def row_slots(png):
    """Return [filled] flags for the 8 bottom-row card slots (vision)."""
    img = Image.open(png).convert("RGB")
    px = img.load()
    filled = []
    for cx in ROW_X:
        n = sum(0 if is_green(px[cx + dx, ROW_Y]) else 1
                for dx in range(-40, 41, 8))
        filled.append(n >= 6)
    return filled


def waste_sig(png):
    """Signature of the waste-card region (identity proxy, exact bytes)."""
    img = Image.open(png).convert("RGB").crop((832, 348, 924, 464))
    return hash(img.tobytes())


def cards_remaining(png):
    """Cards Remaining counter region — pixel-diff proxy (bottom HUD)."""
    img = Image.open(png).convert("L").crop((0, 1580, 560, 1680))
    return hash(img.tobytes())


def main():
    os.makedirs(OUT, exist_ok=True)
    report = []

    # ---------- Phase P: probe ----------
    pd = f"{OUT}/probe"
    rc = run_engine([], 61, pd)
    deal = frame(pd, 40)
    lobby = frame(pd, 22)
    assert lobby and os.path.exists(lobby), "no lobby frame"
    assert deal and os.path.exists(deal), "no deal frame"
    slots0 = row_slots(deal)
    report.append(f"probe rc={rc} lobby@22 deal@40 slots={slots0}")
    print(report[-1])

    # ---------- Phase C: calibration tap ----------
    cd = f"{OUT}/calib"
    rc = run_engine([(519, ROW_Y, 44)], 56, cd)
    pre = frame(cd, 42)
    post = last_frame(cd)
    s_pre, s_post = row_slots(pre), row_slots(post)
    emptied = [i for i in range(8) if s_pre[i] and not s_post[i]]
    wchg = waste_sig(pre) != waste_sig(post)
    report.append(f"calib tap(519,{ROW_Y})@44 rc={rc} emptied_slots={emptied} "
                  f"waste_changed={wchg}")
    print(report[-1])

    # derive mapping: tap x -> selected slot index
    if emptied:
        tapped_slot = ROW_X.index(519)
        offset = emptied[0] - tapped_slot
    else:
        offset = None
    report.append(f"tap->card offset = {offset} "
                  f"(0 means 1:1; None means no legal move detected)")
    print(report[-1])

    # ---------- Phase M: main session ----------
    # Planned (assuming offset resolved as off): moves follow the deal
    # 3h 8c 7h 5d Kh 5h Ac Qh + waste 6c.
    # Strategy: play every legal +-1 from the current waste, then draw.
    md = f"{OUT}/main"
    taps = [(NEW_GAME[0], NEW_GAME[1], 24)]

    def tx(i):   # slot index -> tap x honoring measured offset
        return ROW_X[i + offset] if (offset is not None and
                                     0 <= i + offset < 8) else ROW_X[i]

    # The deal is deterministic (S120 x2 identical). Known-legal openers
    # against waste 6c: 7h (slot2) and 5d (slot3) and 5h (slot5).
    schedule = [
        (2, 44, "play 7h onto 6c"),      # waste -> 7h
        (1, 48, "play 8c onto 7h"),      # waste -> 8c
        (6, 52, "play 5h onto ..."),     # only legal if waste -1/+1 fits
        ("stock", 56, "draw from stock"),
        ("stock", 60, "draw again"),
    ]
    for (slot, fr, note) in schedule:
        if slot == "stock":
            taps.append((STOCK[0], STOCK[1], fr))
        else:
            taps.append((tx(slot), ROW_Y, fr))
    rc = run_engine(taps, 84, md)
    report.append(f"main rc={rc} taps={taps}")
    print(report[-1])

    # stage analysis: waste signature + row slots across key frames
    stages = {}
    for name, fr in [("dealt", 40), ("after44", 46), ("after48", 50),
                     ("after52", 54), ("after56", 58), ("after60", 62),
                     ("final", 83)]:
        p = frame(md, fr)
        if p:
            stages[name] = {
                "waste_changed_vs_dealt": waste_sig(p) != waste_sig(deal),
                "slots": row_slots(p),
            }
    for k, v in stages.items():
        report.append(f"stage {k}: {v}")
        print(f"stage {k}: {v}")

    # HUD counter diffs (Game Winings / Cards Remaining proxies)
    hud = {}
    base = cards_remaining(deal)
    for name, fr in [("after44", 46), ("after48", 50), ("after52", 54),
                     ("after56", 58), ("after60", 62), ("final", 83)]:
        p = frame(md, fr)
        if p:
            hud[name] = cards_remaining(p) != base
    report.append(f"HUD-counter-region changed per stage: {hud}")
    print(report[-1])

    # ---------- Phase D: determinism 3x ----------
    digests = []
    for run in range(3):
        dd = f"{OUT}/det{run}"
        run_engine(taps, 84, dd)
        h = []
        for fr in (30, 40, 46, 50, 58, 70, 83):
            p = frame(dd, fr)
            h.append(Image.open(p).tobytes().__hash__() if p else "MISS")
        digests.append(h)
    det = all(d == digests[0] for d in digests)
    report.append(f"determinism 3x: {'IDENTICAL' if det else 'VARIANCE'} "
                  f"{digests}")
    print(report[-1])

    with open(f"{OUT}/s121_tripeaks_record.txt", "w") as f:
        f.write("\n".join(report) + "\n")
    print("WROTE", f"{OUT}/s121_tripeaks_record.txt")


if __name__ == "__main__":
    main()
