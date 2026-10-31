#!/usr/bin/env bash
# CONT-11 TRAIN-9 probe H — THE HIT-TEST'S OWN READS.
# MINIANDROID_TOUCH_FIELD_TRACE=1 (every iget-wide during the touch
# dispatch, with recv ids) + FIELD-TRACE Lpz0;.D (every .D put/get all run).
# Answers: at dispatch, which coordinator objects does the hit-test read,
# and what .D values does it see for the FAB ancestor chain?
set -u
cd /home/z/my-project
OUT=tmp/train9_probeH
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_TOUCH_FIELD_TRACE="1"
export MINIANDROID_FIELD_TRACE="Lpz0;.D"
timeout 560 ./miniandroid/build/miniandroid run upload/canonical_apks/dooz_23_toplevel.apk \
  --width 1080 --height 1920 --frames 14 \
  --max-seconds 540 \
  --tap 765,1830@8 \
  -o "$OUT" 2>"$OUT/probeH.log"
echo "exit=$?"
echo "=== touch-window iget-wide reads (first 40) ==="
grep "HT-WIDE\|TOUCH-FIELD" "$OUT/probeH.log" | head -40
echo "=== .D get lines in dispatch window (recv ids) ==="
grep "FIELD-TRACE.* get .*Lpz0;\.D" "$OUT/probeH.log" | tail -40
