#!/usr/bin/env bash
# CONT-11 TRAIN-9 probe F — the delegate dump: LN-DUMP Lbt0; (MeasurePass-
# Delegate per node: .e/.f = measured w/h, .w = isPlaced, .L = placeOuter-
# CoordinatorPosition) with the 512 bound. Combined with probeE's node
# graph this identifies every node in the FAB ancestor chain by SIZE.
set -u
cd /home/z/my-project
OUT=tmp/train9_probeF
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_LAYOUTNODE_DUMP="Lbt0;"
export MINIANDROID_LN_DUMP_LIMIT="512"
timeout 560 ./miniandroid/build/miniandroid run upload/canonical_apks/dooz_23_toplevel.apk \
  --width 1080 --height 1920 --frames 14 \
  --max-seconds 540 \
  --tap 765,1830@8 \
  -o "$OUT" 2>"$OUT/probeF.log"
echo "exit=$?"
echo "=== delegate dump count ==="
grep -c "^\[LN-DUMP\] obj#" "$OUT/probeF.log"
grep "LN-DUMP" "$OUT/probeF.log" | head -4
