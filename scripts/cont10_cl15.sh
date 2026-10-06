#!/bin/bash
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/w6
RUN=$OUT/dooz_cl15
rm -rf "$RUN"; mkdir -p "$RUN"
MINIANDROID_RET_TRACE="Enum;" \
MINIANDROID_CL_TRACE="Lcx0;.o,Lcx0;.b,Lvw0;.a,Lxw0;.b" \
  "$BIN" run --package io.github.yamin8000.dooz --data-root "$OUT/store_dooz" \
  --dump-view-tree --trace --max-seconds 120 --frames 40 -o "$RUN" \
  > "$RUN/run.log" 2> "$RUN/cl_trace.txt"
echo rc=$?; wc -l "$RUN/cl_trace.txt"
