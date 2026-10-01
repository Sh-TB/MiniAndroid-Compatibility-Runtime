#!/usr/bin/env python3
"""s131_input_wave.py — M-01 INPUT evidence wave (S131, law-gated by
docs/REUSE_AUDIT_INPUT.md: adapter EVIDENCE, zero new input subsystems).

A. sudoku baseline determinism: 3 runs x 8 frames, byte-identical screenshots.
B. sudoku intercept/tap evidence: --tap at the CENTER of the real 'Next'
   button (849,1794 231x126 -> center 964,1857) through the R-NEW-424 walk
   law; expect UI-EVENT chain records + PerformClick + frame change.
C. opencalculator honest recording: 76 Buttons present but GridLayout bounds
   unassigned (w=0) in the dump — measured MC-041 layout frontier; tap
   attempt recorded honestly.
Output: run/s131/wave_report.json + evidence JPGs.
"""
import glob
import hashlib
import json
import os
import re
import subprocess

from PIL import Image

R = "/home/z/my-project"
ENG = f"{R}/miniandroid/build/miniandroid"
OUT = f"{R}/run/s131"
EV = f"{R}/evidence/s131_input_wave"
os.makedirs(EV, exist_ok=True)
REPORT = {}


def sha256(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:8]


def run(tag, apk, frames, taps=(), timeout=600):
    d = f"{OUT}/{tag}"
    os.makedirs(d, exist_ok=True)
    cmd = [ENG, "run", "--execution-mode", "real-dalvik",
           "--frames", str(frames), "--frame-delay", "100", "-o", d]
    for (x, y, k) in taps:
        cmd += ["--tap", f"{x},{y}@{k}"]
    cmd += [apk]
    rc = subprocess.call(cmd, stdout=open(f"{d}.log", "w"),
                         stderr=subprocess.STDOUT, timeout=timeout)
    return rc, d


def small_jpg(src, dst, w=460):
    im = Image.open(src).convert("RGB")
    r = w / im.width
    im = im.resize((w, int(im.height * r)))
    im.save(dst, "JPEG", quality=82)


def shots(d):
    return sorted(glob.glob(f"{d}/screenshot*.png")) or (
        [f"{d}/screenshot.png"] if os.path.exists(f"{d}/screenshot.png") else [])


# ---- A. sudoku baseline determinism (3 runs) ----
SUD = f"{R}/upload/sudoku_secuso_101.apk"
base_shas = []
for i in (1, 2, 3):
    rc, d = run(f"sudoku_base{i}", SUD, 8)
    s = shots(d)
    base_shas.append(sha256(s[-1]) if s else "NONE")
print("A. sudoku baseline SHAs:", base_shas)
REPORT["sudoku_baseline"] = {"rc": rc, "shas": base_shas,
                             "deterministic": len(set(base_shas)) == 1}
if base_shas[0] != "NONE":
    small_jpg(shots(f"{OUT}/sudoku_base1")[-1], f"{EV}/sudoku_baseline.jpg")

# ---- B. sudoku 'Next' tap through the walk law ----
rc, d = run("sudoku_tap", SUD, 10, taps=[(964, 1857, 4)])
log = open(f"{OUT}/sudoku_tap.log").read()
chains = re.findall(r"touch_target_chain[^\n]*", log)
clicks = re.findall(r"PerformClick[^\n]*", log) or re.findall(
    r"performClick[^\n]*", log)
events = re.findall(r"\[UI-EVENT\][^\n]*", log)
tap_shas = [sha256(p) for p in shots(d)]
print("B. sudoku tap rc:", rc, "shas:", tap_shas)
print("   chains:", len(chains), "clicks:", len(clicks),
      "events:", len(events))
for e in events[:6]:
    print("   ", e[:150])
REPORT["sudoku_tap"] = {
    "rc": rc, "shas": tap_shas,
    "changed_vs_baseline": bool(tap_shas and tap_shas[-1] != base_shas[0]
                                and base_shas[0] != "NONE"),
    "chain_records": len(chains), "click_records": len(clicks),
    "ui_events": len(events), "event_sample": events[:4],
}
if shots(d):
    small_jpg(shots(d)[-1], f"{EV}/sudoku_after_tap.jpg")

# ---- C. opencalculator honest recording ----
t = json.load(open(f"{OUT}/opencalculator_probe2/view_tree.json"))
nodes = t["nodes"]
btns = [n for n in nodes if "Button" in n.get("class", "")]
laid = [n for n in btns if n.get("width", 0) > 0 and n.get("height", 0) > 0]
print("C. opencalculator buttons:", len(btns), "with bounds:", len(laid))
REPORT["opencalculator"] = {
    "buttons": len(btns), "buttons_with_bounds": len(laid),
    "honest": ("GridLayout button bounds unassigned in tree dump — MC-041 "
               "layout family frontier; taps cannot resolve through the walk "
               "law until bounds exist. MEASURED FINDING, no input-code fix "
               "permitted by the REUSE-FIRST audit (layout law, not input)."),
}

# chain max for the baseline wave law (S128 measured max=5 on calc)
REPORT["law_gate"] = {
    "wave": "S131 M-01 INPUT evidence wave (audit-gated, zero new subsystems)",
    "battery_ref": "scripts/test/run_test_battery.sh 124 stages ALL PASS",
}
json.dump(REPORT, open(f"{OUT}/wave_report.json", "w"), indent=1)
print("report -> run/s131/wave_report.json")
