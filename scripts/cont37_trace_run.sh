#!/usr/bin/env bash
# cont37_trace_run.sh — one traced composeStopwatch run on the CONT-36 binary
set -uo pipefail
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
CSW=$BASE/tmp/cont35_apks/composeStopwatch_1009011.apk
O=$1
rm -rf "$O"; mkdir -p "$O"
MINIANDROID_CANVAS_DRAW_WIN_TRACE=1 \
MINIANDROID_DRAW_WINDOW_TRACE=1 \
timeout 300 "$BIN" run "$CSW" --width 1080 --height 1920 \
  --frames 5 --max-seconds 15 -o "$O" > "$O/run.log" 2>&1
echo "rc=$?"
sha256sum "$O/screenshot.png" 2>/dev/null | cut -c1-16
