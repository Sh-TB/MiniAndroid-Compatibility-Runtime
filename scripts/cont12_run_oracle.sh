#!/bin/bash
# cont12_run_oracle.sh — CONT-12 PHASE 3 experiment B2: run the bound
# external-Compose oracle probe on MiniAndroid with full evidence capture.
set -uo pipefail
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/w8/oracle12
APK=$OUT.apk
APKPATH=$BASE/run/w8/oracle12.apk
mkdir -p "$OUT"
ST=$OUT/store
if [ ! -d "$ST" ]; then
  "$BIN" install "$APKPATH" --data-root "$ST" > "$OUT/install.log" 2>&1
  echo "install rc=$?"
fi
"$BIN" run --package com.probe.oracle12 --data-root "$ST" \
  --dump-view-tree --trace --max-seconds 120 --frames 40 -o "$OUT" \
  > "$OUT/run.log" 2> "$OUT/trace.txt"
echo "run rc=$?"
echo "── verdict:"; grep -oE 'VERDICT [A-Z_]+|"verdict"[^,}]*' "$OUT/run.log" | head -2
echo "── screenshot:"; sha256sum "$OUT/screenshot.png" 2>/dev/null | cut -c1-16
echo "── run.log size: $(wc -l < "$OUT/run.log") lines; trace: $(wc -l < "$OUT/trace.txt") lines"
echo "── last log lines:"; tail -6 "$OUT/run.log"
