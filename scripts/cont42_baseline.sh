#!/bin/bash
# cont42_baseline.sh — TRAIN 2 (CONT-42) baseline: dooz 90s at the fresh
# canonical binary. Verifies anchor byte-exactness (pin 851cc176), banks
# instruction count + wall time (the throughput baseline), and captures the
# census rows that name the burn.
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/cont42
RUN=$OUT/dooz_baseline
mkdir -p "$RUN"
S=$OUT/store_dooz
if [ ! -d "$S" ]; then
  "$BIN" install "$BASE/upload/canonical_apks/io.github.yamin8000.dooz_23.apk" --data-root "$S" > /dev/null 2>&1
fi
T0=$(date +%s.%N)
"$BIN" run --package io.github.yamin8000.dooz --data-root "$S" \
  --width 1080 --height 1920 --frames 5 --max-seconds 90 -o "$RUN" \
  > "$RUN/run.log" 2>&1
RC=$?
T1=$(date +%s.%N)
echo "rc=$RC wall=$(echo "$T1 - $T0" | bc)s"
echo "sha=$(sha256sum "$RUN/screenshot.png" 2>/dev/null | cut -c1-16)  (pin: 851cc176)"
grep -aE "VERDICT|verdict|APP_DRAW_OPS|app_draw_ops|instructions" "$RUN/run.log" | head -8
