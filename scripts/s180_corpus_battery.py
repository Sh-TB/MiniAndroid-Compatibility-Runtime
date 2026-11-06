#!/usr/bin/env python3
"""s180_corpus_battery.py — S180: full-corpus load battery on the CURRENT
main binary (C9+C7, 5d7edcdb34b1502c).

Answers the user's standing question with TODAY's evidence: with all coder
waves merged (88 laws), which titles FULLY load, and has any NEW title
reached REAL_APP_CONTENT vs the historical pins?

Tiers (argv[1]):
  anchors  microtimer + g2048 + opencalc (fast pins)
  dooztg   dooz settle (S156 fresh-store law) + Telegram boot (seed+skip)
  games    the six W8-battery games with their CONT-28/29 face pins
  real     TB / NC / tusky / forkgram (real-world frontiers)
  extra    solitaire + freebloks + memory + klondike (never recently gated)

Classification per title: face sha16, frame_analysis.verdict, uncaught,
ndfe, api_calls. Class = PIN_MATCH / REAL_APP_CONTENT / PARTIAL / NO_FRAME.
Evidence: evidence/s180_battery/S180_BATTERY.json (incremental).
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
OUT = BASE / "run_s180_battery"
OUT.mkdir(parents=True, exist_ok=True)
EVID = BASE / "evidence/s180_battery"
EVID.mkdir(parents=True, exist_ok=True)
EJSON = EVID / "S180_BATTERY.json"

# want_face = historical pinned face (8-16 hex); want_cls = standing class
TITLES = {
    # ---- anchors (standing full loads) ----
    "microtimer": dict(apk="upload/canonical_apks/dubrowgn.microtimer_8.apk",
                       pkg="dubrowgn.microtimer", secs=60, frames=4,
                       want_face="bbd350b6c14fbd52"),
    "g2048": dict(apk="upload/s80_games/build_2048/g2048_v1.0_vc1.apk",
                  pkg="com.miniandroid.g2048", secs=40, frames=4,
                  want_face="f43face08299ffc6"),
    "opencalc": dict(apk="upload/opencalculator_53.apk",
                     pkg="com.darkempire78.opencalculator", secs=60, frames=4,
                     want_face="63020bc7334048fe"),
    # ---- the six W8-battery games (pins from CONT-28/29 battery law) ----
    "tetris": dict(apk="upload/s80_games/build_tetris/tetris_v1.0_vc1.apk",
                   pkg="com.miniandroid.tetris", secs=30, frames=5,
                   want_face="b818a6a7"),
    "snake_deluxe": dict(
        apk="upload/s80_games/build_sd/snake_deluxe_v1.0_vc1.apk",
        pkg="com.miniandroid.snakedeluxe", secs=30, frames=5,
        want_face="5235683f"),
    "snakeneon": dict(
        apk="upload/s98_games/build_snakeneon/snakeneon_v1.0_vc1.apk",
        pkg="com.miniandroid.snakeneon", secs=30, frames=5,
        want_face="b669ce89"),
    "ttt_deluxe": dict(
        apk="upload/s83_games/build_ttt/tictactoe_deluxe_v1.0_vc1.apk",
        pkg="com.miniandroid.tictactoedeluxe", secs=30, frames=5,
        want_face="db1d633d"),
    "minicraft": dict(
        apk="upload/s86_games/build_minicraft/minicraft_v1.0_vc1.apk",
        pkg="com.miniandroid.minicraft", secs=40, frames=5,
        want_face="e77a073f"),
    "gmdice": dict(apk="upload/canonical_apks/de.duenndns.gmdice_8.apk",
                   pkg="de.duenndns.gmdice", secs=30, frames=5,
                   want_face="3891679d"),
    # ---- settle/boot laws run via s166_trains (dooz / tg) ----
    "dooz": dict(apk="upload/canonical_apks/dooz_23_toplevel.apk",
                 pkg=None, secs=240, frames=4,
                 want_face="a0fae9072313e2d1"),
    "tg": dict(apk="upload/telegram_official.apk", pkg=None, secs=90,
               frames=8, want_face=None),
    # ---- real-world frontiers ----
    "tb": dict(apk="upload/net.thunderbird.android_33.apk",
               pkg="net.thunderbird.android", secs=90, frames=4,
               want_face="43bfdac6023cba66"),
    "nc": dict(apk="upload/com.nextcloud.client_350000290.apk",
               pkg="com.nextcloud.client", secs=90, frames=4,
               want_face="33fd925fc12e7585"),
    "tusky": dict(apk="upload/com.keylesspalace.tusky_145.apk",
                  pkg="com.keylesspalace.tusky", secs=90, frames=4,
                  want_face="31ddd4d5"),
    "forkgram": dict(apk="upload/forkgram_709208.apk", pkg=None, secs=90,
                     frames=4, want_face=None),
    # ---- never-recently-gated games ----
    "solitaire": dict(apk="upload/cont50_apks/de.tobiasbielefeld.solitaire_71.apk",
                      pkg="de.tobiasbielefeld.solitaire", secs=40, frames=5,
                      want_face=None),
    "freebloks": dict(apk="upload/canonical_apks/de.saschahlusiak.freebloks_184.apk",
                      pkg="de.saschahlusiak.freebloks", secs=40, frames=5,
                      want_face=None),
    "memory": dict(apk="upload/canonical_apks/org.secuso.privacyfriendlymemory_100.apk",
                   pkg="org.secuso.privacyfriendlymemory", secs=40, frames=5,
                   want_face=None),
    "klondike": dict(apk="upload/klondike_veldsoft_3.apk", pkg=None, secs=40,
                     frames=5, want_face=None),
}

TIERS = {
    "anchors": ["microtimer", "g2048", "opencalc"],
    "dooztg": [],  # special-cased via s166 laws
    "games": ["tetris", "snake_deluxe", "snakeneon", "ttt_deluxe",
              "minicraft", "gmdice"],
    "real": ["tb", "nc", "tusky", "forkgram"],
    "extra": ["solitaire", "freebloks", "memory", "klondike"],
}


def load_rows():
    if EJSON.exists():
        return json.load(open(EJSON))
    return {}


def save_rows(rows):
    json.dump(rows, open(EJSON, "w"), indent=1, default=str)


def discover_pkg(apk, store):
    """Install once, learn the package from data/app/<pkg>/base.apk."""
    store.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([str(BIN), "install", str(apk), "--data-root",
                        str(store)], capture_output=True, timeout=600)
    apps = store / "data" / "app"
    if apps.exists():
        ds = [d.name for d in apps.iterdir() if d.is_dir()]
        if ds:
            return ds[0]
    print("[discover] FAIL", (r.stderr or b"")[-200:].decode(
        errors="replace"))
    return None


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
            row["dominant"] = fa.get("dominant_color")
            row["dominant_pct"] = fa.get("dominant_pct")
            row["final_state"] = (s.get("lifecycle") or {}).get("final_state")
        except Exception:
            pass
    at = rundir / "api_trace.json"
    if at.exists():
        try:
            row["api_calls"] = json.load(open(at)).get("total_calls")
        except Exception:
            pass
    return row


def classify(row, spec):
    if row.get("class") in ("INSTALL_FAIL",):
        return row["class"]
    want = spec.get("want_face") or ""
    face = row.get("face") or ""
    if want and face.startswith(want[:8]):
        return "PIN_MATCH"
    if "REAL_APP_CONTENT" in str(row.get("verdict")):
        return "REAL_APP_CONTENT"
    if not face:
        return "NO_FRAME"
    return "PARTIAL"


def run_title(name, row_out):
    spec = TITLES[name]
    print(f"=== {name} ({spec['apk']}) pkg={spec['pkg']}", flush=True)
    if name == "dooz":
        row = s166.dooz_run("s180_dz", BIN, budget=240, store_root=OUT)
        row["tag"] = "dooz"
        row["face"] = row.get("face")
    elif name == "tg":
        row = s166.tg_run("s180_tg", BIN, store_name="s180_tg_store")
        row["tag"] = "tg"
    else:
        row = app_run(name, spec)
    row["class"] = classify(row, spec)
    prev = row_out.get(name, {}).get("class") if name in row_out else None
    row["prev_class_this_session"] = prev
    row_out[name] = row
    save_rows(row_out)
    keep = ["face", "verdict", "class", "uncaught", "ndfe", "wall_s",
            "app_owned_pixels", "final_state", "api_calls", "pkg",
            "settle", "rss_peak_mb"]
    print(f"--- {name}: " + json.dumps(
        {k: row.get(k) for k in keep if k in row}, default=str)[:400],
        flush=True)


if __name__ == "__main__":
    tier = sys.argv[1]
    rows = load_rows()
    if tier == "dooztg":
        for name in ("dooz", "tg"):
            run_title(name, rows)
    else:
        for name in TIERS[tier]:
            run_title(name, rows)
    # tier summary
    print(f"\n== S180 battery tier '{tier}' ==")
    for k, v in rows.items():
        print(f"{k:12s} {str(v.get('class')):18s} face={v.get('face')} "
              f"verdict={v.get('verdict')} uncaught={v.get('uncaught')}")
