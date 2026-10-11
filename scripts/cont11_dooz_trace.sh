#!/bin/bash
# CONT-11 WAVE 7 — decisive dooz draw-path trace.
# Question: WHERE does the draw chain stop between "layer drawContent runs"
# and "canvas ops recorded"? Instruments: full method trace (bounded), CL trace
# on the draw chain classes, FIELD trace on Ly3;.a (DrawTransform canvas slot),
# NODE census, canvas-op trace.
set -e
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/cont11
STORE=$OUT/store_dooz_base
RUN=$OUT/dooz_drawtrace
rm -rf "$RUN"; mkdir -p "$RUN"
MINIANDROID_METHOD_TRACE=1 MINIANDROID_METHOD_TRACE_BUDGET=400000 \
MINIANDROID_NODE_CENSUS=1 \
MINIANDROID_CL_TRACE="Lt4;,Lpz0;,Lug0;,Lyl;,Ly3;,Lz3;,Ljt1;,Lel0;,Lkc;,Lng0;,Lhi;" \
MINIANDROID_FIELD_TRACE="Ly3;.a,Lhi;.a,Lz3;.a" \
MINIANDROID_CANVAS_OP_TRACE=1 \
  "$BIN" run --package io.github.yamin8000.dooz --data-root "$STORE" \
  --dump-view-tree --trace --max-seconds 120 --frames 40 -o "$RUN" \
  > "$RUN/run.log" 2> "$RUN/method_trace.txt" || true
echo "=== sizes ==="; wc -l "$RUN/method_trace.txt" 2>/dev/null || true
echo "=== canvas ops ==="; grep -cE "APP_DRAW_OPS=[1-9]" "$RUN/run.log" || echo "0 nonzero APP_DRAW_OPS lines"
grep -oE "APP_DRAW_OPS=[0-9]+" "$RUN/run.log" | tail -3 || true
echo "=== draw-chain presence in method trace ==="
for pat in "Lyl;.z" "Lz3;.a" "isHardwareAccelerated" "Lpz0;.M0" "Lpz0;.h1" "dispatchDraw" "Lel0;.i"; do
  printf "%-24s %s\n" "$pat" "$(grep -c "$pat" "$RUN/method_trace.txt" 2>/dev/null || echo 0)"
done
echo "=== uncaught ==="; grep -cE "EXC-UNCAUGHT" "$RUN/run.log" || true
