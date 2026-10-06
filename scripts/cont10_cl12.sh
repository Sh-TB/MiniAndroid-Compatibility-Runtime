#!/bin/bash
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/w6
RUN=$OUT/dooz_cl12
rm -rf "$RUN"; mkdir -p "$RUN"
MINIANDROID_R337_TRACE=1 \
MINIANDROID_CL_TRACE="Ltp1;.j,Ltp1;.a,Lzw0;.a,Lcx0;.b,Lm20;.equals,Lm20;.isEmpty" \
  "$BIN" run --package io.github.yamin8000.dooz --data-root "$OUT/store_dooz" \
  --dump-view-tree --trace --max-seconds 120 --frames 40 -o "$RUN" \
  > "$RUN/run.log" 2> "$RUN/cl_trace.txt"
echo rc=$?; wc -l "$RUN/cl_trace.txt"
