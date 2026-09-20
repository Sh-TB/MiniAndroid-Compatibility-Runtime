#!/usr/bin/env python3
"""S72-W3 fixture pixel verification — compare each fixture's screenshot.png
against the STORED BASELINE at docs/evidence/foundation/fixtures/<name>
(same verifier philosophy as verify_foundation.py: pixel evidence, not rc)."""
import os
from PIL import Image

W3 = "/home/z/my-project/run/s72_w3_fixtures"
BASE = "/home/z/my-project/docs/evidence/foundation/fixtures"
WHITE = (255, 255, 255)

def nonwhite_img(p):
    img = Image.open(p).convert("RGB")
    return sum(1 for px in img.getdata() if px != WHITE)

same = 0; diff = 0; missing_base = 0
for name in sorted(os.listdir(W3)):
    w3ss = os.path.join(W3, name, "screenshot.png")
    bass = os.path.join(BASE, name, "screenshot.png")
    if not os.path.exists(w3ss):
        print(f"{name}: W3 screenshot MISSING"); diff += 1; continue
    if not os.path.exists(bass):
        print(f"{name}: baseline screenshot missing (new fixture)"); missing_base += 1; continue
    a, b = nonwhite_img(w3ss), nonwhite_img(bass)
    status = "SAME" if a == b else f"DELTA {a-b:+d}"
    if a == b: same += 1
    else: diff += 1
    print(f"{name}: base={a} w3={b} {status}")
print(f"\nSAME={same} DELTA={diff} no-baseline={missing_base}")
