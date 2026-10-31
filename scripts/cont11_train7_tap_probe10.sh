#!/usr/bin/env bash
# CONT-11 TRAIN-7 probe 10 (DECISIVE): the placement chain.
# v0 = MeasurePassDelegate.placeAt (writes lastPosition L:J)
# i1 = NodeCoordinator.placeSelf (writes position .D)
# FIELD-TRACE = every .D access with values
set -u
cd /home/z/my-project
OUT=tmp/train7_pmc10_out
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_PMC_TRACE="Lbt0;|v0,Lpz0;|i1"
export MINIANDROID_FIELD_TRACE="Lpz0;.D"
timeout 580 ./miniandroid/build/miniandroid run upload/canonical_apks/dooz_23_toplevel.apk \
  --width 1080 --height 1920 --frames 14 \
  --max-seconds 560 \
  --tap 765,1830@8 \
  -o "$OUT" 2>"$OUT/pmc10.log"
echo "exit=$?"
echo "=== ENTER counts ==="
grep "PMC] ENTER" "$OUT/pmc10.log" | sort | uniq -c | sort -rn
echo "=== v0 internal (first 30) ==="
grep "\[PMC\] Lbt0;.v0 " "$OUT/pmc10.log" | head -30
echo "=== i1 internal (first 30) ==="
grep "\[PMC\] Lpz0;.i1 " "$OUT/pmc10.log" | head -30
echo "=== .D non-init puts ==="
grep "FIELD-TRACE" "$OUT/pmc10.log" | grep " put " | grep -v "<init>" | head -12
