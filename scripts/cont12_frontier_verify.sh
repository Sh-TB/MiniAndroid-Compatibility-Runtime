#!/bin/bash
# cont12_frontier_verify.sh — CONT-12 PHASE 0: independent frontier re-verification
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/w8/frontier
rm -rf "$OUT"; mkdir -p "$OUT"
ST=$BASE/run/w8/store_dooz
MINIANDROID_CL_TRACE="Lzs0;,Lm7;,Lkb;,Lvs0;,Lel0;,Lt4;" \
  "$BIN" run --package io.github.yamin8000.dooz --data-root "$ST" \
  --dump-view-tree --trace --max-seconds 120 --frames 40 -o "$OUT" \
  > "$OUT/run.log" 2> "$OUT/trace.txt"
echo "rc=$?"
echo "── verdict:"; grep -oE 'VERDICT [A-Z_]+|"verdict"[^,}]*' "$OUT/run.log" | head -1
echo "── screenshot sha16:"; sha256sum "$OUT/screenshot.png" | cut -c1-16
echo "── measure chain frames (Lzs0.m / Lm7.<init> / Lvs0.c / Lel0.Y):"
for m in "Lzs0;\.m" "Lm7;\.<init>" "Lvs0;\.c" "Lel0;\.Y"; do
  printf "   %-16s %s\n" "$m" "$(grep -cE "CL-TRACE\] d=[0-9]+ $m" "$OUT/trace.txt")"
done
echo "── canvas content ops (run.log):"
grep -ciE "canvas (draw|op)|drawRect|drawCircle|drawPath|drawText" "$OUT/run.log" || true
grep -oE "C013-ONDRAW[^|]*\|[^|]*" "$OUT/run.log" | head -4
