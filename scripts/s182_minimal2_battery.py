#!/usr/bin/env python3
"""s182_minimal2_battery.py — S182: the user's 10-tiny-games + 10-simple-apps
battery («۱۰ بازی native خیلی خیلی ریزه میزه + ۱۰ برنامه native خیلی خیلی ساده»).

20 NEVER-MEASURED titles (games and apps separated) + keeps S181's 13 in the
census. Same forensics as S181 (fresh store, real-dalvik, subsystem census,
first-stack, trace_summary failure fields). Incremental JSON so a killed run
resumes: evidence/s182_minimal2/S182_BATTERY.json.

GAMES (10): gmdice, bouncy, aeropayout, uturn, pfdicer, stacktower3d,
            emmanuelttt, awagam, pfsolitaire, pfludo
APPS  (10): librecontactsbackup, quicksettingssoundprofile, lrceditor,
            floatdeck, wocheneinkauf, webstack, textpad, notepad, dmfstasks,
            peri
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
OUT = BASE / "run_s182_minimal2"
OUT.mkdir(parents=True, exist_ok=True)
EVID = BASE / "evidence/s182_minimal2"
EVID.mkdir(parents=True, exist_ok=True)
EJSON = EVID / "S182_BATTERY.json"

TITLES = {
    # ---------------- 10 tiny/easy GAMES ----------------
    "gmdice": ("upload/canonical_apks/de.duenndns.gmdice_8.apk", 40, "game"),
    "bouncy": ("upload/canonical_apks/com.dozingcatsoftware.bouncy_43.apk",
               45, "game"),
    "aeropayout": ("upload/fdroid_batch/com.aeropayout.game_12.apk", 45,
                   "game"),
    "uturn": ("upload/fdroid_batch/ac.stresa.uturn_22.apk", 45, "game"),
    "pfdicer": ("upload/fdroid_batch/org.secuso.privacyfriendlydicer_101.apk",
                45, "game"),
    "stacktower3d": ("upload/canonical_apks/stack.tower3d_1.apk", 45, "game"),
    "emmanuelttt": ("upload/canonical_apks/com.emmanuelmess.tictactoe_3.apk",
                    45, "game"),
    "awagam": ("upload/fdroid_batch/com.awagam.android_5.apk", 45, "game"),
    "pfsolitaire": ("upload/fdroid_batch/org.secuso.privacyfriendlysolitaire_4.apk",
                    45, "game"),
    "pfludo": ("upload/fdroid_batch/org.secuso.privacyfriendlyludo_100.apk",
               45, "game"),
    # ---------------- 10 very simple APPS ----------------
    "librecontactsbackup": (
        "upload/fdroid_batch/com.ashkanrafiee.librecontactsbackup_32.apk",
        60, "app"),
    "quicksettingssound": (
        "upload/fdroid_batch/com.curryplayer.quicksettingssoundprofile_11.apk",
        60, "app"),
    "lrceditor": ("upload/fdroid_batch/com.cg.lrceditor_57.apk", 60, "app"),
    "floatdeck": ("upload/fdroid_batch/app.floatdeck_8.apk", 60, "app"),
    "wocheneinkauf": ("upload/fdroid_batch/app.wocheneinkauf_199.apk", 60,
                      "app"),
    "webstack": ("upload/fdroid_batch/com.chiranth7.webstack_6.apk", 60,
                 "app"),
    "textpad": ("upload/fdroid_batch/com.maxistar.textpad_63.apk", 60, "app"),
    "notepad": ("upload/fdroid_batch/com.nononsenseapps.notepad_72700.apk",
                60, "app"),
    "dmfstasks": ("upload/fdroid_batch/org.dmfs.tasks_82200.apk", 60, "app"),
    "peri": ("upload/fdroid_batch/app.simple.peri_983.apk", 60, "app"),
}

SUBSYS = {
    "font": r"Typeface|TextShaper|font_family|createFromAsset|FontFamily",
    "graphics": r"Bitmap|BitmapFactory|Canvas|drawable|Drawable|decode|Surface|shader",
    "layout": r"Inflater|inflate|LayoutTras|setContentView|measure|layout_nodes|XMLLoader",
    "webview": r"WebView|webkit|loadUrl",
    "db": r"SQLite|sqlite|Room|Cursor|Database",
    "compose": r"Compose|Recomposer|Snapshot",
    "missing_class": r"NoDefinitionFoundException|ClassNotFoundException",
}


def discover_pkg(apk, store):
    store.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([str(BIN), "install", str(apk), "--data-root",
                        str(store)], capture_output=True, timeout=600)
    apps = store / "data" / "app"
    if apps.exists():
        # F-NEW-376 staged promotion leaves a .staging dir behind — skip it
        ds = [d.name for d in apps.iterdir() if d.is_dir()
              and not d.name.startswith(".")]
        if ds:
            return ds[0]
    print("[discover] FAIL", (r.stderr or b"")[-160:].decode(
        errors="replace"))
    return None


def first_uncaught_block(text, span=6):
    m = re.search(r"UNCAUGHT", text)
    if not m:
        m = re.search(r"(?:Exception|Error)[:\s]", text)
    if not m:
        return None
    lines = text[max(0, m.start() - 80):m.start() + 900].splitlines()
    return " | ".join(lines[:span])[:500]


def census(text):
    out = {}
    for k, pat in SUBSYS.items():
        n = len(re.findall(pat, text))
        if n:
            out[k] = n
    return out


def run_title(name, apk_rel, secs, kind, rows):
    apk = BASE / apk_rel
    store = OUT / f"store_{name}"
    pkg = discover_pkg(apk, store)
    if pkg is None or not t.ensure_store(apk, store, BIN, pkg):
        rows[name] = {"tag": name, "kind": kind, "class": "INSTALL_FAIL"}
        json.dump(rows, open(EJSON, "w"), indent=1, default=str)
        return
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
    row = {"tag": name, "kind": kind, "pkg": pkg, "apk": apk_rel,
           "wall_s": wall,
           "face": t.sha16(shot) if shot.exists() else None,
           "uncaught": len(re.findall(r"UNCAUGHT", text)),
           "ndfe": len(re.findall(r"NoDefinitionFoundException", text))}
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
            row["first_failure_event"] = s.get("first_failure_event")
            row["last_exception"] = s.get("last_exception")
        except Exception as e:
            row["trace_err"] = str(e)[:120]
    row["first_stack"] = first_uncaught_block(text)
    row["subsys_census"] = census(text)
    if "REAL_APP_CONTENT" in str(row.get("verdict")):
        row["class"] = "REAL_APP_CONTENT"
    elif row.get("face") is None:
        row["class"] = "NO_FRAME"
    else:
        row["class"] = "PARTIAL"
    rows[name] = row
    json.dump(rows, open(EJSON, "w"), indent=1, default=str)
    keep = ["class", "verdict", "face", "uncaught", "app_owned_pixels",
            "unique_colors", "final_state", "wall_s"]
    print(f"--- [{kind}] {name} ({pkg}): " + json.dumps(
        {k: row.get(k) for k in keep if k in row}, default=str)[:300],
        flush=True)
    if row.get("first_failure_event"):
        print(f"    fail: {json.dumps(row['first_failure_event'], default=str)[:260]}",
              flush=True)
    if row.get("first_stack"):
        print(f"    stack: {row['first_stack'][:260]}", flush=True)


if __name__ == "__main__":
    only = sys.argv[1:] or list(TITLES)
    rows = {}
    if EJSON.exists():
        rows = json.load(open(EJSON))
    for name in only:
        if name in rows and rows[name].get("class") not in (
                None, "INSTALL_FAIL"):
            print(f"== skip {name} (done: {rows[name].get('class')})",
                  flush=True)
            continue
        apk_rel, secs, kind = TITLES[name]
        run_title(name, apk_rel, secs, kind, rows)
    print("\n== S182 battery ==")
    g = [r for r in rows.values() if r.get("kind") == "game"]
    a = [r for r in rows.values() if r.get("kind") == "app"]
    for label, grp in (("GAME", g), ("APP", a)):
        real = sum(1 for r in grp if r.get("class") == "REAL_APP_CONTENT")
        print(f"{label}s: {real}/{len(grp)} REAL_APP_CONTENT")
        for r in grp:
            print(f"  {r.get('tag', '?'):22s} {str(r.get('class')):18s} "
                  f"face={r.get('face')} uncaught={r.get('uncaught')} "
                  f"px={r.get('app_owned_pixels')}")
