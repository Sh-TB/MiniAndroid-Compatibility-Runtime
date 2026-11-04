#!/usr/bin/env python3
"""s164_trains.py — S164: the 10-train run lane (5 dooz + 5 Telegram).

User directive: bring 5 dooz trains and 5 Telegram trains to destination,
10 verified achievements, apps must LOAD FASTER and run LIGHTER.

Phases (invoked by argv[1]):
  tg_baseline  T1 — Telegram 90s cold start on the S163 store (no
               reinstall), full blocker census (l9/j Firebase family,
               TLRPC autoDownloadSettings NPE, paint rows).
  dooz_diag    D2 — dooz E5 60s with MINIANDROID_S109_BITMAP=1: dump the
               replayed drawText colors + EXP092-COPY fb census. Answers
               WHY the 1468-op Lt4 paint lands as a uniform dark cover.
Everything reuses the s154 harness verbatim (install/run_case/sha16).
"""
import json
import os
import re
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

BASE = Path("/home/z/my-project")
sys.path.insert(0, str(BASE / "scripts"))
import s154_awaitup_gate as g

g.BIN = BASE / "miniandroid/build/miniandroid"
g.OUT = BASE / "run_s164_trains"
g.OUT.mkdir(parents=True, exist_ok=True)
EVID = BASE / "evidence/s164_trains"
EVID.mkdir(parents=True, exist_ok=True)

TG_APK = BASE / "upload/telegram_official.apk"
TG_PKG = "org.telegram.messenger.web"
TG_STORE = BASE / "run_s163_telegram/store_telegram/data"

DOOZ_APK = BASE / "upload/canonical_apks/dooz_23_toplevel.apk"
DOOZ_PKG = "io.github.yamin8000.dooz"
DOOZ_STORE = BASE / "run_s163_dooz/store_dooz/data"

BIN_SHA = None


def bin_sha16():
    global BIN_SHA
    if BIN_SHA is None:
        import hashlib
        BIN_SHA = hashlib.sha256(g.BIN.read_bytes()).hexdigest()[:16]
    return BIN_SHA


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


# ── T1: Telegram baseline ──────────────────────────────────────────────
def tg_baseline():
    assert TG_STORE.exists(), "S163 telegram store missing — reinstall needed"
    print(f"== T1 telegram baseline 90s (bin {bin_sha16()}, "
          f"existing store, no reinstall) ==")
    row, text = g.run_case("tg_baseline_90s", TG_APK, TG_STORE, tap=None,
                           gate_ms=None, frames=8, max_seconds=90,
                           package=TG_PKG)
    row["bin_sha16"] = bin_sha16()
    row["uncaught_l9j"] = len(re.findall(r"Ll9/j;", text))
    row["uncaught_tl_autodl"] = len(
        re.findall(r"TL_autoDownloadSettings", text))
    row["uncaught_firebase_provider"] = len(
        re.findall(r"FirebaseInitProvider", text))
    row["uncaught_first5"] = re.findall(r"UNCAUGHT[^\n]{0,150}", text)[:5]
    row["rec_miss_total"] = len(re.findall(r"REC-MISS", text))
    row["ondraw_zero_ops"] = len(
        re.findall(r"onDraw dispatched .*ops=0|ops=0 \(", text))
    fam = Counter(re.findall(r"UNCAUGHT-TOP\] \[EXC-UNCAUGHT-TOP\] (L\S+);",
                             text))
    row["uncaught_top_families"] = dict(fam.most_common(8))
    row["frames_rendered"] = re.findall(r"Frames Rendered: (\d+)", text)
    shot = g.OUT / "tg_baseline_90s/screenshot.png"
    if shot.exists():
        import shutil
        shutil.copy(shot, EVID / "S164_tg_baseline_screenshot.png")
        row["face_screenshot"] = g.sha16(shot)
    merge_evid("S164_TG_BASELINE.json", row)
    for k in ("wall_s", "verdict", "uncaught", "uncaught_l9j",
              "uncaught_tl_autodl", "face_screenshot"):
        print(k, "=", row.get(k))


# ── D2: dooz composite diagnosis ───────────────────────────────────────
def dooz_diag(seconds=60):
    assert DOOZ_STORE.exists(), "S163 dooz store missing"
    rundir = g.OUT / "dooz_diag"
    console = g.OUT / "dooz_diag_console.log"
    env = dict(os.environ)
    env["MINIANDROID_S109_BITMAP"] = "1"
    cmd = [str(g.BIN), "run", "--execution-mode", "real-dalvik",
           "--data-root", str(DOOZ_STORE), "-o", str(rundir),
           "--max-seconds", str(seconds), "--frames", "30",
           "--trace", "--package", DOOZ_PKG]
    print(f"== D2 dooz diag {seconds}s S109-BITMAP (bin {bin_sha16()}) ==")
    t0 = time.time()
    with open(console, "w") as cf:
        subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                       timeout=seconds + 90, env=env)
    wall = round(time.time() - t0, 1)
    text = console.read_text(errors="replace")
    dt = re.findall(r"\[S109-DRAWTEXT\] replay '([^']{0,40})' at \("
                    r"([-\d.]+),([-\d.]+)\) size=([\d.]+) color=0x([0-9a-f]+)",
                    text)
    colors = Counter(c for _, _, _, _, c in dt)
    row = {
        "bin_sha16": bin_sha16(),
        "wall_s": wall,
        "drawtext_replay_rows": len(dt),
        "drawtext_color_hist": dict(colors.most_common(10)),
        "drawtext_first8": dt[:8],
        "c013_rows": re.findall(r"\[C013-CUSTOMVIEW\][^\n]{0,140}", text)[:4],
        "exp092_copy": re.findall(r"\[EXP092-COPY\] fb has (\d+) non-white",
                                  text)[-3:],
        "winbg": re.findall(r"\[EXT01-WINBG\][^\n]{0,80}", text)[-1:]
        if "[EXT01-WINBG]" in text else [],
        "f351_erase_rows": len(re.findall(r"\[F351-ERASE\]", text)),
        "f298_keep_rows": len(re.findall(r"\[F298-KEEP\]", text)),
        "verdict_timeline": re.findall(r"FRAME_ANALYSIS state=(\S+)", text),
        "face": g.sha16(rundir / "screenshot.png")
        if (rundir / "screenshot.png").exists() else None,
    }
    merge_evid("S164_DOOZ_DIAG.json", row)
    print(json.dumps({k: row[k] for k in
                      ("wall_s", "drawtext_replay_rows",
                       "drawtext_color_hist", "face")}, indent=1))


if __name__ == "__main__":
    phase = sys.argv[1] if len(sys.argv) > 1 else "all"
    if phase in ("all", "tg_baseline"):
        tg_baseline()
    if phase in ("all", "dooz_diag"):
        dooz_diag()
