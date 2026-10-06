#!/bin/bash
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/w6
RUN=$OUT/dooz_fix_trace3
rm -rf "$RUN"; mkdir -p "$RUN"
MINIANDROID_F259_TRACE=1 \
MINIANDROID_CL_TRACE="Lcx0;.o,Lcx0;.b,Lvw0;.a,Ltp1;.j,Lc41;.setValue,Lyl;.g,Lww;.i,Lww;.h,Lnb0;.n,Lnb0;.H,Lzx0;.h,Lom;.h,Lp00;.t,Lrr0;.h,Lel0;.<init>,Lv02;.c" \
  "$BIN" run --package io.github.yamin8000.dooz --data-root "$OUT/store_dooz" \
  --dump-view-tree --trace --max-seconds 120 --frames 40 -o "$RUN" \
  > "$RUN/run.log" 2> "$RUN/cl_trace.txt"
echo rc=$?
