#!/usr/bin/env bash
# CONT-11 TRAIN-8 probe E — the post-tap LayoutNode heap dump: node ids,
# primitive fields (incl. measured sizes), coordinator pointers. Find the
# FAB node (409x147) and which nodes hold real geometry.
set -u
cd /home/z/my-project
OUT=tmp/train8_probeE
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_LAYOUTNODE_DUMP="Lel0;"
timeout 580 ./miniandroid/build/miniandroid run upload/canonical_apks/dooz_23_toplevel.apk \
  --width 1080 --height 1920 --frames 14 \
  --max-seconds 560 \
  --tap 765,1830@8 \
  -o "$OUT" 2>"$OUT/probeE.log"
echo "exit=$?"
echo "=== LN-DUMP line count ==="
grep -c "LN-DUMP" "$OUT/probeE.log"
grep "LN-DUMP" "$OUT/probeE.log" | head -50
