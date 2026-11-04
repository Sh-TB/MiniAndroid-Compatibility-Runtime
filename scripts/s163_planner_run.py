#!/usr/bin/env python3
"""s163_planner_run.py — S163: first RUNS of planner-class apps on merged main.

User directive: «کاری اصلی خودت دوز تلگرام و یکی دوتا برنامه ریزه ... رو اجرا
باید بکنی» — run dooz, Telegram, and 1-2 planner apps. This script covers the
planner lane: Etar calendar (ws.xsoh.etar) + SECUSO privacy-friendly todolist
(org.secuso.privacyfriendlytodolist). Neither appears in the execution ledger
as a RUN (worklog hits were batch listings only) — these are first-run rows.

Reuses the S154 harness verbatim (install/run_case/frame_faces) with:
  BIN -> miniandroid/build/miniandroid (W5-merged main 512517269d9634a1)
  OUT -> run_s163_planner (external, gitignored)
No tap, gate unset, 30s budget, 12 frames — pure launch-and-render rows.
"""
import json
import re
import sys
from pathlib import Path

BASE = Path("/home/z/my-project")
sys.path.insert(0, str(BASE / "scripts"))
import s154_awaitup_gate as g

g.BIN = BASE / "miniandroid/build/miniandroid"
g.OUT = BASE / "run_s163_planner"
g.OUT.mkdir(parents=True, exist_ok=True)
EVID = BASE / "evidence/s163_runs"
EVID.mkdir(parents=True, exist_ok=True)

APKS = [
    ("etar_calendar", BASE / "upload/fdroid_batch/ws.xsoh.etar_57.apk",
     "ws.xsoh.etar"),
    ("secuso_todolist",
     BASE / "upload/fdroid_batch/org.secuso.privacyfriendlytodolist_103.apk",
     "org.secuso.privacyfriendlytodolist"),
]


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    rows = {}
    for tag, apk, pkg in APKS:
        if which != "all" and which not in tag:
            continue
        store = g.OUT / f"store_{pkg}/data"
        print(f"== install {pkg} ==")
        g.install(apk, store)
        print(f"== run {tag} ({pkg}) ==")
        row, text = g.run_case(tag, apk, store, tap=None, gate_ms=None,
                               frames=12, max_seconds=30, package=pkg)
        # honest extras: render nodes + first blocker lines
        row["exp092_render_nodes"] = len(
            re.findall(r"\[EXP092-RENDER\]", text))
        row["uncaught_first"] = next(
            iter(re.findall(r"UNCAUGHT[^\n]{0,140}", text)), None)
        verdicts = re.findall(r"FRAME_ANALYSIS state=(\S+)", text)
        row["verdict_timeline"] = verdicts
        rows[tag] = row

    rows["_meta"] = {
        "binary": g.BIN.name, "binary_sha16": g.sha16(g.BIN),
        "protocol": "s154 harness reuse, no-tap launch rows, 30s/12 frames",
        "law": "claims untested = zero value; these are tested rows",
    }
    out = EVID / "S163_PLANNER.json"
    json.dump(rows, open(out, "w"), indent=1)
    print("evidence ->", out)


if __name__ == "__main__":
    main()
