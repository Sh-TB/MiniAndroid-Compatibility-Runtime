#!/usr/bin/env bash
# CONT-11 TRAIN-7 probe 9: who WRITES Lpz0;.D (the coordinator packed position)?
# Source law (1.6.7 NodeCoordinator.placeAt): placement writes the coordinator
# position. If puts=0 -> the engine's placement writes Placeables but never
# the coordinator positions -> the hit-test sees zeros -> wrong hit path.
set -u
cd /home/z/my-project
OUT=tmp/train7_pmc9_out
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_FIELD_TRACE="Lpz0;.D"
timeout 580 ./miniandroid/build/miniandroid run upload/canonical_apks/dooz_23_toplevel.apk \
  --width 1080 --height 1920 --frames 16 \
  --max-seconds 560 \
  --tap 765,1830@8 \
  -o "$OUT" 2>"$OUT/pmc9.log"
echo "exit=$?"
echo "=== FIELD-TRACE lines ==="
grep -c "FIELD-TRACE" "$OUT/pmc9.log" || true
echo "=== iput (writes) ==="
grep "FIELD-TRACE" "$OUT/pmc9.log" | grep -c "iput" || true
echo "=== first writes (iput) ==="
grep "FIELD-TRACE" "$OUT/pmc9.log" | grep "iput" | head -15
echo "=== first reads (iget) ==="
grep "FIELD-TRACE" "$OUT/pmc9.log" | grep "iget" | head -8
