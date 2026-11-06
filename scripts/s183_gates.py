#!/usr/bin/env python3
"""s183_gates.py — standing-title gate check on the B1 binary (additive-law byte-inertness)."""
import json, os, re, subprocess, sys, time, shutil
from pathlib import Path

BASE = Path("/home/z/my-project")
sys.path.insert(0, str(BASE / "scripts"))
import s165_trains as t
import s166_trains as s166

BIN = BASE / "miniandroid" / "build" / "miniandroid"
OUT = BASE / "run_s183_gates"
OUT.mkdir(parents=True, exist_ok=True)

GATES = [
    ("microtimer", "upload/canonical_apks/dubrowgn.microtimer_8.apk", "bbd350b6c14fbd52"),
    ("g2048", "upload/canonical_apks/g2048_1.2.apk", "f43face08299ffc6"),
    ("opencalc", "upload/s80_games/build_opencalc/opencalc_v1.1_vc4.apk", None),  # opencalc apk name varies
    ("dooz", "upload/canonical_apks/io.github.yamin8000.dooz_23.apk", "a0fae9072313e2d1"),
]
rows = {}
for name, apk_rel, want in GATES:
    apk = BASE / apk_rel
    if not apk.exists():
        rows[name] = {"error": "apk missing"}
        continue
    store = OUT / f"store_{name}"
    if store.exists():
        shutil.rmtree(store)
    subprocess.run([str(BIN), "install", str(apk), "--data-root", str(store)],
                   capture_output=True, timeout=600)
    apps = store / "data" / "app"
    ds = [d.name for d in apps.iterdir() if d.is_dir() and not d.name.startswith(".")] if apps.exists() else []
    if not ds:
        rows[name] = {"error": "install fail"}
        continue
    pkg = ds[0]
    for k in s166.CLEAN_ENVS:
        os.environ.pop(k, None)
    rundir = OUT / name
    cmd = [str(BIN), "run", "--execution-mode", "real-dalvik", "--data-root",
           str(store), "-o", str(rundir), "--max-seconds", "40", "--frames", "4",
           "--trace", "--package", pkg]
    with open(OUT / f"{name}.err", "w") as cf:
        subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT, timeout=150)
    shot = rundir / "screenshot.png"
    face = t.sha16(shot) if shot.exists() else None
    rows[name] = {"face": face, "want": want, "match": (face == want) if want and face else None}
    print(name, face, "WANT", want, "MATCH" if rows[name]["match"] else ("SET" if want is None else "DRIFT"))

json.dump(rows, open(BASE / "evidence" / "s183_gdx" / "S183_GATES.json", "w"), indent=1)
print("saved")
