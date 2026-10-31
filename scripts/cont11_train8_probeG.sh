#!/usr/bin/env bash
# CONT-11 TRAIN-8 probe G — the onNodePlaced gate:
#   Lug0;.k0 = InnerNodeCoordinator.placeAt = placeSelf + [if(!Lfr0;.n)] u0
#   FIELD-TRACE Lfr0;.n = isShallowPlacing flag: every read + write
#   PMC Lug0;|k0 = how many coordinator placeAts run + do they reach u0?
set -u
cd /home/z/my-project
OUT=tmp/train8_probeG
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_PMC_TRACE="Lug0;|k0,Lbt0;|u0"
export MINIANDROID_FIELD_TRACE="Lfr0;.n"
timeout 580 ./miniandroid/build/miniandroid run upload/canonical_apks/dooz_23_toplevel.apk \
  --width 1080 --height 1920 --frames 14 \
  --max-seconds 560 \
  --tap 765,1830@8 \
  -o "$OUT" 2>"$OUT/probeG.log"
echo "exit=$?"
echo "=== Lug0;.k0 ENTER count ==="
grep -c "PMC] ENTER Lug0;.k0" "$OUT/probeG.log"
echo "=== Lug0.k0 -> u0 reached? ==="
grep "PMC] Lug0;.k0 pc=" "$OUT/probeG.log" | awk '{print $4" "$5}' | sort | uniq -c | sort -rn | head
echo "=== Lfr0;.n puts (who sets isShallowPlacing) ==="
grep "FIELD-TRACE" "$OUT/probeG.log" | grep " put " | grep "Lfr0;\.n" | awk '{print $4, $6, $7}' | sort | uniq -c | sort -rn | head
echo "=== Lfr0;.n put value histogram ==="
grep "FIELD-TRACE" "$OUT/probeG.log" | grep " put " | grep "Lfr0;\.n" | awk '{print $NF}' | sort | uniq -c
echo "=== Lfr0;.n get count ==="
grep "FIELD-TRACE" "$OUT/probeG.log" | grep " get " | grep -c "Lfr0;\.n"
