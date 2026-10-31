#!/usr/bin/env bash
# CONT-11 TRAIN-8 probe B — clean FIELD-TRACE of coordinator.position (Lpz0;.D)
# over the WHOLE run (no PMC contention), to re-derive the placement
# y-histogram without the 2400-PMC-budget window artifact, + the tap
# dispatch/hit-test window ([HT-WIDE] auto on D reads).
set -u
cd /home/z/my-project
OUT=tmp/train8_probeB
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_FIELD_TRACE="Lpz0;.D"
timeout 580 ./miniandroid/build/miniandroid run upload/canonical_apks/dooz_23_toplevel.apk \
  --width 1080 --height 1920 --frames 14 \
  --max-seconds 560 \
  --tap 765,1830@8 \
  -o "$OUT" 2>"$OUT/probeB.log"
echo "exit=$?"
echo "=== .D puts total ==="
grep -c "FIELD-TRACE.* put .*Lpz0;\.D" "$OUT/probeB.log"
echo "=== .D put values (packed J) with calling method ==="
grep "FIELD-TRACE" "$OUT/probeB.log" | grep " put " | grep "Lpz0;\.D" | head -40
echo "=== HT-WIDE reads during dispatch ==="
grep -c "HT-WIDE" "$OUT/probeB.log"
echo "=== field-trace budget exhausted? (lines) ==="
wc -l < "$OUT/probeB.log"
