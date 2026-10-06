#!/bin/bash
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/w6
RUN=$OUT/dooz_cl6
rm -rf "$RUN"; mkdir -p "$RUN"
MINIANDROID_CL_TRACE="Ltp1;.j,Ltp1;.i,Ltp1;.h,Ltp1;.a,Ltp1;.getValue,Ltp1;.m,Lxa1;.a,Ls50;.m,Ly91;.setValue,Ly91;.getValue" \
  "$BIN" run --package io.github.yamin8000.dooz --data-root "$OUT/store_dooz" \
  --dump-view-tree --trace --max-seconds 120 --frames 40 -o "$RUN" \
  > "$RUN/run.log" 2> "$RUN/cl_trace.txt"
echo rc=$?; wc -l "$RUN/cl_trace.txt"
