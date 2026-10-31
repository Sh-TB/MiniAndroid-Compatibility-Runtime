#!/usr/bin/env bash
# CONT-11 TRAIN-9 (fix train) probe A — THE BLOCK-DISPATCH CORRELATION.
# Banked question: 42 deferred branches (TRAIN-8) vs 22 observe-block
# dispatches — do all deferred placeOuterCoordinatorBlocks execute?
# Instruments (revised after the v0/pc=83 decode + Lat0; class dump):
#   FIELD "Lat0;" — every field access inside the block lambda's frame
#   (Lat0;.a, 362 insns, the Lu80; Function0 body). One execution prints a
#   group of get lines => a budget-free block-execution counter (PMC watch
#   "Lat0;|" was a watch artifact: empty method never matches).
set -u
cd /home/z/my-project
OUT=tmp/train9_probeA
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_FIELD_TRACE="Lat0;"
timeout 560 ./miniandroid/build/miniandroid run upload/canonical_apks/dooz_23_toplevel.apk \
  --width 1080 --height 1920 --frames 14 \
  --max-seconds 540 \
  --tap 765,1830@8 \
  -o "$OUT" 2>"$OUT/probeA.log"
echo "exit=$?"
echo "=== block lambda field accesses (total) ==="
grep "FIELD-TRACE.*Lat0;" "$OUT/probeA.log" | wc -l
echo "=== distinct block execution groups (get from Lat0;.a) ==="
grep "FIELD-TRACE.* get Lat0;" "$OUT/probeA.log" | wc -l
echo "=== first 20 block frames ==="
grep "FIELD-TRACE" "$OUT/probeA.log" | grep "Lat0;" | head -20
