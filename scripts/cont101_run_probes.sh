#!/usr/bin/env bash
# cont101_run_probes.sh — run the CONT-101 batch probes and print the
# stderr state rows. Pixel/ink-band oracles are evaluated separately by
# scripts/cont101_oracle.py (deterministic PPM scans).
# Usage: cont101_run_probes.sh <tag>   (tag = pre | post)
set -uo pipefail
cd /home/z/my-project
BIN=${BIN:-miniandroid/build/miniandroid}
TAG=$1
OUT=run/cont101/${TAG}
mkdir -p "$OUT"

run_one() {
  local APK=$1 NAME=$2 FRAMES=$3
  local o="$OUT/$NAME"
  rm -rf "$o"; mkdir -p "$o"
  timeout 120 "$BIN" run "$APK" --width 1080 --height 1920 --frames "$FRAMES" \
    --max-seconds 30 -o "$o" > "$o/run.log" 2>&1
  echo "== $NAME rc=$? =="
  rg -o "\[C99-(TX|ZO|CV|TXPAINT|TXVPAINT|ZOEL)[^]]*\].*|\[C99-(TX|ZO|CV)VER\].*|\[C99-(TX|ZO|CV)(DONE|ERR)\].*" \
     "$o/run.log" | sed 's/^/  /'
}

# T5 text: one run, phase rows land before the final frame
run_one run/cont101/c99tx.apk tx 6
# T6 z-order: TWO runs — phase1 raster (short) and phase2 raster (late)
run_one run/cont101/c99zo.apk zo1 3
run_one run/cont101/c99zo.apk zo2 8
# T7 canvas: single run (draw happens on first frame)
run_one run/cont101/c99cv.apk cv 5

echo "== binaries =="
for n in tx zo1 zo2 cv; do
  P=$(ls "$OUT/$n"/screenshot.ppm 2>/dev/null || ls "$OUT/$n"/frames/*.ppm 2>/dev/null | tail -1)
  echo "$n raster: $P"
done
