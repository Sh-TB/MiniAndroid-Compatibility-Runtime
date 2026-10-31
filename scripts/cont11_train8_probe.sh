#!/usr/bin/env bash
# CONT-11 TRAIN-8 (fix train) probe A — the banked next-station questions:
#   Q1: did the 17 executed deferred blocks run the onNodePlaced (u0) ->
#       markNodeAndSubtreeAsPlaced (q0) tail?  PMC: v0 (placeAt), u0
#       (onNodePlaced), q0 (markNodeAndSubtreeAsPlaced), i1 (placeSelf)
#       + FIELD-TRACE Lbt0;.w (isPlaced writes/reads)
#   Q2: which sites were cycle-STUBBED during placement ([M3-19-CYCLE])
#   Q3: the 39 guard-skips on Lpz0;.D (placeSelf position==stored)
set -u
cd /home/z/my-project
OUT=tmp/train8_probeA
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_PMC_TRACE="Lbt0;|v0,Lbt0;|u0,Lbt0;|q0,Lpz0;|i1"
export MINIANDROID_FIELD_TRACE="Lbt0;.w"
timeout 580 ./miniandroid/build/miniandroid run upload/canonical_apks/dooz_23_toplevel.apk \
  --width 1080 --height 1920 --frames 14 \
  --max-seconds 560 \
  --tap 765,1830@8 \
  -o "$OUT" 2>"$OUT/probeA.log"
echo "exit=$?"
echo "=== PMC ENTER counts ==="
grep "PMC] ENTER" "$OUT/probeA.log" | sort | uniq -c | sort -rn
echo "=== v0 pc=0x55 deferred branch hits (snapshotObserver invoke) ==="
grep "Lbt0;.v0 pc=0x5" "$OUT/probeA.log" | sort | uniq -c | sort -rn | head
echo "=== u0 (onNodePlaced) sites ==="
grep "Lbt0;.u0 pc=" "$OUT/probeA.log" | head -8
echo "=== q0 (markNodeAndSubtreeAsPlaced) sites ==="
grep "Lbt0;.q0 pc=" "$OUT/probeA.log" | head -8
echo "=== CYCLE STUBS ==="
grep "M3-19-CYCLE" "$OUT/probeA.log" | head -12
echo "=== .w (isPlaced) puts ==="
grep "FIELD-TRACE" "$OUT/probeA.log" | grep " put " | grep "Lbt0;.w" | head -10
echo "=== .w get count vs put count ==="
grep "FIELD-TRACE" "$OUT/probeA.log" | grep -c " get .*Lbt0;\.w\| get .*\.w "
grep "FIELD-TRACE" "$OUT/probeA.log" | grep -c " put .*Lbt0;\.w\| put .*\.w "
