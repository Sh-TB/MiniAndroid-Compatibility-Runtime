#!/bin/bash
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/w6
RUN=$OUT/dooz_cl7
rm -rf "$RUN"; mkdir -p "$RUN"
MINIANDROID_CL_TRACE="Lcx0;.a,Lcx0;.b,Lcx0;.c,Lcx0;.e,Lcx0;.f,Lcx0;.g,Lcx0;.i,Lcx0;.j,Lcx0;.n,Lcx0;.d,Ltp1;.j,Ltp1;.i,Ltp1;.h,Ltp1;.getValue,Lhe;.a,Lhe;.b" \
  "$BIN" run --package io.github.yamin8000.dooz --data-root "$OUT/store_dooz" \
  --dump-view-tree --trace --max-seconds 120 --frames 40 -o "$RUN" \
  > "$RUN/run.log" 2> "$RUN/cl_trace.txt"
echo rc=$?; wc -l "$RUN/cl_trace.txt"
