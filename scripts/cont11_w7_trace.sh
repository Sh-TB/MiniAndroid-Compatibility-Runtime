#!/bin/bash
# cont11_w7_trace.sh — TRAIN 1: dooz draw-path trace with focused CL_TRACE.
# Goal: capture the draw window after W6 fixes (nodes materialize) and find
# where the chain stops constructing the canvas / emitting draw ops.
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/w7
RUN=$OUT/dooz_trace1
rm -rf "$RUN"; mkdir -p "$OUT" "$RUN"
# Focus tokens: draw dispatch family + drawscope + canvas wrapper + text wrapper
export MINIANDROID_CL_TRACE="Lel0;.i,Lpz0;,Lgl0;,Ljt1;,Liw0;,Lwt0;,Luc0;,Lj7;.e"
"$BIN" run --package io.github.yamin8000.dooz --data-root "$OUT/store_dooz" \
  --dump-view-tree --trace --max-seconds 120 --frames 40 -o "$RUN" \
  > "$RUN/run.log" 2>&1
echo "rc=$?"
unset MINIANDROID_CL_TRACE
echo "--- verdict / draw ops ---"
grep -aE "VERDICT|verdict|APP_DRAW_OPS|app_draw_ops" "$RUN/run.log" | head -6
echo "--- screenshot sha ---"
sha256sum "$RUN/screenshot.png" 2>/dev/null | cut -c1-16
echo "--- CL_TRACE rows in draw family (last 40) ---"
grep -aE "\[CL-TRACE\]|\[METHOD-IN\]" "$RUN/run.log" | grep -aE "Lpz0|Lgl0|Ljt1|Lel0|Luc0|Lj7" | tail -40
echo "--- ERR/EXC rows near draw family ---"
grep -anE "ERR|EXC|unresolved|not found|NOT FOUND|missing" "$RUN/run.log" | grep -aiE "Lpz0|Lgl0|Ljt1|Lel0|canvas|draw" | head -30
