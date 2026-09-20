#!/usr/bin/env python3
"""w4_px.py <rundir> — nonwhite pixel count of run's screenshot.png (or -1)."""
import sys, os
from PIL import Image
d = sys.argv[1]
ss = os.path.join(d, "screenshot.png")
if os.path.exists(ss):
    img = Image.open(ss).convert("RGB")
    print(sum(1 for p in img.getdata() if p != (255, 255, 255)))
else:
    print(-1)
