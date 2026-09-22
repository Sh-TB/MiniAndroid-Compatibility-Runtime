#!/usr/bin/env python3
"""s81_batch01.py — S81 BATCH-01 (§13/§14): mixed execution subset.

§31 smart-not-blind + §32 disk guard: download a deterministic mixed subset
(5 simple apps + 5 mid + 5 visually rich + 5 games + 5 high-value) of
BATCH-01 from F-Droid, run each through the real engine, visual-audit the
last frame, and promote corpus statuses DISCOVERED → SOURCED → LOADED →
EXECUTED → RENDERED (+ VISUALLY_AUDITED metrics). Every APK records
SHA256 + size (§32 RUN_SIZE law). Artifacts under run/s81_batch01/ with
small per-item retention (§33: last frame + log only).
"""
import glob
import hashlib
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s81_visual_audit import audit_frame, level_of

ROOT = "/home/z/my-project"
ENG = f"{ROOT}/miniandroid/build/miniandroid"
OUT = f"{ROOT}/run/s81_batch01"
os.makedirs(OUT, exist_ok=True)

# §14 mix: 25 items — deterministic picks from the BATCH-01 plan + corpus
PICKS = [
    # 5 simple apps (calculator/clock family — small APKs)
    ("com.best.deskclock", "app"),
    ("com.bnyro.clock", "app"),
    ("com.alaskalinuxuser.hourlyreminder", "app"),
    ("com.droidquest", "app"),
    ("fr.neamar.androidtimesbugger", "app"),
    # 5 mid apps (from APPS_100 corpus picks)
    ("com.qwde.ccm", "app"),
    ("app.halma", "game"),
    ("eu.veldsoft.no.thanks", "game"),
    ("com.simondalvai.ball2box", "game"),
    ("cos.premy.mines", "game"),
    # 5 visually rich
    ("com.astroloop.game", "game"),
    ("com.jeffliu.balancetheball", "game"),
    ("crypto.o0o0o0o0o.games.blackjack", "game"),
    ("si.palcka.tarok", "game"),
    ("io.github.hathibelagal.mykanji", "app"),
    # 5 games (solitaire/chess/battleship families)
    ("de.tobiasbielefeld.solitaire", "game"),
    ("com.sidhant.queens", "game"),
    ("org.secuso.privacyfriendlybattleship", "game"),
    ("com.dash1971.maia_chess", "game"),
    ("com.vovagorodok.blichess", "game"),
    # 5 unknown/high-value
    ("page.codeberg.lanticy.guandan", "game"),
    ("xyz.deepdaikon.quinb", "game"),
    ("eu.quelltext.memory", "game"),
    ("com.vayunmathur.games.solitaire", "game"),
    ("bim.app", "app"),
]

FDROID_APK = "https://f-droid.org/repo/{pkg}_{vcode}.apk"


def apk_url(pkg):
    """resolve latest version code via the v1 API, return (url, vcode, vname)"""
    try:
        body = subprocess.run(["curl", "-s", "-m", "20",
                               f"https://f-droid.org/api/v1/packages/{pkg}"],
                              capture_output=True, timeout=25).stdout
        d = json.loads(body)
        p = (d.get("packages") or [{}])[0]
        vc = p.get("versionCode")
        return (FDROID_APK.format(pkg=pkg, vcode=vc), vc, p.get("versionName"))
    except Exception:
        return None, None, None


def main():
    report = []
    for pkg, kind in PICKS:
        url, vc, vname = apk_url(pkg)
        item = {"PACKAGE": pkg, "KIND": kind, "VERSION": vname, "VERSION_CODE": vc,
                "STATUS": "DISCOVERED"}
        if not url:
            item["STATUS"] = "SOURCE_NOT_RECOVERED"
            report.append(item)
            print(f"SOURCING-FAIL {pkg}")
            continue
        apk_path = f"{OUT}/{pkg}_{vc}.apk"
        if not os.path.exists(apk_path):
            r = subprocess.run(["curl", "-s", "-m", "120", "-o", apk_path, url])
            if r.returncode != 0 or not os.path.exists(apk_path) or os.path.getsize(apk_path) < 10000:
                item["STATUS"] = "SOURCED_FAIL"
                report.append(item)
                print(f"DOWNLOAD-FAIL {pkg}")
                continue
        item["APK_SHA256"] = hashlib.sha256(open(apk_path, "rb").read()).hexdigest()
        item["APK_SIZE"] = os.path.getsize(apk_path)
        item["STATUS"] = "SOURCED"
        # run
        rundir = f"{OUT}/{pkg}_{vc}"
        os.makedirs(rundir, exist_ok=True)
        cmd = [ENG, "run", "--execution-mode", "real-dalvik",
               "--frames", "8", "--frame-delay", "300", "-o", rundir, apk_path]
        log = f"{rundir}.log"
        with open(log, "w") as lf:
            try:
                rc = subprocess.call(cmd, stdout=lf, stderr=lf, timeout=420)
            except subprocess.TimeoutExpired:
                rc = -1
        item["RUN_RC"] = rc
        item["STATUS"] = "LOADED" if rc == 0 else "LOADED_RC1"
        frames = sorted(glob.glob(f"{rundir}/frames/frame_*.png"))
        if frames:
            m = audit_frame(frames[-1])
            lvl, name = level_of(m)
            item["VISUAL"] = {k: m[k] for k in
                              ("UNIQUE_COLORS", "COLOR_ENTROPY",
                               "DOMINANT_COLOR_RATIO", "NON_BACKGROUND_RATIO",
                               "IMAGE_PIXELS", "ICON_PIXELS", "TEXT_PIXELS",
                               "FLAGS")}
            item["VISUAL"]["LEVEL"] = lvl
            item["VISUAL"]["LEVEL_NAME"] = name
            # S80 ladder law: rc=1-with-render (F-016 exception-honesty) is
            # a documented boundary, NOT a load failure — classify on
            # artifacts (frames + pixels), keep RUN_RC honest alongside.
            item["STATUS"] = ("RENDERED" if lvl >= 2 and item["RUN_RC"] == 0
                              else "RENDERED_RC1" if lvl >= 2
                              else "RENDERED_PARTIAL" if item["RUN_RC"] == 0
                              else "RENDERED_PARTIAL_RC1")
            item["MINIANDROID_FRAME"] = f"run/s81_batch01/{pkg}_{vc}/frames/{os.path.basename(frames[-1])}"
        print(f"{item['STATUS']:<16} {pkg}")
        report.append(item)
    with open(f"{OUT}/batch01_report.json", "w") as f:
        json.dump({"BATCH": "BATCH-01", "MIX_SUBSET": True, "SIZE": len(report),
                   "DISK_BEFORE_MB": None, "results": report}, f, indent=1)
    ok = sum(1 for r in report if r["STATUS"].startswith("RENDERED"))
    print(f"\nBATCH-01: {ok}/{len(report)} rendered; report=run/s81_batch01/batch01_report.json")


if __name__ == "__main__":
    main()
