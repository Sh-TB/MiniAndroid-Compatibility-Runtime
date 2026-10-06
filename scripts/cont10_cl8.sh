#!/bin/bash
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/w6
RUN=$OUT/dooz_cl8
rm -rf "$RUN"; mkdir -p "$RUN"
MINIANDROID_FIELD_TRACE="Lcx0;.g" \
MINIANDROID_CL_TRACE="Lcx0;.n,Lcx0;.<init>,Lxa1;.<init>,Lxa1;.b,Ly91;.<init>" \
  "$BIN" run --package io.github.yamin8000.dooz --data-root "$OUT/store_dooz" \
  --dump-view-tree --trace --max-seconds 120 --frames 40 -o "$RUN" \
  > "$RUN/run.log" 2> "$RUN/cl_trace.txt"
echo rc=$?; wc -l "$RUN/cl_trace.txt"
