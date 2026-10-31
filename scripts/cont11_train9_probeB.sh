#!/usr/bin/env bash
# CONT-11 TRAIN-9 (fix train) probe B — placement writes vs the recursion
# driver. FIELD "Lpz0;.D" = coordinator position (real .D writes with recv
# coordinator ids); PMC "Lbt0;|u0" = onNodePlaced entries (the tail that
# drives child layoutChildren upstream).
set -u
cd /home/z/my-project
OUT=tmp/train9_probeB
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_PMC_TRACE="Lbt0;|u0"
export MINIANDROID_FIELD_TRACE="Lpz0;.D"
timeout 560 ./miniandroid/build/miniandroid run upload/canonical_apks/dooz_23_toplevel.apk \
  --width 1080 --height 1920 --frames 14 \
  --max-seconds 540 \
  --tap 765,1830@8 \
  -o "$OUT" 2>"$OUT/probeB.log"
echo "exit=$?"
echo "=== u0 (onNodePlaced) ENTER count ==="
grep -c "PMC] ENTER Lbt0;.u0" "$OUT/probeB.log"
echo "=== u0 invoke tail (layoutChildren reach?) ==="
grep "PMC] Lbt0;.u0 pc=" "$OUT/probeB.log" | grep " -> " | sort | uniq -c | sort -rn | head
echo "=== REAL .D placement writes (non-init) ==="
grep "FIELD-TRACE" "$OUT/probeB.log" | grep " put " | grep "Lpz0;\.D" | grep -v "<init>" | wc -l
echo "=== all real .D writes (recv + value) ==="
grep "FIELD-TRACE" "$OUT/probeB.log" | grep " put " | grep "Lpz0;\.D" | grep -v "<init>" | head -40
