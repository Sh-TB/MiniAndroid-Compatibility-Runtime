#!/usr/bin/env python3
"""s131_input_probe.py — M-01 wave probe: dump view trees for sudoku +
opencalculator to select real tap targets for the intercept evidence wave."""
import os
import re
import subprocess

R = "/home/z/my-project"
ENG = f"{R}/miniandroid/build/miniandroid"
OUT = f"{R}/run/s131"
os.makedirs(OUT, exist_ok=True)

for tag, apk in [("sudoku", f"{R}/upload/sudoku_secuso_101.apk"),
                 ("opencalculator", f"{R}/upload/opencalculator_53.apk")]:
    d = f"{OUT}/{tag}_probe"
    os.makedirs(d, exist_ok=True)
    cmd = [ENG, "run", "--execution-mode", "real-dalvik", "--frames", "6",
           "--frame-delay", "150", "--dump-view-tree", "-o", d, apk]
    rc = subprocess.call(cmd, stdout=open(f"{d}.log", "w"),
                         stderr=subprocess.STDOUT, timeout=600)
    tree = f"{d}/view_tree.json"
    if os.path.exists(tree):
        t = open(tree).read()
        # clickable views with bounds
        hits = re.findall(r'\{[^{}]*"clickable"[^{}]*\}', t)
        print(f"== {tag} rc={rc} tree={len(t)}B clickable-entries={len(hits)}")
        for h in hits[:14]:
            print("  ", h[:200])
    else:
        print(f"== {tag} rc={rc} NO TREE; log tail:")
        print("  ", open(f"{d}.log").read()[-400:])
