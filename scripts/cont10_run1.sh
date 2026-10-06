#!/bin/bash
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/w6
RUN=$OUT/dooz_fix1
rm -rf "$RUN"; mkdir -p "$RUN"
"$BIN" run --package io.github.yamin8000.dooz --data-root "$OUT/store_dooz" \
  --dump-view-tree --trace --max-seconds 120 --frames 40 -o "$RUN" \
  > "$RUN/run.log" 2>&1
echo rc=$?
grep -E "verdict|VERDICT|APP_DRAW_OPS|app_draw_ops" "$RUN/run.log" | head -5
grep -E "first_missing_stage|FRAME_ANALYSIS" "$RUN/run.log" | head -4
