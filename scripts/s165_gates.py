#!/usr/bin/env python3
"""s165_gates.py — S165 D5 train: byte-inertness gates on the D3 binary.

REF = S164 seedskip bin 1cb76138897a22d2 (the immediate parent).
NEW = S165 D3-checkpoint bin (44d73d91... — build/miniandroid).
The checkpoint + fb-histo code is env-gated default-off, so with no env
the two binaries must be byte-inert on every anchor (microtimer full pin
bbd350b6c14fbd52, g2048, opencalc) and dooz's standing face 11a38a5a.
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

BASE = Path("/home/z/my-project")
sys.path.insert(0, str(BASE / "scripts"))
import s165_trains as t

REF = t.BIN_SEED
NEW = t.BASE / "miniandroid/build/miniandroid"
OUT = t.OUT / "gates"
OUT.mkdir(parents=True, exist_ok=True)
EVID = t.EVID

APKS = {
    "microtimer": (BASE / "upload/microtimer.apk", "dubrowgn.microtimer"),
    "g2048": (BASE / "upload/g2048.apk", "com.miniandroid.g2048"),
    "opencalc": (BASE / "upload/opencalculator_53.apk",
                 "com.darkempire78.opencalculator"),
}
PINS = {"microtimer": "bbd350b6c14fbd52"}


def app_run(bin_path, tag, apk, store, pkg, max_seconds=75):
    for k in ("MINIANDROID_APP_DATA_SEED", "MINIANDROID_PROVIDER_SKIP",
              "MINIANDROID_DRAW_CHECKPOINT", "MINIANDROID_FB_HISTO"):
        os.environ.pop(k, None)
    store.parent.mkdir(parents=True, exist_ok=True)
    t.ensure_store(apk, store, bin_path, pkg)
    rundir = OUT / tag
    console = OUT / f"{tag}.err"
    cmd = [str(bin_path), "run", "--execution-mode", "real-dalvik",
           "--data-root", str(store), "-o", str(rundir),
           "--max-seconds", str(max_seconds), "--frames", "4", "--trace",
           "--package", pkg]
    t0 = time.time()
    with open(console, "w") as cf:
        subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                       timeout=max_seconds + 90)
    wall = round(time.time() - t0, 1)
    shot = rundir / "screenshot.png"
    return {
        "tag": tag, "wall_s": wall,
        "stderr_sha16": t.sha16(console) if console.exists() else None,
        "screenshot_face": t.sha16(shot) if shot.exists() else None,
    }


def main():
    rows = {"ref_bin": t.sha16(REF), "new_bin": t.sha16(NEW), "anchors": {}}
    for name, (apk, pkg) in APKS.items():
        pair = {}
        for tag, b in ((f"{name}_ref", REF), (f"{name}_new", NEW)):
            pair[tag] = app_run(b, tag, apk, OUT / f"store_{name}", pkg)
            print(f"[{tag}] face={pair[tag]['screenshot_face']} "
                  f"wall={pair[tag]['wall_s']}s")
        pair["delta_inert"] = (pair[f"{name}_ref"]["screenshot_face"]
                               is not None and
                               pair[f"{name}_ref"]["screenshot_face"] ==
                               pair[f"{name}_new"]["screenshot_face"])
        if name in PINS:
            pair["pin_match"] = bool(
                pair[f"{name}_new"]["screenshot_face"] and
                pair[f"{name}_new"]["screenshot_face"].startswith(PINS[name]))
        rows["anchors"][name] = pair
    # dooz face-inert (env OFF — the checkpoint must be inert by default)
    t.ensure_store(t.DOOZ_APK, t.OUT / "store_dooz", NEW, t.DOOZ_PKG)
    row = app_run(NEW, "dooz_inert", t.DOOZ_APK, t.OUT / "store_dooz",
                  t.DOOZ_PKG, max_seconds=90)
    rows["dooz_inert"] = row
    rows["dooz_inert"]["face_stable"] = (
        row["screenshot_face"] == "11a38a5aeeff45a6")
    all_inert = all(v.get("delta_inert") for v in rows["anchors"].values())
    rows["VERDICT"] = ("PASS — D3 binary byte-inert on all anchors"
                       if all_inert and rows["dooz_inert"]["face_stable"]
                       else "DRIFT")
    json.dump(rows, open(EVID / "S165_D5_GATES.json", "w"), indent=1)
    print(json.dumps({k: rows[k] for k in
                      ("ref_bin", "new_bin", "VERDICT")}, indent=1))
    for n, v in rows["anchors"].items():
        print(n, "inert:", v["delta_inert"], "pin:", v.get("pin_match"))
    print("dooz face_stable:", rows["dooz_inert"]["face_stable"],
          "wall:", row["wall_s"])


if __name__ == "__main__":
    main()
