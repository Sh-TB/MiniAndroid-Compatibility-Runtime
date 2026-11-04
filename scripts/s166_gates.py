#!/usr/bin/env python3
"""s166_gates.py — S166 Z10: anchor-family gate on the final campaign binary.

REF = pre-campaign D3 insurance 770206f2d976d997
NEW = final adopted binary 2a5464c2bf15f9ec (Z1 alloc-log gate + Z3
readable_class on-demand; Z8 memo reverted — build reproduces 2a5464c2).
Claim: byte-inert behavior on every anchor + dooz face-stable env-off.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

BASE = Path("/home/z/my-project")
sys.path.insert(0, str(BASE / "scripts"))
import s166_trains as s

REF = s.BIN_D3
NEW = s.BIN_NEW
OUT = s.OUT / "gates_z10"
OUT.mkdir(parents=True, exist_ok=True)

APKS = {
    # paths re-censored 2026-11-05: the recycle moved the anchor APKs;
    # the first gate run produced face=None on BOTH arms (fake-DRIFT) —
    # the S165 None==None lesson, inverse form, caught on read-back.
    "microtimer": (BASE / "upload/canonical_apks/dubrowgn.microtimer_8.apk",
                   "dubrowgn.microtimer"),
    "g2048": (BASE / "upload/s80_games/build_2048/g2048_v1.0_vc1.apk",
              "com.miniandroid.g2048"),
    "opencalc": (BASE / "upload/opencalculator_53.apk",
                 "com.darkempire78.opencalculator"),
}
PINS = {"microtimer": "bbd350b6c14fbd52"}


def app_run(bin_path, tag, apk, store, pkg, max_seconds=75):
    for k in s.CLEAN_ENVS:
        os.environ.pop(k, None)
    s.t.ensure_store(apk, store, bin_path, pkg)
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
        "stderr_sha16": s.t.sha16(console) if console.exists() else None,
        "screenshot_face": s.t.sha16(shot) if shot.exists() else None,
    }


def main():
    rows = {"ref_bin": s.t.sha16(REF), "new_bin": s.t.sha16(NEW),
            "anchors": {}}
    for name, (apk, pkg) in APKS.items():
        pair = {}
        for tag, b in ((f"{name}_ref", REF), (f"{name}_new", NEW)):
            pair[tag] = app_run(b, tag, apk, OUT / f"store_{name}", pkg)
            print(f"[{tag}] face={pair[tag]['screenshot_face']} "
                  f"wall={pair[tag]['wall_s']}s", flush=True)
        pair["delta_inert"] = (pair[f"{name}_ref"]["screenshot_face"]
                               is not None and
                               pair[f"{name}_ref"]["screenshot_face"] ==
                               pair[f"{name}_new"]["screenshot_face"])
        if name in PINS:
            pair["pin_match"] = bool(
                pair[f"{name}_new"]["screenshot_face"] and
                pair[f"{name}_new"]["screenshot_face"].startswith(PINS[name]))
        rows["anchors"][name] = pair
    # dooz face-stable env-off on the final binary
    row = app_run(NEW, "dooz_inert", s.DOOZ_APK, OUT / "store_dooz",
                  s.DOOZ_PKG, max_seconds=90)
    rows["dooz_inert"] = row
    rows["dooz_inert"]["face_stable"] = (
        row["screenshot_face"] == "11a38a5aeeff45a6")
    all_inert = all(v.get("delta_inert") for v in rows["anchors"].values())
    rows["VERDICT"] = ("PASS — final campaign binary byte-inert on all anchors"
                       if all_inert and rows["dooz_inert"]["face_stable"]
                       else "DRIFT")
    json.dump(rows, open(s.EVID / "S166_Z10_GATES.json", "w"), indent=1)
    print("VERDICT:", rows["VERDICT"])
    for n, v in rows["anchors"].items():
        print(n, "inert:", v["delta_inert"], "pin:", v.get("pin_match"))
    print("dooz face_stable:", rows["dooz_inert"]["face_stable"],
          "wall:", row["wall_s"])


if __name__ == "__main__":
    main()
