#!/usr/bin/env python3
"""w4_pxcmp.py <runA> <runB> — compare final-frame pixel SHA (SAME/DIFF/?)."""
import sys, os, hashlib
from PIL import Image

def px_sha(d):
    ss = os.path.join(d, "screenshot.png")
    if not os.path.exists(ss):
        return None
    return hashlib.sha256(Image.open(ss).convert("RGB").tobytes()).hexdigest()[:16]

a, b = px_sha(sys.argv[1]), px_sha(sys.argv[2])
if a is not None and a == b:
    print("SAME")
elif a and b:
    print("DIFF")
else:
    print("?")
