#!/usr/bin/env bash
# CONT-11 TRAIN-8 probe C — the DECISIVE placement map.
# FIELD-TRACE Lbt0;.L = MeasurePassDelegate.lastPosition (J), written
# UNCONDITIONALLY by every placeAt (Lbt0;.v0) at pc=0x37/0x66 — captures
# EVERY placeAt call (receiver node + packed position) with NO budget
# contention. Answers: did the FAB/bottom-subtree placeAt ever run, and
# with what position?
set -u
cd /home/z/my-project
OUT=tmp/train8_probeC
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_FIELD_TRACE="Lbt0;.L"
timeout 580 ./miniandroid/build/miniandroid run upload/canonical_apks/dooz_23_toplevel.apk \
  --width 1080 --height 1920 --frames 14 \
  --max-seconds 560 \
  --tap 765,1830@8 \
  -o "$OUT" 2>"$OUT/probeC.log"
echo "exit=$?"
echo "=== .L puts (all placeAt calls) ==="
grep -c "FIELD-TRACE.* put .*Lbt0;\.L" "$OUT/probeC.log"
grep "FIELD-TRACE" "$OUT/probeC.log" | grep " put " | grep "Lbt0;\.L" | grep -v "<init>" | head -60
