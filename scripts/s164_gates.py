#!/usr/bin/env python3
"""s164_gates.py — S164: the 10-train gates (5 dooz + 5 Telegram).

Phases:
  anchors   REF (908d5ba6) vs NEW (1cb76138897a22d2) byte-inertness wall:
            microtimer/g2048/opencalc on BOTH binaries, envs OFF. The only
            ungated change is the T4 draw() fallback (arms when onDraw AND
            dispatchDraw both produced 0 ops — the anchor views either
            paint or stay diagnostic).
  dooz_inert  dooz E5 on NEW with envs OFF: face must stay 11a38a5a
            (byte-inert when no train env is set); wall recorded as the
            D1/D4 baseline on the new binary.
  tg_train    Telegram 90s on NEW with MINIANDROID_APP_DATA_SEED=1 +
            MINIANDROID_PROVIDER_SKIP=FirebaseInitProvider — T2+T3 verdict
            vs the T1 baseline (uncaught census, boot depth, wall).
  dooz_color  dooz E5 60s on NEW with MINIANDROID_SETCOLOR_TRACE=1 —
            full paint-color history for the D3 composite fix.
"""
import json
import os
import sys
from pathlib import Path

BASE = Path("/home/z/my-project")
sys.path.insert(0, str(BASE / "scripts"))
import s154_awaitup_gate as g
import s158_w5_gates as gates
import s164_trains as tr

NEW = BASE / "miniandroid/build/miniandroid"  # 8ffd60cae4125ec5 (T4 v2)
NEW_SHA = "8ffd60cae4125ec5"
OUT = BASE / "run_s164_gates"
OUT.mkdir(parents=True, exist_ok=True)
EVID = BASE / "evidence/s164_trains"

APKS = {
    "microtimer": (gates.MICRO_APK, "dubrowgn.microtimer"),
    "g2048": (gates.G2048_APK, "com.miniandroid.g2048"),
    "opencalc": (BASE / "upload/opencalculator_53.apk",
                 "com.darkempire78.opencalculator"),
}


def merge_evid(name, update):
    out = EVID / name
    rows = {}
    if out.exists():
        try:
            rows = json.load(open(out))
        except Exception:
            rows = {}
    rows.update(update)
    json.dump(rows, open(out, "w"), indent=1)
    print("evidence ->", out)


def clean_env():
    for k in ("MINIANDROID_APP_DATA_SEED", "MINIANDROID_PROVIDER_SKIP",
              "MINIANDROID_SETCOLOR_TRACE", "MINIANDROID_S109_BITMAP"):
        os.environ.pop(k, None)


def phase_anchors():
    clean_env()
    gates.OUT = OUT
    rows, out = {}, {}
    p = EVID / "S164_GATES.json"
    if p.exists():
        rows = json.load(open(p))
        out = rows.get("anchors", {})
    for name, (apk, pkg) in APKS.items():
        pair = {}
        for tag, b in ((f"{name}_ref", gates.REF), (f"{name}_new", NEW)):
            store = OUT / f"store_{name}_{tag}/data"
            pair[tag] = gates.app_run(b, tag, apk, store, pkg,
                                      max_seconds=75)
            print(f"[{tag}] face={pair[tag]['screenshot_face']} "
                  f"wall={pair[tag]['wall_s']}s")
        fr, fw = (pair[f"{name}_ref"]["screenshot_face"],
                  pair[f"{name}_new"]["screenshot_face"])
        pair["delta_inert"] = (fr is not None and fr == fw)
        if name == "microtimer":
            pair["pin_match"] = bool(fw and
                                     fw.startswith(gates.PINS["microtimer"]))
        out[name] = pair
        rows["anchors"] = out
        json.dump(rows, open(p, "w"), indent=1, default=str)
    all_inert = all(v.get("delta_inert") for v in out.values())
    print("ANCHOR WALL:", "PASS" if all_inert else "DRIFT",
          {k: v.get("delta_inert") for k, v in out.items()})
    return all_inert


def phase_dooz_inert(seconds=220):
    clean_env()
    tr.g.BIN = NEW
    rundir = OUT / "dooz_inert"
    console = OUT / "dooz_inert_console.log"
    cmd = [str(NEW), "run", "--execution-mode", "real-dalvik",
           "--data-root", str(tr.DOOZ_STORE), "-o", str(rundir),
           "--max-seconds", str(seconds), "--frames", "30",
           "--trace", "--package", tr.DOOZ_PKG]
    import subprocess, time
    t0 = time.time()
    with open(console, "w") as cf:
        subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                       timeout=seconds + 90)
    wall = round(time.time() - t0, 1)
    text = console.read_text(errors="replace")
    shot = rundir / "screenshot.png"
    row = {
        "bin": NEW_SHA, "env": "OFF",
        "wall_s": wall,
        "settle": wall < seconds - 5,
        "uncaught": len(__import__("re").findall(r"UNCAUGHT", text)),
        "face": g.sha16(shot) if shot.exists() else None,
        "frames": __import__("re").findall(r"Frames Rendered: (\d+)", text),
    }
    merge_evid("S164_GATES.json", {"dooz_inert": row})
    print(json.dumps(row, indent=1))
    return row


def phase_tg_train(seconds=90):
    os.environ.setdefault("MINIANDROID_APP_DATA_SEED", "1")
    # T3 v2: the S164 run lane proved the remaining l9/j escape comes from
    # MlKitInitProvider.onCreate (same Play-Services family) — both init
    # providers get the platform-skip token.
    os.environ.setdefault("MINIANDROID_PROVIDER_SKIP",
                          "FirebaseInitProvider,MlKitInitProvider")
    tr.g.BIN = NEW
    tr.g.OUT = OUT
    import re
    row, text = g.run_case("tg_train_90s", tr.TG_APK, tr.TG_STORE, tap=None,
                           gate_ms=None, frames=8, max_seconds=seconds,
                           package=tr.TG_PKG)
    row["bin"] = "1cb76138897a22d2"
    row["env"] = {"APP_DATA_SEED": 1, "PROVIDER_SKIP": "FirebaseInitProvider"}
    row["uncaught_l9j"] = len(re.findall(r"Ll9/j;", text))
    row["uncaught_tl_autodl"] = len(
        re.findall(r"TL_autoDownloadSettings", text))
    row["seed_rows"] = re.findall(r"\[APP-DATA-SEED\][^\n]{0,120}", text)[:6]
    row["skip_rows"] = re.findall(r"\[S1-PROVIDER\] PLATFORM-SKIP[^\n]{0,140}",
                                  text)
    row["draw_fallback_rows"] = re.findall(
        r"\[C013-DRAW-FALLBACK\][^\n]{0,140}", text)[:8]
    fam = __import__("collections").Counter(
        re.findall(r"UNCAUGHT-TOP\] \[EXC-UNCAUGHT-TOP\] (L\S+);", text))
    row["uncaught_top_families"] = dict(fam.most_common(8))
    row["uncaught_first5"] = re.findall(r"UNCAUGHT[^\n]{0,150}", text)[:5]
    row["frames_rendered"] = re.findall(r"Frames Rendered: (\d+)", text)
    shot = OUT / "tg_train_90s/screenshot.png"
    if shot.exists():
        import shutil
        shutil.copy(shot, EVID / "S164_tg_train_screenshot.png")
        row["face_screenshot"] = g.sha16(shot)
    merge_evid("S164_GATES.json", {"tg_train": row})
    print(json.dumps({k: row.get(k) for k in
                      ("wall_s", "verdict", "uncaught", "uncaught_l9j",
                       "uncaught_tl_autodl", "frames_rendered",
                       "face_screenshot")}, indent=1))
    return row


def phase_dooz_color(seconds=60):
    os.environ["MINIANDROID_SETCOLOR_TRACE"] = "1"
    tr.g.BIN = NEW
    rundir = OUT / "dooz_color"
    console = OUT / "dooz_color_console.log"
    cmd = [str(NEW), "run", "--execution-mode", "real-dalvik",
           "--data-root", str(tr.DOOZ_STORE), "-o", str(rundir),
           "--max-seconds", str(seconds), "--frames", "4",
           "--trace", "--package", tr.DOOZ_PKG]
    import subprocess, time, re
    t0 = time.time()
    with open(console, "w") as cf:
        subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                       timeout=seconds + 90)
    wall = round(time.time() - t0, 1)
    text = console.read_text(errors="replace")
    sc = re.findall(r"\[F298-SETCOLOR\] recv=(\d+) cls=(\S+) color=0x([0-9a-f]+)",
                    text)
    from collections import Counter
    colors = Counter(c for _, _, c in sc)
    nonblack = [(r, c, col) for r, c, col in sc
                if col not in ("ff000000", "00000000")]
    merge_evid("S164_GATES.json", {"dooz_color": {
        "bin": NEW_SHA, "wall_s": wall,
        "setcolor_rows": len(sc),
        "color_hist": dict(colors.most_common(12)),
        "nonblack_first12": nonblack[:12],
        "nonblack_total": len(nonblack),
    }})
    print(f"setcolor rows={len(sc)} nonblack={len(nonblack)}")
    print("hist:", dict(colors.most_common(12)))


def phase_tg_deep(seconds=150, frames=24):
    """T2 exercise: a DEEPER telegram boot (more frames + budget) so the
    k2/k3 runnable wave reaches DownloadController$Preset — the TLRPC
    autoDownloadSettings NPE site the seed law targets."""
    os.environ.setdefault("MINIANDROID_APP_DATA_SEED", "1")
    os.environ.setdefault("MINIANDROID_PROVIDER_SKIP",
                          "FirebaseInitProvider,MlKitInitProvider")
    tr.g.BIN = NEW
    tr.g.OUT = OUT
    import re
    row, text = g.run_case("tg_deep", tr.TG_APK, tr.TG_STORE, tap=None,
                           gate_ms=None, frames=frames, max_seconds=seconds,
                           package=tr.TG_PKG)
    row["bin"] = "1cb76138897a22d2"
    row["env"] = {"APP_DATA_SEED": 1,
                  "PROVIDER_SKIP": "FirebaseInitProvider,MlKitInitProvider"}
    row["seed_rows"] = re.findall(r"\[APP-DATA-SEED\][^\n]{0,140}", text)[:8]
    row["uncaught_tl_autodl"] = len(re.findall(r"TL_autoDownloadSettings", text))
    row["uncaught"] = len(re.findall(r"UNCAUGHT", text))
    row["uncaught_first5"] = re.findall(r"UNCAUGHT[^\n]{0,150}", text)[:5]
    row["synth_exc"] = re.findall(r"\[SYNTH-EXC\][^\n]{0,140}", text)[:6]
    row["frames_rendered"] = re.findall(r"Frames Rendered: (\d+)", text)
    row["run_end"] = re.findall(r"F-NEW-200[^\n]{0,120}", text)[-1:]
    shot = OUT / "tg_deep/screenshot.png"
    if shot.exists():
        import shutil
        shutil.copy(shot, EVID / "S164_tg_deep_screenshot.png")
        row["face_screenshot"] = g.sha16(shot)
    merge_evid("S164_GATES.json", {"tg_deep": row})
    print(json.dumps({k: row.get(k) for k in
                      ("wall_s", "verdict", "uncaught",
                       "uncaught_tl_autodl", "frames_rendered",
                       "face_screenshot")}, indent=1))
    for s in row["seed_rows"][:6]:
        print(" SEED:", s[:130])
    return row


if __name__ == "__main__":
    phase = sys.argv[1] if len(sys.argv) > 1 else "all"
    if phase in ("all", "anchors"):
        phase_anchors()
    if phase in ("all", "dooz_inert"):
        phase_dooz_inert()
    if phase in ("all", "tg_train"):
        phase_tg_train()
    if phase in ("all", "dooz_color"):
        phase_dooz_color()
