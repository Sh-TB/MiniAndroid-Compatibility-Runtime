#!/usr/bin/env bash
# CONT-11 TRAIN-8 probe D — the placement call graph without budget
# contention: PMC on Lbt0;|v0 ONLY (placeAt ~87 calls x ~10 invoke-site
# prints fits the 2400 budget). Correlate with probe C's .L position map.
set -u
cd /home/z/my-project
OUT=tmp/train8_probeD
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_PMC_TRACE="Lbt0;|v0"
timeout 580 ./miniandroid/build/miniandroid run upload/canonical_apks/dooz_23_toplevel.apk \
  --width 1080 --height 1920 --frames 14 \
  --max-seconds 560 \
  --tap 765,1830@8 \
  -o "$OUT" 2>"$OUT/probeD.log"
echo "exit=$?"
echo "=== v0 ENTER count ==="
grep -c "PMC] ENTER Lbt0;.v0" "$OUT/probeD.log"
echo "=== v0 invoke-site histogram (who places children) ==="
grep "PMC] Lbt0;.v0 pc=" "$OUT/probeD.log" | awk '{print $4" "$5}' | sort | uniq -c | sort -rn | head -20
echo "=== budget exhausted? (PMC lines total) ==="
grep -c "PMC]" "$OUT/probeD.log"
