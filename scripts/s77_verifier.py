#!/usr/bin/env python3
"""s77_verifier.py — S77 §1 baseline verification (the S72-W3 verifier recipe
+ the S76-strengthened f54 A7b gate).

1. For each fixture dir in run/s77_baseline: compare screenshot.png nonwhite
   pixel count against the STORED BASELINE at docs/evidence/foundation/fixtures/<name>.
2. f54 gate: engine.log must contain the [A7b] ... DECODED line.
Pixel evidence, not rc.
"""
import os, re, sys
from PIL import Image

RUN = "/home/z/my-project/run/s77_baseline"
BASE = "/home/z/my-project/docs/evidence/foundation/fixtures"
WHITE = (255, 255, 255)

def nonwhite_img(p):
    img = Image.open(p).convert("RGB")
    return sum(1 for px in img.getdata() if px != WHITE)

same = 0; diff = 0; missing_base = 0; gate_fail = []
for name in sorted(os.listdir(RUN)):
    if not os.path.isdir(os.path.join(RUN, name)):
        continue
    ss = os.path.join(RUN, name, "screenshot.png")
    bass = os.path.join(BASE, name, "screenshot.png")
    if not os.path.exists(ss):
        print(f"{name}: screenshot MISSING"); diff += 1; continue
    if not os.path.exists(bass):
        print(f"{name}: baseline missing (no stored base)"); missing_base += 1; continue
    a, b = nonwhite_img(ss), nonwhite_img(bass)
    status = "SAME" if a == b else f"DELTA {a-b:+d}"
    if a == b: same += 1
    else: diff += 1
    # f54 A7b gate (S76-strengthened)
    if name == "f54_manifestlabel":
        log = open(os.path.join(RUN, name, "engine.log")).read()
        if not re.search(r"\[A7b\] icon @0x[0-9a-f]+ -> .* DECODED \d+x\d+", log):
            gate_fail.append(name)
            status += " A7B_GATE_FAIL"
        else:
            status += " A7B_GATE_OK"
    print(f"{name}: base={a} run={b} {status}")
total = same + diff
print(f"\nSAME={same} DELTA={diff} no-baseline={missing_total if False else missing_base} a7b_gate_fail={len(gate_fail)}")
print(f"VERIFIER RESULT: {same}/{total} PASS" if diff == 0 and not gate_fail else f"VERIFIER RESULT: {same}/{total} — FAILURES PRESENT")
sys.exit(0 if diff == 0 and not gate_fail else 1)
