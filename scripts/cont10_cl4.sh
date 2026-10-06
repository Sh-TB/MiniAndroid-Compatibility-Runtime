#!/bin/bash
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/w6
RUN=$OUT/dooz_cl4
rm -rf "$RUN"; mkdir -p "$RUN"
MINIANDROID_RET_TRACE="Lc41;" \
MINIANDROID_CL_TRACE="Lc41;.getValue,Lc41;.setValue,Lyl;.g,Lyl;.f,Lzx0;.h,Lza1;.b,Lom;.h,Lp00;.t,Ld;.i,Lnb0;.H" \
  "$BIN" run --package io.github.yamin8000.dooz --data-root "$OUT/store_dooz" \
  --dump-view-tree --trace --max-seconds 120 --frames 40 -o "$RUN" \
  > "$RUN/run.log" 2> "$RUN/cl_trace.txt"
echo rc=$?; wc -l "$RUN/cl_trace.txt"
