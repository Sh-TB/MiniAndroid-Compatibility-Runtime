#!/usr/bin/env python3
"""s163_telegram_probe.py — S163: Telegram RUN attempt on merged main.

User directive: run Telegram. History: S51-era mapped the v12 startup path
("no first frame this session", init-chain frontier). This is the current
answer on the W5-merged binary: install telegram_official.apk (64.8MB,
sha256 prefix e37aced2a49c1dbb) and run 90s with 8 frames, then extract the
first blockers (first UNCAUGHT, first REC-MISS families, verdict timeline).

Bounded by design: install timeout 600s, run budget 90s + 60s harness
grace — whatever the outcome (first frame / stall point / install failure)
it becomes the honest current row for the ledger.
"""
import json
import re
import sys
from pathlib import Path

BASE = Path("/home/z/my-project")
sys.path.insert(0, str(BASE / "scripts"))
import s154_awaitup_gate as g

g.BIN = BASE / "miniandroid/build/miniandroid"
g.OUT = BASE / "run_s163_telegram"
g.OUT.mkdir(parents=True, exist_ok=True)
EVID = BASE / "evidence/s163_runs"
EVID.mkdir(parents=True, exist_ok=True)

APK = BASE / "upload/telegram_official.apk"
# real package id (S163 install row): org.telegram.messenger.web,
# versionName 12.10.5, vc 71059 — NOT org.telegram.messenger
PKG = "org.telegram.messenger.web"


def main():
    import hashlib
    store = g.OUT / "store_telegram/data"
    apk_sha16 = hashlib.sha256(APK.read_bytes()).hexdigest()[:16]
    print(f"== install {APK.name} ({apk_sha16}) — may take minutes ==")
    g.install(APK, store)
    print("== run telegram 90s ==")
    row, text = g.run_case("telegram_90s", APK, store, tap=None,
                           gate_ms=None, frames=8, max_seconds=90,
                           package=PKG)
    # fallback: maybe package id differs — retry once without --package
    if row["verdict"] is None and re.search(r"not find|No package|not found",
                                            text):
        print("package not found under", PKG, "- retrying auto-detect")
        row2, text2 = g.run_case("telegram_90s_autopkg", APK, store,
                                 tap=None, gate_ms=None, frames=8,
                                 max_seconds=90, package=None)
        if row2["verdict"] is not None:
            row, text = row2, text2
    # blocker extraction: distinct first rows per family
    row["apk_sha16"] = apk_sha16
    row["verdict_timeline"] = re.findall(r"FRAME_ANALYSIS state=(\S+)", text)
    row["uncaught_first3"] = re.findall(r"UNCAUGHT[^\n]{0,160}", text)[:3]
    fams = re.findall(r"REC-MISS[^\n]{0,120}", text)
    row["rec_miss_total"] = len(fams)
    row["rec_miss_first3"] = fams[:3]
    row["last_console_lines"] = text.splitlines()[-8:]
    out = EVID / "S163_TELEGRAM.json"
    json.dump(row, open(out, "w"), indent=1)
    print("evidence ->", out)


if __name__ == "__main__":
    main()
