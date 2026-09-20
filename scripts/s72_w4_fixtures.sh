#!/usr/bin/env bash
# s72_w4_fixtures.sh — W4 fixture battery: 25 pinned foundation APKs on the
# current binary, same recipe as s72_w3_fixtures.sh; per-fixture rc + frame_px
# + f141-throw count; then pixel-compare vs W3 run dir (stored evidence).
set -uo pipefail
ROOT=/home/z/my-project
ENG=$ROOT/miniandroid/build/miniandroid
SRC=$ROOT/upload/foundation_apks
OUT=$ROOT/run/s72_w4_fixtures
W3=$ROOT/run/s72_w3_fixtures
mkdir -p "$OUT"

for apk in "$SRC"/*.apk; do
  name="$(basename "$apk" .apk)"
  run="$OUT/$name"
  rm -rf "$run"; mkdir -p "$run"
  (cd "$run" && timeout 120 "$ENG" run -o "$run" "$apk" > engine.log 2>&1)
  rc=$?
  px=$(python3 "$ROOT/scripts/w4_px.py" "$run")
  f141=$(grep -c "f141-null-recv" "$run/engine.log" 2>/dev/null || true)
  same="?"
  w3run="$W3/$name"
  if [ -f "$w3run/screenshot.png" ]; then
    same=$(python3 "$ROOT/scripts/w4_pxcmp.py" "$run" "$w3run")
  fi
  echo "$name rc=$rc frame_px=$px f141_throws=$f141 pixel_vs_w3=$same"
done
