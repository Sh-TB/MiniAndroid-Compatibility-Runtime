#!/usr/bin/env bash
# CONT-11 TRAIN-8 probe F — ARG-TRACE on Lbt0; (MeasurePassDelegate):
# every v0 (placeAt) entry prints receiver node id + packed J position +
# zIndex + layerBlock. The exact (node -> offset) map of the placement
# cascade, with caller frames.
set -u
cd /home/z/my-project
OUT=tmp/train8_probeF
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_ARG_TRACE="Lbt0;"
timeout 580 ./miniandroid/build/miniandroid run upload/canonical_apks/dooz_23_toplevel.apk \
  --width 1080 --height 1920 --frames 14 \
  --max-seconds 560 \
  --tap 765,1830@8 \
  -o "$OUT" 2>"$OUT/probeF.log"
echo "exit=$?"
echo "=== v0 ARG-TRACE entries ==="
grep -c "ARG-TRACE.*Lbt0;.v0" "$OUT/probeF.log"
echo "=== all v0 entries (receiver + J) ==="
grep -A2 "ARG-TRACE.*Lbt0;.v0" "$OUT/probeF.log" | head -80
