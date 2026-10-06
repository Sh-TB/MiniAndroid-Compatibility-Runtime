#!/bin/bash
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/w6
RUN=$OUT/dooz_cl2
rm -rf "$RUN"; mkdir -p "$RUN"
MINIANDROID_CL_TRACE="Lwo;.s,Lwo;.t,Lwo;.c,Lza1;.b,Laj0;.<init>,Lom;.h,Lrr0;.h,Ld;.i,Lp00;.t,Lnb0;.h,Lwo;.w,Lfb1;.a,Lfb1;.I" \
  "$BIN" run --package io.github.yamin8000.dooz --data-root "$OUT/store_dooz" \
  --dump-view-tree --trace --max-seconds 120 --frames 40 -o "$RUN" \
  > "$RUN/run.log" 2> "$RUN/cl_trace.txt"
echo rc=$?; wc -l "$RUN/cl_trace.txt"
