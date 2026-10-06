#!/bin/bash
# CONT-10 W6 — method-trace run for invalidation-chain analysis
set -e
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/w6
STORE=$OUT/store_dooz
RUN=$OUT/dooz_mtrace1
rm -rf "$RUN"; mkdir -p "$RUN"
MINIANDROID_METHOD_TRACE=1 MINIANDROID_METHOD_TRACE_BUDGET=200000 \
  "$BIN" run --package io.github.yamin8000.dooz --data-root "$STORE" \
  --dump-view-tree --trace --max-seconds 120 --frames 40 -o "$RUN" \
  > "$RUN/run.log" 2> "$RUN/method_trace.txt"
wc -l "$RUN/method_trace.txt"
