#!/usr/bin/env python3
"""s152_probe5.py — S152 wave: interactive tap probes on the 5 S151
REAL_APP_CONTENT programs (kiss / diary / tickmate / better.alarm /
transistor). Each app: one scripted canonical tap (540,960) at mid-run,
then verdict + frame-face pre/post-tap comparison + UI-EVENT dispatch
record. Law: every row keeps its raw evidence trail; a tap that dispatches
but renders no face change is recorded as DISPATCH_NO_FACECHANGE, not
passed off as a click.

Usage: s152_probe5.py <name ...>   (default: all five)
Output: evidence/s152/PROBE5.json (merge-safe: skips already-recorded rows)
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

BASE = Path("/home/z/my-project")
BIN = BASE / "miniandroid/build/miniandroid"
OUT = BASE / "run/s152"
EV = BASE / "evidence/s152/PROBE5.json"

APPS = {
    "kiss": {
        "pkg": "fr.neamar.kiss", "vc": "224",
        "apk": "upload/s151_internet_batch/fr.neamar.kiss_224.apk",
        "tap": "540,960@15",
    },
    "diary": {
        "pkg": "org.billthefarmer.diary", "vc": "1105",
        "apk": "upload/s151_internet_batch/org.billthefarmer.diary_1105.apk",
        # FAB ImageButton (view_tree: x=954 y=1794 w=126 h=126) -> center
        "tap": "1017,1857@15",
    },
    "tickmate": {
        "pkg": "de.smasi.tickmate", "vc": "50",
        "apk": "upload/s151_internet_batch/de.smasi.tickmate_50.apk",
        "tap": "540,960@15",
    },
    "better.alarm": {
        "pkg": "com.better.alarm", "vc": "31504",
        "apk": "upload/s151_internet_batch/com.better.alarm_31504.apk",
        "tap": "540,400@15",
    },
    "transistor": {
        "pkg": "org.y20k.transistor", "vc": "117",
        "apk": "upload/s151_internet_batch/org.y20k.transistor_117.apk",
        # ImageButton (view_tree: x=912 y=483 w=168 h=168) -> center
        "tap": "996,567@15",
    },
}

VERDICT_RE = re.compile(r"FRAME_ANALYSIS state=(\S+)")


def sha16(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def frame_faces(run_dir, limit=30):
    faces = {}
    fdir = run_dir / "frames"
    if fdir.is_dir():
        for f in sorted(fdir.glob("frame_*.png")):
            m = re.search(r"frame_(\d+)", f.name)
            if m:
                idx = int(m.group(1))
                if idx < limit:
                    faces[idx] = sha16(f)
    return faces


def run_probe(name, cfg):
    # S151 batch law: data-root = store/data (app at store/data/data/app/<pkg>)
    store = BASE / "evidence/s151_trains" / f"store_{cfg['pkg']}_{cfg['vc']}" / "data"
    if not store.is_dir():
        subprocess.run(
            [str(BIN), "install", str(BASE / cfg["apk"]),
             "--data-root", str(store)],
            capture_output=True, timeout=300)
    rundir = OUT / f"probe_{name}"
    console = OUT / f"probe_{name}_console.log"
    cmd = [
        str(BIN), "run", "--execution-mode", "real-dalvik",
        "--package", cfg["pkg"], "--data-root", str(store),
        "-o", str(rundir), "--max-seconds", "110", "--frames", "30",
        "--trace", "--tap", cfg["tap"],
    ]
    with open(console, "w") as cf:
        subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT, timeout=150)
    text = console.read_text(errors="replace")
    verdict = None
    for m in VERDICT_RE.finditer(text):
        verdict = m.group(1)
    shot = rundir / "screenshot.png"
    face = sha16(shot) if shot.is_file() else None
    faces = frame_faces(rundir)
    tap_frame = int(cfg["tap"].split("@")[1])
    pre = faces.get(tap_frame - 1) or faces.get(tap_frame - 2)
    post = faces.get(tap_frame + 1) or faces.get(tap_frame + 2) or faces.get(tap_frame + 3)
    ui_events = re.findall(
        r"\[UI-EVENT\] event=TOUCH action=(\d+)[^\n]*", text)
    consumed = re.findall(
        r"\[UI-EVENT\] event=TOUCH action=\d+ result=(\S+) consumed=(\S+)",
        text)
    f117 = re.findall(r"\[F117-TAP\] frame \d+ (DOWN|UP) \(([^)]*)\) target=(\d+)", text)
    uncaught = len(re.findall(r"EXC-UNCAUGHT-TOP", text))
    # CLICK dispatch = the REAL app listener ran (PerformClick -> DEX
    # onClick -> [UI-EVENT] event=CLICK ... result=DISPATCHED). This is
    # the strongest per-row signal — stronger than the DOWN/UP bookkeeping.
    click_dispatch = re.findall(
        r"\[UI-EVENT\] event=CLICK view_object=(\d+) view_class=(\S+);\s*"
        r"listener=(\d+) listener_class=(\S+);", text)
    click_results = re.findall(
        r"\[UI-EVENT\] event=CLICK result=(\S+) listener=(\S+)", text)
    if not f117:
        tap_state = "NO_DISPATCH"
    else:
        down_ok = any(ph == "DOWN" and tgt != "0" for ph, _, tgt in f117)
        up_ok = any(ph == "UP" for ph, _, tgt in f117)
        cons = any(c == "true" for _, c in consumed)
        clicked = any(r == "DISPATCHED" for r, _ in click_results)
        if clicked:
            tap_state = "CLICK_DISPATCHED"
        elif down_ok and up_ok and cons:
            tap_state = "DOWN_UP_CONSUMED"
        elif down_ok and up_ok:
            tap_state = "DOWN_UP_NOT_CONSUMED"
        elif down_ok:
            tap_state = "DOWN_ONLY" + ("_CONSUMED" if cons else "")
        else:
            tap_state = "DOWN_MISS"
    face_changed = bool(pre and post and pre != post)
    if face_changed and tap_state in (
            "CLICK_DISPATCHED", "DOWN_UP_CONSUMED", "DOWN_UP_NOT_CONSUMED"):
        row_state = "TAP_EFFECT_RENDERED"
    elif tap_state == "CLICK_DISPATCHED":
        row_state = "CLICK_DISPATCHED_NO_FACECHANGE"
    else:
        row_state = tap_state
    return {
        "apk": cfg["apk"],
        "package": cfg["pkg"],
        "tap": cfg["tap"],
        "verdict": verdict,
        "face": face,
        "face_pre_tap": pre,
        "face_post_tap": post,
        "face_changed": face_changed,
        "tap_state": tap_state,
        "row_state": row_state,
        "click_dispatch": [
            {"view": v, "view_class": vc, "listener": l, "listener_class": lc}
            for v, vc, l, lc in click_dispatch],
        "click_results": [{"result": r, "listener": l} for r, l in click_results],
        "f117_events": [{"phase": p, "xy": xy, "target": t} for p, xy, t in f117],
        "ui_event_actions": ui_events,
        "results": [{"action_result": r, "consumed": c} for r, c in consumed],
        "uncaught": uncaught,
        "frames": {str(k): v for k, v in sorted(faces.items())},
    }


def main():
    names = sys.argv[1:] or list(APPS)
    EV.parent.mkdir(parents=True, exist_ok=True)
    data = {"rows": {}}
    if EV.is_file():
        data = json.loads(EV.read_text())
    for name in names:
        cfg = APPS[name]
        key = f"{cfg['pkg']}_{cfg['vc']}"
        if key in data["rows"]:
            print(f"{name}: already recorded — skip")
            continue
        print(f"{name}: probing ...", flush=True)
        try:
            row = run_probe(name, cfg)
        except subprocess.TimeoutExpired:
            row = {"apk": cfg["apk"], "package": cfg["pkg"],
                   "tap": cfg["tap"], "row_state": "RUN_TIMEOUT",
                   "verdict": None, "face": None}
        data["rows"][key] = row
        print(f"{name}: {row.get('row_state')} verdict={row.get('verdict')} "
              f"face={row.get('face')} pre={row.get('face_pre_tap')} "
              f"post={row.get('face_post_tap')}")
        EV.write_text(json.dumps(data, indent=1, ensure_ascii=False))
    print(f"evidence -> {EV}")


if __name__ == "__main__":
    main()
