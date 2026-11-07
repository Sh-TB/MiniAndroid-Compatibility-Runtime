#!/usr/bin/env python3
"""s186_stuck_battery.py — S186 (Coder-4 W13): the stuck-corpus battery.

User directive (2026-11-06): «in our own GitHub many games/programs are
stuck at ONE stage — find the libraries they need, apply them, then see
how much progress they make». This battery measures the BASELINE (current
main binary) for every stuck title, with the full trace so the blocking
library call can be decoded per title.

Gates (byte-inertness law): microtimer + opencalc + dooz settle.
Stuck targets: the S181 Family-1/2/3 failures + the theme-background-only
corpus (Coder-2 trackers #477-#491) — all pure-Java/Kotlin titles, no
native .so dependency (the directive's filter: apps that need LIBRARIES,
not natives).

Tier (argv[1]): gates | stuck | all.  Store/OUT under run_s186/.
Evidence: evidence/s186_stuck/S186_STUCK.json (incremental).
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
import s166_trains as s166

BIN = BASE / "miniandroid/build/miniandroid"
OUT = BASE / "run_s186"
OUT.mkdir(parents=True, exist_ok=True)
EVID = BASE / "evidence/s186_stuck"
EVID.mkdir(parents=True, exist_ok=True)
EJSON = EVID / "S186_STUCK.json"

GATES = {
    "microtimer": dict(apk="upload/canonical_apks/dubrowgn.microtimer_8.apk",
                       pkg="dubrowgn.microtimer", secs=60, frames=4,
                       want_face="bbd350b6c14fbd52"),
    "opencalc": dict(apk="upload/opencalculator_53.apk",
                     pkg="com.darkempire78.opencalculator", secs=60, frames=4,
                     want_face="63020bc7334048fe"),
    "dooz": dict(apk="upload/canonical_apks/io.github.yamin8000.dooz_23.apk",
                 pkg="io.github.yamin8000.dooz", secs=240, frames=4,
                 want_face="a0fae9072313e2d1"),
}

STUCK = {
    # ---- S181 Family 2: androidx lifecycle/coroutines clinit NPE storms --
    "sunpiano": dict(apk="upload/fdroid_batch/code.alimiracle.sunpiano_2.apk",
                     pkg="code.alimiracle.sunpiano", secs=60, frames=6),
    "sopadeletras": dict(apk="upload/fdroid_batch/app.sopadeletras_24.apk",
                         pkg="app.sopadeletras", secs=60, frames=6),
    # ---- S181 Family 1: Compose runtime init ----
    "sparkledns": dict(apk="upload/fdroid_batch/cc.skysparkle.sparkledns_10006.apk",
                       pkg="cc.skysparkle.sparkledns", secs=60, frames=6),
    "stopwatch": dict(apk="upload/fdroid_batch/com.github.muellerma.stopwatch_6.apk",
                      pkg="com.github.muellerma.stopwatch", secs=60, frames=6),
    # ---- theme-background-only corpus (Coder-2 trackers, stuck at ONE
    #      stage: theme color paints, app content never draws) ----
    "freebloks": dict(apk="upload/fdroid_batch/de.saschahlusiak.freebloks_184.apk",
                      pkg="de.saschahlusiak.freebloks", secs=90, frames=6),
    "pfdicer": dict(apk="upload/fdroid_batch/org.secuso.privacyfriendlydicer_101.apk",
                    pkg="org.secuso.privacyfriendlydicer", secs=90, frames=6),
    "itsfrz_ttt": dict(apk="upload/fdroid_batch/com.itsfrz.tictactoe_5.apk",
                       pkg="com.itsfrz.tictactoe", secs=90, frames=6),
    "openlauncher": dict(apk="upload/fdroid_batch/com.benny.openlauncher_39.apk",
                         pkg="com.benny.openlauncher", secs=90, frames=6),
    "notes": dict(apk="upload/fdroid_batch/org.billthefarmer.notes_139.apk",
                  pkg="org.billthefarmer.notes", secs=90, frames=6),
    "lexica": dict(apk="upload/fdroid_batch/com.serwylo.lexica_30018.apk",
                   pkg="com.serwylo.lexica", secs=90, frames=6),
    "antimine": dict(apk="upload/fdroid_batch/dev.lucanlm.antimine_1706031.apk",
                     pkg="dev.lucanlm.antimine", secs=90, frames=6),
}

SUBSYS = {
    "compose": r"Compose|Recomposer|ViewRootImpl.*compose|Snapshot|AbstractComposeView",
    "lifecycle": r"Lifecycle|lifecycle|ViewModel|ViewModelStore",
    "missing_class": r"NoDefinitionFoundException|ClassNotFoundException",
    "npe": r"NullPointerException",
    "native": r"UnsatisfiedLink|dlopen|System\.loadLibrary",
}


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


def first_uncaught(text, span=8):
    """The first UNCAUGHT/EXCEPTION window, with 3 lines of context before."""
    lines = text.splitlines()
    for i, l in enumerate(lines):
        if "UNCAUGHT" in l:
            ctx = lines[max(0, i - 3):i + span]
            return " | ".join(ctx)[:700]
    for i, l in enumerate(lines):
        if "[FRONTIER]" in l:
            ctx = lines[max(0, i - 3):i + span]
            return " | ".join(ctx)[:700]
    return None


def census(text):
    out = {}
    for k, pat in SUBSYS.items():
        n = len(re.findall(pat, text))
        if n:
            out[k] = n
    return out


def app_run(name, spec):
    for k in s166.CLEAN_ENVS:
        os.environ.pop(k, None)
    apk = BASE / spec["apk"]
    pkg = spec["pkg"]
    store = OUT / f"store_{name}"
    if pkg is None:
        pkg = discover_pkg(apk, store)
        if pkg is None:
            return {"tag": name, "class": "INSTALL_FAIL"}
        spec["pkg"] = pkg
    assert t.ensure_store(apk, store, BIN, pkg), f"install fail {name}"
    rundir = OUT / name
    console = OUT / f"{name}.err"
    cmd = [str(BIN), "run", "--execution-mode", "real-dalvik",
           "--data-root", str(store), "-o", str(rundir),
           "--max-seconds", str(spec["secs"]), "--frames", str(spec["frames"]),
           "--trace", "--package", pkg]
    t0 = time.time()
    with open(console, "w") as cf:
        subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                       timeout=spec["secs"] + 120)
    wall = round(time.time() - t0, 1)
    shot = rundir / "screenshot.png"
    text = console.read_text(errors="replace")
    row = {
        "tag": name, "pkg": pkg, "bin": t.sha16(BIN), "wall_s": wall,
        "face": t.sha16(shot) if shot.exists() else None,
        "uncaught": len(re.findall(r"UNCAUGHT", text)),
        "ndfe": len(re.findall(r"NoDefinitionFoundException", text)),
        "frames": re.findall(r"Frames Rendered: (\d+)", text)[-1:],
        "first_stack": first_uncaught(text),
        "subsys": census(text),
    }
    ts = rundir / "trace_summary.json"
    if ts.exists():
        try:
            s = json.load(open(ts))
            fa = s.get("frame_analysis") or {}
            row["verdict"] = fa.get("verdict")
            row["app_owned_pixels"] = fa.get("app_owned_pixels")
            row["app_draw_ops"] = fa.get("app_draw_ops")
            row["unique_colors"] = fa.get("unique_colors")
            row["final_state"] = (s.get("lifecycle") or {}).get("final_state")
        except Exception:
            pass
    want = spec.get("want_face")
    if want:
        row["pin"] = want
        row["pin_match"] = (row.get("face") or "").startswith(want[:8])
    return row


def classify(row):
    if row.get("class") == "INSTALL_FAIL":
        return
    v = row.get("verdict") or ""
    px = row.get("app_owned_pixels") or 0
    if row.get("pin_match"):
        row["class"] = "PIN_MATCH"
    elif "REAL_APP_CONTENT" in v or px > 50000:
        row["class"] = "REAL_APP_CONTENT"
    elif px > 0:
        row["class"] = "PARTIAL_" + v
    else:
        row["class"] = v or "NO_FRAME"


def save_rows(rows):
    json.dump(rows, open(EJSON, "w"), indent=1, default=str)


def main():
    tier = sys.argv[1] if len(sys.argv) > 1 else "all"
    rows = json.loads(EJSON.read_text()) if EJSON.exists() else {}
    todo = {}
    if tier in ("gates", "all"):
        todo.update(GATES)
    if tier in ("stuck", "all"):
        todo.update(STUCK)
    for name, spec in todo.items():
        if name in rows and rows[name].get("bin") == t.sha16(BIN):
            print(f"[skip] {name} already measured on this binary")
            continue
        print(f"[run ] {name} ({spec['pkg']}) ...", flush=True)
        row = app_run(name, spec)
        classify(row)
        rows[name] = row
        save_rows(rows)
        print(f"       class={row.get('class')} px={row.get('app_owned_pixels')} "
              f"uncaught={row.get('uncaught')} face={row.get('face')}",
              flush=True)
    print(json.dumps({k: {kk: v.get(kk) for kk in
                          ("class", "app_owned_pixels", "uncaught",
                           "face", "pin_match")}
                      for k, v in rows.items()}, indent=1))


if __name__ == "__main__":
    main()
