#!/usr/bin/env python3
"""
UNIFIED_007 — Final corpus pass with capability-split evidence.

Runs every corpus APK + Telegram on the CURRENT binary and records, per app:
  launch     : process exit 0
  render_ui  : nonwhite pixels > threshold (real UI visible, not white screen)
  interaction: at least one click listener registered AND dispatched
  render     : screenshot artifacts exist
Classes results as PROVEN / PARTIAL / FAILED / NOT_PROVEN per the charter
vocabulary, writes corpus_results.json + a human-readable table.
"""
import json
import os
import subprocess
import sys
from PIL import Image

REPO = "/home/z/my-project/repo/miniandroid"
OUT = os.path.join(REPO, "run", "u007_corpus_final")
os.makedirs(OUT, exist_ok=True)

APKS = []
corpus_dir = os.path.join(REPO, "download", "corpus")
for f in sorted(os.listdir(corpus_dir)):
    if f.endswith(".apk"):
        APKS.append((f.replace(".apk", ""), os.path.join(corpus_dir, f)))
APKS.append(("telegram", os.path.join(REPO, "download", "exp038_telegram", "Telegram.apk")))

results = {}
for name, apk in APKS:
    run_dir = os.path.join(OUT, name)
    timeout = 150 if name != "telegram" else 420
    cmd = [os.path.join(REPO, "build", "miniandroid"), "run",
           "--output", run_dir, apk]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=timeout, cwd=REPO)
        exit_code = p.returncode
        stderr = p.stderr
        stdout = p.stdout
    except subprocess.TimeoutExpired:
        exit_code = -99
        stderr = "TIMEOUT"
        stdout = ""

    rec = {"apk": name, "exit_code": exit_code}
    rec["launch"] = "PROVEN" if exit_code == 0 else "FAILED"

    # Screenshot analysis
    shot = os.path.join(run_dir, "screenshot.png")
    nonwhite = 0
    if os.path.exists(shot):
        try:
            img = Image.open(shot).convert("RGB")
            w, h = img.size
            px = img.load()
            nonwhite = sum(1 for y in range(0, h, 2) for x in range(0, w, 2)
                           if px[x, y] != (255, 255, 255))
        except Exception:
            nonwhite = 0
    rec["nonwhite_sampled"] = nonwhite
    rec["render_ui"] = "PROVEN" if nonwhite > 5000 else (
        "FAILED" if exit_code == 0 else "NOT_PROVEN")

    # Inflation + interactions from stderr
    infl = "U007-INFLATE] root_id=" in stderr
    views = 0
    for line in stderr.splitlines():
        if "U007-INFLATE] root_id=" in line and "views=" in line:
            try:
                views = int(line.split("views=")[1].split()[0])
            except Exception:
                pass
    rec["inflated_views"] = views
    dispatched = "dispatch_click(" in stderr and ") → OK" in stderr
    onclick_dex = "onClick" in stderr and "TRY-ENTRY" in stderr
    rec["interaction"] = ("PROVEN" if (dispatched and onclick_dex)
                          else "PARTIAL" if views > 0
                          else "NOT_PROVEN")

    # Deep DEX execution evidence
    deep = stderr.count("RECURSIVE INVOKE")
    rec["recursive_invokes"] = deep
    rec["render"] = "PROVEN" if os.path.exists(shot) else "FAILED"
    results[name] = rec
    print(f"{name:16s} exit={exit_code:>3} nonwhite={nonwhite:>7} "
          f"views={views:>3} invokes={deep:>5} "
          f"ui={rec['render_ui']} inter={rec['interaction']}")

with open(os.path.join(OUT, "corpus_results.json"), "w") as f:
    json.dump(results, f, indent=2)
print("\ncorpus_results.json written to", OUT)
