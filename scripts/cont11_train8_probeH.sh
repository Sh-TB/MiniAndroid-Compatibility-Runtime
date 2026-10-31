#!/usr/bin/env bash
# CONT-11 TRAIN-8 probe H — the placement-lambda offsets:
# ARG-TRACE Lc61; = the placement scope statics g/i/j/k with (scope,
# placeable, x/y or packed J) — the offsets the measure-result lambdas
# actually computed for each child.
set -u
cd /home/z/my-project
OUT=tmp/train8_probeH
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_ARG_TRACE="Lc61;"
timeout 580 ./miniandroid/build/miniandroid run upload/canonical_apks/dooz_23_toplevel.apk \
  --width 1080 --height 1920 --frames 14 \
  --max-seconds 560 \
  --tap 765,1830@8 \
  -o "$OUT" 2>"$OUT/probeH.log"
echo "exit=$?"
grep -c "ARG-TRACE" "$OUT/probeH.log"
grep -A4 "ARG-TRACE.*Lc61;\.i\|ARG-TRACE.*Lc61;\.g" "$OUT/probeH.log" | head -60
