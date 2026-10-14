#!/bin/bash
# cont12_phase0_baseline.sh — CONT-12 PHASE 0: lock baseline
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/w8
APK=$BASE/upload/canonical_apks/io.github.yamin8000.dooz_23.apk
mkdir -p "$OUT"
ST="$OUT/store_dooz"
if [ ! -d "$ST" ]; then
  "$BIN" install "$APK" --data-root "$ST" > /dev/null 2>&1
fi
for i in 1 2 3; do
  o="$OUT/dooz_run$i"; rm -rf "$o"; mkdir -p "$o"
  "$BIN" run --package io.github.yamin8000.dooz --data-root "$ST" \
    --trace --max-seconds 120 --frames 40 -o "$o" > "$o/run.log" 2>&1
  s=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
  v=$(grep -oE 'VERDICT [A-Z_]+|"verdict"[^,}]*' "$o/run.log" | head -1)
  echo "dooz_run$i sha=$s $v"
done
