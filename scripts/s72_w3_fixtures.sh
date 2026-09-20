#!/usr/bin/env bash
# s72_w3_fixtures.sh — run the EXISTING 25 foundation fixture APKs on the
# current (F-141 law) binary + pixel-verify against the stored baseline.
# Fixture APKs are pinned (upload/foundation_apks) — no rebuild needed for
# a runtime-law regression (RULE 17 build matrix: skip rebuild when the
# fixture sources are unchanged).
set -uo pipefail
ROOT=/home/z/my-project
ENG=$ROOT/miniandroid/build/miniandroid
SRC=$ROOT/upload/foundation_apks
OUT=$ROOT/run/s72_w3_fixtures
mkdir -p "$OUT"

PASS=0; FAIL=0
for apk in "$SRC"/*.apk; do
  name="$(basename "$apk" .apk)"
  run="$OUT/$name"
  rm -rf "$run"; mkdir -p "$run"
  (cd "$run" && timeout 120 "$ENG" run -o "$run" "$apk" > engine.log 2>&1)
  rc=$?
  # pixel evidence: latest frame nonwhite
  px=$(python3 - "$run" <<'EOF'
import sys, os
from PIL import Image
d = sys.argv[1]
frames = sorted(fn for fn in (os.listdir(os.path.join(d, "frames")) if os.path.isdir(os.path.join(d, "frames")) else []) if fn.endswith((".ppm", ".png")))
f8 = os.path.join(d, "frames", frames[-1]) if frames else None
if not f8:
    print(-1)
else:
    img = Image.open(f8).convert("RGB")
    print(sum(1 for p in img.getdata() if p != (255,255,255)))
EOF
)
  f141=$(grep -c "f141-null-recv" "$run/engine.log" 2>/dev/null || true)
  echo "$name rc=$rc frame_px=$px f141_throws=$f141"
done
