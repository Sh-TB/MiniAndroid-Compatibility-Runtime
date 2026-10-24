#!/bin/bash
# cont11_drawtrace.sh — CONT-11 W7: F-NEW-256 canvas-bridge engagement forensics.
# Trace the dooz draw chain at the current binary to find WHY Ljt1;
# (AndroidCanvas) is never constructed and CanvasShadow records 0 ops.
# Faces to discriminate (from W4/W6 evidence):
#   (a) Lt4;.dispatchDraw never invoked by the engine's top-level draw
#   (b) dispatchDraw runs but breaks before canvasHolder.drawInto
#   (c) drawInto runs but the layer drawContent leaf never reaches
#       CanvasDrawScope.draw -> AndroidCanvas.drawRect
#   (d) Ljt1;.drawRect runs but dispatches to a shadow slot that drops ops
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/w7/trace
ST=$BASE/run/w7/anchors/store_dooz
APK=$BASE/upload/canonical_apks/io.github.yamin8000.dooz_23.apk
mkdir -p "$OUT"
if [ ! -d "$ST" ]; then
  "$BIN" install "$APK" --data-root "$ST" > /dev/null 2>&1
fi

run_one() {
  local name="$1"; shift
  local o="$OUT/$name"
  rm -rf "$o"; mkdir -p "$o"
  env "$@" "$BIN" run --package io.github.yamin8000.dooz --data-root "$ST" \
    --trace --max-seconds 120 --frames 40 -o "$o" > "$o/run.log" 2>&1
  echo "== $name rc=$? =="
  grep -E "C013-ONDRAW|APP_DRAW_OPS|app_draw_ops|first_missing_stage|FRAME_ANALYSIS|verdict" "$o/run.log" | head -6
}

# 1. baseline counters (C013 + F095 drawchild + canvas op counts)
run_one baseline

# 2. trace AndroidComposeView.dispatchDraw (Lt4;) — is it invoked, where does it stop
MINIANDROID_METHOD_TRACE="Lt4;|dispatchDraw" MINIANDROID_METHOD_TRACE_BUDGET=30000 run_one mtrace_dispatchDraw

# 3. trace the layer drawContent (Lpz0;.M0)
MINIANDROID_METHOD_TRACE="Lpz0;|M0" MINIANDROID_METHOD_TRACE_BUDGET=30000 run_one mtrace_drawContent

# 4. caller-frame trace of the draw manager family
MINIANDROID_CL_TRACE="Ljt1;,Lpz0;,Ly3;,Lt4;" run_one cltrace_drawchain
