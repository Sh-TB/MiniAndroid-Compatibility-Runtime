#!/usr/bin/env bash
# CONT-11 TRAIN-9 (fix train) probe D — the second-pass exception census.
# Banked: 45x Leo;.P (ensureActive) post-pass-1 at log line ~29953 (TRAIN-7
# baseline). Are these the RE-placement pass dying (u0 placeOrder family)?
# Clean run (no PMC/FIELD probes) so the census is budget-free.
set -u
cd /home/z/my-project
OUT=tmp/train9_probeD
rm -rf "$OUT"; mkdir -p "$OUT"
timeout 560 ./miniandroid/build/miniandroid run upload/canonical_apks/dooz_23_toplevel.apk \
  --width 1080 --height 1920 --frames 14 \
  --max-seconds 540 \
  --tap 765,1830@8 \
  -o "$OUT" 2>"$OUT/probeD.log"
echo "exit=$?"
echo "=== run summary line ==="
grep -E "SUCCESS|FAIL|frames" "$OUT/probeD.log" | tail -3
echo "=== Leo;.P (ensureActive) exception census ==="
grep -c "Leo;\.P" "$OUT/probeD.log"
echo "=== exception families (all, top 12) ==="
grep -oE "(CancellationException|IllegalStateException|[A-Za-z.]*Exception)" "$OUT/probeD.log" | sort | uniq -c | sort -rn | head -12
echo "=== first Leo;.P context (8 lines around first hit) ==="
FIRST=$(grep -n "Leo;\.P" "$OUT/probeD.log" | head -1 | cut -d: -f1)
if [ -n "$FIRST" ]; then sed -n "$((FIRST-4)),$((FIRST+4))p" "$OUT/probeD.log"; fi
echo "=== M3-19-CYCLE stubs ==="
grep -c "M3-19-CYCLE" "$OUT/probeD.log"
