#!/usr/bin/env python3
"""s181_minimal_battery.py — S181: the user's minimal-app challenge.

«10 تا برنامه بازی ساده native خیلی کم‌حجم تست کن، ببینم مشکل کجاست» +
3 user-named APKs (terminightor_12, just24hoursplus_10400, tangram_90001).

For EVERY title: fresh store, real-dalvik run, then DEEP failure forensics
— trace_summary.first_failure_event / first_divergence / last_exception,
first UNCAUGHT stack from the console, and a subsystem keyword census
(font / bitmap-graphics / layout-inflate / webview / sqlite-room /
provider-service / compose) so the recurring BASIC blocker can be named.
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
OUT = BASE / "run_s181_minimal"
OUT.mkdir(parents=True, exist_ok=True)
EVID = BASE / "evidence/s181_minimal"
EVID.mkdir(parents=True, exist_ok=True)
EJSON = EVID / "S181_MINIMAL.json"

TITLES = {
    # ---- 10 smallest/simple corpus titles (native, mostly never measured) --
    "opmt": ("upload/canonical_apks/opmt_v0.1.2_vc1.apk", None, 45),
    "unote": ("upload/canonical_apks/app.varlorg.unote_30.apk", None, 60),
    "fishrings": ("upload/canonical_apks/fishrings_v1.23_vc6.apk", None, 45),
    "tripeaks": ("upload/canonical_apks/tripeaks_v1.2.1_vc4.apk", None, 45),
    "balance": ("upload/fdroid_batch/com.ashkanrafiee.balance_29000.apk",
                None, 60),
    "stopwatch": ("upload/canonical_apks/com.github.muellerma.stopwatch_6.apk",
                  None, 60),
    "bmi": ("upload/cont11_apks/bmi_402.apk", None, 60),
    "sunpiano": ("upload/fdroid_batch/code.alimiracle.sunpiano_2.apk",
                 None, 45),
    "sopadeletras": ("upload/fdroid_batch/app.sopadeletras_24.apk",
                     None, 45),
    "sparkledns": ("upload/fdroid_batch/cc.skysparkle.sparkledns_10006.apk",
                   None, 60),
    # ---- the 3 user-named APKs (exact pinned versions, fetched today) ----
    "terminightor": ("upload/fdroid_batch/org.schabi.terminightor_12.apk",
                     None, 60),
    "just24hours": ("upload/fdroid_batch/com.chancehorizon.just24hoursplus_10400.apk",
                    None, 60),
    "tangram": ("upload/fdroid_batch/com.xmission.trevin.android.tangram_90001.apk",
                None, 60),
}

SUBSYS = {
    "font": r"Typeface|TextShaper|font_family|createFromAsset|FontFamily",
    "graphics": r"Bitmap|BitmapFactory|Canvas|drawable|Drawable|decode|Surface|shader",
    "layout": r"Inflater|inflate|LayoutTras|setContentView|measure|layout_nodes|XMLLoader",
    "webview": r"WebView|webkit|loadUrl",
    "db": r"SQLite|sqlite|Room|Cursor|Database",
    "provider": r"ContentProvider|onCreate.*Provider|FirebaseInit|WorkManagerInit|App Startup",
    "compose": r"Compose|Recomposer|ViewRootImpl.*compose|Snapshot",
    "missing_class": r"NoDefinitionFoundException|ClassNotFoundException",
    "native": r"UnsatisfiedLink|JNI.*ERROR|dlopen|System.loadLibrary",
}


def discover_pkg(apk, store):
    store.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([str(BIN), "install", str(apk), "--data-root",
                        str(store)], capture_output=True, timeout=600)
    apps = store / "data" / "app"
    if apps.exists():
        ds = [d.name for d in apps.iterdir() if d.is_dir()]
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


def run_title(name, apk_rel, pkg, secs, rows):
    apk = BASE / apk_rel
    store = OUT / f"store_{name}"
    if pkg is None:
        pkg = discover_pkg(apk, store)
        if pkg is None:
            rows[name] = {"class": "INSTALL_FAIL"}
            return
    if not t.ensure_store(apk, store, BIN, pkg):
        rows[name] = {"class": "INSTALL_FAIL"}
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
    row = {"tag": name, "pkg": pkg, "apk": apk_rel, "wall_s": wall,
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
            row["first_divergence"] = s.get("first_divergence")
            row["last_exception"] = s.get("last_exception")
            row["severity_census"] = s.get("severity_census")
            row["stages_tail"] = [x.get("stage") if isinstance(x, dict)
                                  else str(x)[:40]
                                  for x in (s.get("stages") or [])[-4:]]
        except Exception as e:
            row["trace_err"] = str(e)[:120]
    row["first_stack"] = first_uncaught_block(text)
    row["subsys_census"] = census(text)
    # classification
    if "REAL_APP_CONTENT" in str(row.get("verdict")):
        row["class"] = "REAL_APP_CONTENT"
    elif row.get("face") is None:
        row["class"] = "NO_FRAME"
    else:
        row["class"] = "PARTIAL"
    rows[name] = row
    json.dump(rows, open(EJSON, "w"), indent=1, default=str)
    keep = ["class", "verdict", "face", "uncaught", "app_owned_pixels",
            "final_state"]
    print(f"--- {name} ({pkg}): " + json.dumps(
        {k: row.get(k) for k in keep if k in row}, default=str)[:280],
        flush=True)
    if row.get("first_failure_event"):
        print(f"    first_failure: {json.dumps(row['first_failure_event'], default=str)[:300]}",
              flush=True)
    if row.get("first_stack"):
        print(f"    first_stack: {row['first_stack'][:300]}", flush=True)
    if row.get("subsys_census"):
        print(f"    subsys: {row['subsys_census']}", flush=True)


if __name__ == "__main__":
    only = sys.argv[1:] or list(TITLES)
    rows = {}
    if EJSON.exists():
        rows = json.load(open(EJSON))
    for name in only:
        apk_rel, pkg, secs = TITLES[name]
        run_title(name, apk_rel, pkg, secs, rows)
    print("\n== S181 minimal battery ==")
    for k, v in rows.items():
        print(f"{k:14s} {str(v.get('class')):18s} "
              f"verdict={v.get('verdict')} uncaught={v.get('uncaught')} "
              f"px={v.get('app_owned_pixels')}")
