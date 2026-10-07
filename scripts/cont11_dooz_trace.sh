#!/bin/bash
# cont11_dooz_trace.sh — W7 draw-path frontier trace:
# 1) plain baseline run (C013-ONDRAW always prints dispatch status/ops)
# 2) CL-trace run targeting the compose draw chain from dispatchDraw down
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/w7
RUN=$OUT/dooz_drawtrace
mkdir -p "$OUT"
rm -rf "$RUN"; mkdir -p "$RUN"
ST=$OUT/store_dooz_drawtrace
if [ ! -d "$ST" ]; then
  "$BIN" install "$BASE/upload/canonical_apks/io.github.yamin8000.dooz_23.apk" --data-root "$ST" > /dev/null 2>&1
fi
# Trace the draw chain candidates: AbstractComposeView/AndroidComposeView R8
# names come from the C013 line in run 1; CanvasDrawScope/AndroidCanvas are
# traced by their structural call sites (invoke of <init> under Ljt1;).
MINIANDROID_CL_TRACE="Ljt1;,Lpz0;,Lug0;,Lt4;" \
  "$BIN" run --package io.github.yamin8000.dooz --data-root "$ST" \
  --dump-view-tree --trace --max-seconds 120 --frames 40 -o "$RUN" \
  > "$RUN/run.log" 2> "$RUN/trace.txt"
echo "rc=$?"
grep -E "C013-ONDRAW|verdict|VERDICT" "$RUN/run.log" | head -8
echo "--- trace lines:"; wc -l < "$RUN/trace.txt"
echo "--- AndroidCanvas ctor sightings (Ljt1;.<init>):"
grep -c "Ljt1;\.<init>" "$RUN/trace.txt" || true
echo "--- draw-scope method sightings:"
grep -oE "CL-TRACE\] d=[0-9]+ L[a-zA-Z0-9_]+;\.[a-zA-Z0-9_<>]+" "$RUN/trace.txt" | head -5
