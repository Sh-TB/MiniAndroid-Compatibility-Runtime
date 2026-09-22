#!/usr/bin/env python3
"""s84_rescue_runs.py — re-run the 16 S83 titles whose only evidence was a
shared near-blank final frame (content SHA eb16ab5c… ×16 = evidence-integrity
bug caught by the S84 validator R5).

Fresh runs at the CURRENT engine (F-NEW-160, battery 26/26) provide real
provenance for canonical screenshots. obs + click passes, same params as
the S84 NEW-50 campaign.
"""
import glob
import hashlib
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s81_visual_audit import audit_frame, level_of, apk_resource_counts

ROOT = "/home/z/my-project"
ENG = f"{ROOT}/miniandroid/build/miniandroid"
OUT = f"{ROOT}/run/s84_rescue"
S82 = "/tmp/my-project/apk_cache/s82"
CORPUS = "/tmp/my-project/apk_cache/corpus"
os.makedirs(OUT, exist_ok=True)

TITLES = [
    ("dooz", f"{CORPUS}/dooz.apk", "Dooz (tic-tac-toe)", "game"),
    ("com.best.deskclock_2036", f"{S82}/com.best.deskclock_2036.apk",
     "DeskClock", "app"),
    ("com.bnyro.clock_24", f"{S82}/com.bnyro.clock_24.apk", "Bnyro Clock",
     "app"),
    ("se.tube42.p9.android_11", f"{S82}/se.tube42.p9.android_11.apk",
     "P9 (tube42)", "app"),
    ("com.newsblur_289", f"{S82}/com.newsblur_289.apk", "NewsBlur", "app"),
    ("io.timelimit.android.aosp.direct_231",
     f"{S82}/io.timelimit.android.aosp.direct_231.apk", "TimeLimit", "app"),
    ("com.sidhant.queens_93", f"{S82}/com.sidhant.queens_93.apk", "Queens",
     "game"),
    ("org.secuso.privacyfriendlybattleship_101",
     f"{S82}/org.secuso.privacyfriendlybattleship_101.apk", "Battleship",
     "game"),
    ("app.halma_15", f"{S82}/app.halma_15.apk", "Halma", "game"),
    ("com.astroloop.game_4", f"{S82}/com.astroloop.game_4.apk", "Astroloop",
     "game"),
    ("si.palcka.tarok_203", f"{S82}/si.palcka.tarok_203.apk", "Tarok",
     "game"),
    ("page.codeberg.lanticy.guandan_7",
     f"{S82}/page.codeberg.lanticy.guandan_7.apk", "Guandan", "game"),
    ("com.bupkis.tirailleur_13", f"{S82}/com.bupkis.tirailleur_13.apk",
     "Tirailleur", "game"),
    ("com.eightsines.firestrike.opensource_2000",
     f"{S82}/com.eightsines.firestrike.opensource_2000.apk", "Firestrike",
     "game"),
    ("com.vayunmathur.games.solitaire_20260804",
     f"{S82}/com.vayunmathur.games.solitaire_20260804.apk",
     "Solitaire (vayunmathur)", "game"),
    ("de.tobiasbielefeld.solitaire_71",
     f"{S82}/de.tobiasbielefeld.solitaire_71.apk",
     "Solitaire (tobiasbielefeld)", "game"),
]


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def engine_run(apk, out_dir, click):
    os.makedirs(out_dir, exist_ok=True)
    cmd = [ENG, "run", "--execution-mode", "real-dalvik",
           "--frames", "8", "--frame-delay", "300", "--max-seconds", "240",
           "-o", out_dir, apk]
    if click:
        cmd.append("--click-test")
    log = out_dir + ("_click.log" if click else "_obs.log")
    with open(log, "w") as lf:
        try:
            rc = subprocess.call(cmd, stdout=lf, stderr=lf, timeout=300)
        except subprocess.TimeoutExpired:
            rc = -1
    return rc, log


def run_one(item):
    tag, apk, label, kind = item
    rec = {"tag": tag, "label": label, "kind": kind, "apk": apk,
           "apk_sha256": sha256(apk) if os.path.exists(apk) else ""}
    if not os.path.exists(apk):
        rec["rc_obs"] = -2
        return rec
    ro, lo = engine_run(apk, f"{OUT}/{tag}/obs", click=False)
    rc_, lc = engine_run(apk, f"{OUT}/{tag}/click", click=True)
    rec["rc_obs"] = ro
    rec["rc_click"] = rc_
    fr = sorted(glob.glob(f"{OUT}/{tag}/obs/frames/frame_*.png"))
    rec["frames"] = len(fr)
    if fr:
        m = audit_frame(fr[-1])
        lvl, name = level_of(m)
        m["LEVEL"], m["LEVEL_NAME"] = lvl, name
        m.update(apk_resource_counts(apk))
        rec["visual"] = m
        rec["final_frame_sha256"] = sha256(fr[-1])
    cl = sorted(glob.glob(f"{OUT}/{tag}/click/frames/frame_*.png"))
    rec["click_frames"] = len(cl)
    if cl:
        rec["click_final_sha256"] = sha256(cl[-1])
    rec["state_change"] = bool(
        rec.get("final_frame_sha256") and rec.get("click_final_sha256")
        and rec["final_frame_sha256"] != rec["click_final_sha256"])
    v = rec.get("visual", {})
    print(f"[{tag[:40]:<40}] rc={ro} L{v.get('LEVEL','-')} "
          f"uniq={v.get('UNIQUE_COLORS','-'):<5} "
          f"chg={rec['state_change']}")
    return rec


def main():
    with ThreadPoolExecutor(max_workers=4) as ex:
        results = list(ex.map(run_one, TITLES))
    with open(f"{OUT}/report.json", "w") as f:
        json.dump({"wave": "S84 rescue (S83 near-blank 16)",
                   "results": results}, f, indent=1)
    n_ok = sum(1 for r in results if r.get("frames"))
    n_chg = sum(1 for r in results if r.get("state_change"))
    print(f"rescue: {n_ok}/16 frames, {n_chg} state-change, "
          f"report {OUT}/report.json")


if __name__ == "__main__":
    main()
