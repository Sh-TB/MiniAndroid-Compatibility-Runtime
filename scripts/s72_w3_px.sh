#!/usr/bin/env bash
# s72_w3_px.sh — quick pixel metric for a single run dir (frame_008 nonwhite).
set -uo pipefail
d="$1"
python3 - "$d" <<'EOF'
import sys, os
from PIL import Image
d = sys.argv[1]
frames = sorted(fn for fn in (os.listdir(os.path.join(d, "frames")) if os.path.isdir(os.path.join(d, "frames")) else []) if fn.endswith((".ppm", ".png")))
f8 = os.path.join(d, "frames", frames[-1]) if frames else None
if not f8:
    print(f"{d}: NO FRAMES")
else:
    img = Image.open(f8).convert("RGB")
    nw = sum(1 for p in img.getdata() if p != (255,255,255))
    print(f"{d}: frame={os.path.basename(f8)} nonwhite={nw}")
EOF
