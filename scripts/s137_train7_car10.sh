#!/bin/bash
# CONT-11 W11 internet-train-7 car 10: does the REAL clickable composed
# factory (Lpm;.c) run, and how far? car-9 proved its inline REAL element
# construction (pc 0x0db6 Lkr1;.a + 0x0e04 new Ljr1;) never executes.
# Probe: MINIANDROID_PMC_TRACE (S137c) — entry + every invoke inside Lpm;.c.
set -u
cd /home/z/my-project
OUT=tmp/s137_run10
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_CANVAS_OP_TRACE="$OUT/canvas_ops.jsonl"
export MINIANDROID_THROW_TRACE=1
export MINIANDROID_KR1_CALL_TRACE=1
export MINIANDROID_PMC_TRACE="Lje1;|c,Lvs0;|j,Lav1;|h,Ldv1;|h,Lte;|h,Lue;|a"
./miniandroid/build/miniandroid run upload/canonical_apks/dooz_23_toplevel.apk \
  --width 1080 --height 1920 \
  --frames 14 --frame-delay 500 \
  --max-seconds 540 \
  --tap 765,1830@5 \
  --dump-view-tree \
  -o "$OUT" 2>"$OUT/throw_sites.log"
echo "EXIT=$?"
echo "=== ENTER count:"
grep -c '\[PMC\] ENTER' "$OUT/throw_sites.log"
echo "=== first 15 lines:"
grep '\[PMC\]' "$OUT/throw_sites.log" | head -15
echo "=== last 25 lines:"
grep '\[PMC\]' "$OUT/throw_sites.log" | tail -25
echo "=== did it reach the element construction region?"
grep -E '\[PMC\] pc=0x0(d[0-9a-f]{2}|e[0-1][0-9a-f]) ' "$OUT/throw_sites.log" | head -20
