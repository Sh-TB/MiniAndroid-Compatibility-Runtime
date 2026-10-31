#!/usr/bin/env bash
# CONT-11 TRAIN-7 probe 8: hit-test geometry.
# HT-WIDE = every packed-IntOffset/IntSize read on compose node classes during
# the touch dispatch (what bounds the hit-test walk consumed).
# LN-DUMP = post-touch LayoutNode primitive-field dump (placed geometry?).
set -u
cd /home/z/my-project
OUT=tmp/train7_pmc8_out
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_TOUCH_FIELD_TRACE=1
export MINIANDROID_LAYOUTNODE_DUMP=Lel0;
timeout 580 ./miniandroid/build/miniandroid run upload/canonical_apks/dooz_23_toplevel.apk \
  --width 1080 --height 1920 --frames 16 \
  --max-seconds 560 \
  --tap 765,1830@8 \
  -o "$OUT" 2>"$OUT/pmc8.log"
echo "exit=$?"
echo "=== HT-WIDE count ==="
grep -c "HT-WIDE" "$OUT/pmc8.log" || true
echo "=== HT-WIDE sample (first 30) ==="
grep "HT-WIDE" "$OUT/pmc8.log" | head -30
