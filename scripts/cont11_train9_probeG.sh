#!/usr/bin/env bash
# CONT-11 TRAIN-9 probe G — THE COORDINATOR GRAPH AT DISPATCH TIME.
# LN-DUMP Lpz0; (NodeCoordinator: .D = position J, wrappedBy/wrappedByChain
# fields) fires after the dispatched tap — exactly what the hit-test walks.
# Correlates with probeE's node graph (x/I coordinator refs) to answer:
# does the FAB's ancestor coordinator chain hold the real offsets
# (0,1710)/(617,0) at hit-test time, or only the modifier-chain objects?
set -u
cd /home/z/my-project
OUT=tmp/train9_probeG
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_LAYOUTNODE_DUMP="Lpz0;"
export MINIANDROID_LN_DUMP_LIMIT="512"
timeout 560 ./miniandroid/build/miniandroid run upload/canonical_apks/dooz_23_toplevel.apk \
  --width 1080 --height 1920 --frames 14 \
  --max-seconds 540 \
  --tap 765,1830@8 \
  -o "$OUT" 2>"$OUT/probeG.log"
echo "exit=$?"
echo "=== coordinator dump count ==="
grep -c "^\[LN-DUMP\] obj#" "$OUT/probeG.log"
echo "=== FAB-family coordinators (12190..12260) ==="
grep "LN-DUMP" "$OUT/probeG.log" | grep -E "obj#122[0-5][0-9]" | head -6
echo "=== bottom-bar-era coordinators (12000..12100) ==="
grep "LN-DUMP" "$OUT/probeG.log" | grep -E "obj#120[0-9][0-9]" | head -6
