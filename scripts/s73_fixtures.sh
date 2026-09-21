#!/usr/bin/env bash
# s73_fixtures.sh — S73 PART F regression: 25 pinned foundation APKs on the
# CURRENT binary (container rebuild + F-117 scheduled-tap extension).
# Same recipe as s72_w4_fixtures.sh: rc + frame_px + f141-throw count.
set -uo pipefail
ROOT=/home/z/my-project
ENG=$ROOT/miniandroid/build/miniandroid
SRC=$ROOT/upload/foundation_apks
OUT=$ROOT/run/s73_fixtures
mkdir -p "$OUT"

for apk in "$SRC"/*.apk; do
  name="$(basename "$apk" .apk)"
  run="$OUT/$name"
  rm -rf "$run"; mkdir -p "$run"
  (cd "$run" && timeout 120 "$ENG" run -o "$run" "$apk" > engine.log 2>&1)
  rc=$?
  px=$(python3 "$ROOT/scripts/w4_px.py" "$run" 2>/dev/null || echo NA)
  f141=$(grep -c "f141-null-recv" "$run/engine.log" 2>/dev/null || true)
  echo "$name rc=$rc frame_px=$px f141_throws=$f141"
done
echo "S73 fixtures battery complete: $OUT"
