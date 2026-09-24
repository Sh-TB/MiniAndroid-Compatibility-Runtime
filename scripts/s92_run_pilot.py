#!/usr/bin/env python3
"""s92_run_pilot.py — S92 §26/§27 real-corpus pilot runner.

Runs the diverse pilot titles through MiniAndroid with full evidence
instrumentation, builds visual contracts, verifies each run, and emits
verdicts + the S91-claim re-audit (§32). REAL EXECUTION ONLY (§27):
no simulated evidence, no invented numbers.

Pilot selection (S92 §26 — deliberately diverse):
  view-xml (tictactoe, urlchecker, chessclock, unote, gmdice)
  canvas/custom view (dodge, fish-rings)
  surfaceview (bobball)
  glsurface (bouncy)
  raster-heavy app (nounours, hotdeath)
  previously-suspicious recheck (bouncy: only-2-frames GIF claim)
"""
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

BASE_OUT = os.path.join(REPO, "run", "s92pilot")
VERDICTS = os.path.join(REPO, "registry", "graphics_verdicts")
CONTRACTS = os.path.join(REPO, "registry", "visual_contracts")
MA_BIN = os.path.join(REPO, "miniandroid", "build", "miniandroid")
DL = os.path.join(REPO, "miniandroid", "download")

PILOT = [
    # (case_name, apk_path, package, title, frames, taps, source_url, note)
    ("tictactoe", "com.emmanuelmess.tictactoe_3.apk",
     "com.emmanuelmess.tictactoe", "TicTacToe Classic", 12,
     None, "https://f-droid.org/repo/com.emmanuelmess.tictactoe_3.apk",
     "view-xml game, GIF-claimed S91"),
    ("nounours", "ca.rmen.nounours_358.apk", "ca.rmen.nounours",
     "ca.rmen.nounours", 8, None,
     None, "raster-heavy tactile app, GIF-claimed S91"),
    ("dodge", "com.dozingcatsoftware.dodge_15.apk",
     "com.dozingcatsoftware.dodge", "Dodge", 10,
     None, None, "canvas game, GIF-claimed S84/S86"),
    ("bouncy", "com.dozingcatsoftware.bouncy_63.apk",
     "com.dozingcatsoftware.bouncy", "Vector Pinball", 10,
     None, None, "GLSurface game, GIF-claimed, 2-frame evidence"),
    ("hotdeath", "com.smorgasbork.hotdeath_1011.apk",
     "com.smorgasbork.hotdeath", "Hot Death Uno", 10,
     None, None, "card game, raster assets"),
    ("bobball", "org.bobstuff.bobball_117.apk", "org.bobstuff.bobball",
     "Bobball", 10, None, None, "surfaceview game"),
    ("urlchecker", "com.trianguloy.urlchecker_28.apk",
     "com.trianguloy.urlchecker", "URL Checker", 10, None, None,
     "app, GIF-claimed S91"),
    ("chessclock", "com.chessclock.android_29.apk",
     "com.chessclock.android", "Chess Clock", 10, None, None,
     "app, VERIFIED screenshot"),
    ("unote", "app.varlorg.unote_30.apk", "app.varlorg.unote", "uNote",
     10, None, None, "notes app"),
    ("gmdice", "de.duenndns.gmdice_8.apk", "de.duenndns.gmdice", "GM Dice",
     10, None, None, "dice app, raster icons"),
    ("fishrings", "eu.veldsoft.fish.rings_6.apk", "eu.veldsoft.fish.rings",
     "Fish Rings", 40, (540, 1300, 20), None,
     "canvas game, 5s splash, S91 icon-E2E proof — independent rerun"),
]


def sh(cmd, **kw):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          **kw)


def find_apk(fname):
    for base in (DL, os.path.join(DL, "exp076_corpus"),
                 os.path.join(REPO, "miniandroid", "download")):
        p = os.path.join(base, fname)
        if os.path.isfile(p):
            return p
    return None


def run_title(case, apk, package, frames, taps):
    rundir = os.path.join(BASE_OUT, case)
    os.makedirs(rundir, exist_ok=True)
    env = dict(os.environ)
    env["MINIANDROID_GFX_PROVENANCE"] = os.path.join(rundir,
                                                     "gfx_provenance.json")
    env["MINIANDROID_CLICK_AUDIT"] = os.path.join(rundir, "click_audit.jsonl")
    tap = f" --tap {taps[0]},{taps[1]}@{taps[2]}" if taps else ""
    cmd = (f"{MA_BIN} run -o {rundir} --execution-mode real-dalvik "
           f"--frames {frames} --width 1080 --height 1920 "
           f"--data-root {rundir}/data{tap} --apk {apk}")
    r = sh(cmd, env=env, timeout=600)
    return rundir, r.returncode, (r.stdout or "")[-3000:], \
        (r.stderr or "")[-3000:]


def main():
    only = sys.argv[1:] or None
    os.makedirs(VERDICTS, exist_ok=True)
    os.makedirs(CONTRACTS, exist_ok=True)
    results = {}
    for (case, fname, package, title, frames, taps, src_url,
         note) in PILOT:
        if only and case not in only:
            continue
        apk = find_apk(fname)
        if not apk:
            results[case] = {"error": f"APK not found: {fname}"}
            print(f"{case:12s} APK MISSING {fname}")
            continue
        rundir, rc, out, err = run_title(case, apk, package, frames, taps)
        contract_path = os.path.join(CONTRACTS, f"{package}.json")
        cr = subprocess.run(
            [sys.executable, os.path.join(REPO, "tools",
                                          "build_visual_contract.py"),
             "--apk", apk, "--package", package, "--title", title,
             "--run-dir", rundir, "--out", contract_path],
            capture_output=True, text=True)
        vpath = os.path.join(VERDICTS,
                             f"{package}@{os.path.basename(apk)}"
                             f".json".replace(".apk.json", ".json"))
        vr = subprocess.run(
            [sys.executable, os.path.join(REPO, "tools", "verify_graphics.py"),
             "verify-run", "--run-dir", rundir, "--apk", apk,
             "--contract", contract_path, "--package", package,
             "--title", title, "--out", vpath],
            capture_output=True, text=True)
        verdict = {}
        if os.path.isfile(vpath):
            verdict = json.load(open(vpath))
        results[case] = {
            "apk": os.path.basename(apk), "run_rc": rc,
            "verdict": vpath if verdict else None,
            "overall": verdict.get("overall"),
            "failing": verdict.get("failing_stages"),
            "family": verdict.get("renderer_family"),
            "note": note,
            "verify_stderr": (vr.stderr or "")[-300:] if not verdict else "",
        }
        print(f"{case:12s} rc={rc} overall={verdict.get('overall')} "
              f"family={verdict.get('renderer_family')} "
              f"fails={verdict.get('failing_stages')}")
    with open(os.path.join(BASE_OUT, "PILOT_RESULTS.json"), "w") as f:
        json.dump(results, f, indent=1, sort_keys=True)
    print("saved:", os.path.join(BASE_OUT, "PILOT_RESULTS.json"))


if __name__ == "__main__":
    main()
