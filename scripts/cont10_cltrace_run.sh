#!/bin/bash
# CONT-10 W6 — CL_TRACE targeted run: recompose walk internals
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/w6
RUN=$OUT/dooz_cl1
rm -rf "$RUN"; mkdir -p "$RUN"
MINIANDROID_CL_TRACE="Lnb0;.H,Lnb0;.K,Lnb0;.P,Lnb0;.o,Lnb0;.i0,Lnb0;.F,Loo;.c,Lza1;.a,Lza1;.b,Lza1;.c,Lza1;.d,Lnn1;.r,Lnn1;.i,Lnn1;.m,Lnn1;.f,Lnn1;.b,Lnn1;.k,Lnn1;.q,Lbi0;.c,Lnb0;.V,Lnb0;.u,Lnb0;.S,Lnb0;.D,Lnb0;.p" \
  "$BIN" run --package io.github.yamin8000.dooz --data-root "$OUT/store_dooz" \
  --dump-view-tree --trace --max-seconds 120 --frames 40 -o "$RUN" \
  > "$RUN/run.log" 2> "$RUN/cl_trace.txt"
echo rc=$?; wc -l "$RUN/cl_trace.txt"
