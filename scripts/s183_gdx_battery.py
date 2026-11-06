#!/usr/bin/env python3
"""s183_gdx_battery.py — re-run the libGDX family on the B1 host-native binary.
Titles: emmanuelttt (#11 real APK), stacktower3d, bouncy. Fresh store each.
Evidence: evidence/s183_gdx/S183_GDX.json"""
import json, os, re, subprocess, sys, time, shutil
from pathlib import Path

BASE = Path("/home/z/my-project")
sys.path.insert(0, str(BASE / "scripts"))
import s165_trains as t  # ensure_store / sha16 helpers
import s166_trains as s166

BIN = BASE / "miniandroid" / "build" / "miniandroid"
OUT = BASE / "run_s183_gdx"
EJSON = BASE / "evidence" / "s183_gdx" / "S183_GDX.json"
OUT.mkdir(parents=True, exist_ok=True)
(EJSON.parent).mkdir(parents=True, exist_ok=True)

TITLES = [
    ("emmanuelttt", "upload/canonical_apks/com.emmanuelmess.tictactoe_3.apk", 45),
    ("stacktower3d", "upload/canonical_apks/stack.tower3d_1.apk", 45),
    ("bouncy", "upload/canonical_apks/com.dozingcatsoftware.bouncy_43.apk", 45),
]

def discover_pkg(apk, store):
    store.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(BIN), "install", str(apk), "--data-root", str(store)],
                   capture_output=True, timeout=600)
    apps = store / "data" / "app"
    if apps.exists():
        ds = [d.name for d in apps.iterdir() if d.is_dir()
              and not d.name.startswith(".")]
        if ds:
            return ds[0]
    return None

rows = {}
if EJSON.exists():
    rows = json.load(open(EJSON))

for name, apk_rel, secs in TITLES:
    apk = BASE / apk_rel
    store = OUT / f"store_{name}"
    if store.exists():
        shutil.rmtree(store)
    pkg = discover_pkg(apk, store)
    if not pkg or not t.ensure_store(apk, store, BIN, pkg):
        rows[name] = {"tag": name, "class": "INSTALL_FAIL"}
        json.dump(rows, open(EJSON, "w"), indent=1, default=str)
        continue
    for k in s166.CLEAN_ENVS:
        os.environ.pop(k, None)
    rundir = OUT / name
    console = OUT / f"{name}.err"
    cmd = [str(BIN), "run", "--execution-mode", "real-dalvik",
           "--data-root", str(store), "-o", str(rundir),
           "--max-seconds", str(secs), "--frames", "5",
           "--trace", "--package", pkg]
    t0 = time.time()
    with open(console, "w") as cf:
        subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                       timeout=secs + 120)
    wall = round(time.time() - t0, 1)
    shot = rundir / "screenshot.png"
    text = console.read_text(errors="replace")
    row = {"tag": name, "pkg": pkg, "apk": apk_rel, "wall_s": wall,
           "face": t.sha16(shot) if shot.exists() else None,
           "uncaught": len(re.findall(r"UNCAUGHT", text)),
           "gdx_host": len(re.findall(r"GDX-HOST\] .*LOADED", text)),
           "host_refused": len(re.findall(r"host-native .* also refused", text)),
           "gl_surf": len(re.findall(r"GLSurfaceView|createGLSurfaceView", text)),
           "gles20_calls": len(re.findall(r"GLES20", text)),
           "freetype_calls": len(re.findall(r"FreeType|freetype", text)),
           "checkgl": len(re.findall(r"checkGL20|reqGlEsVersion|requires OpenGL", text)),
           }
    ts = rundir / "trace_summary.json"
    if ts.exists():
        try:
            tj = json.load(open(ts))
            row["app_px"] = tj.get("app_owned_pixels")
            row["colors"] = tj.get("unique_colors")
        except Exception:
            pass
    m = re.search(r"UNCAUGHT[^\n]*", text)
    row["first_exc"] = (m.group(0)[:260] if m else None)
    rows[name] = row
    json.dump(rows, open(EJSON, "w"), indent=1, default=str)
    print(name, json.dumps(row)[:400])

print("saved", EJSON)
