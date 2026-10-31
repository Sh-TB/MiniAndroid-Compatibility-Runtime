#!/usr/bin/env bash
# CONT-11 TRAIN-7 probe 6: which PointerInputEventHandler implementation runs,
# and where does the handler stop? (foundation 1.6.7 law: handler first calls
# awaitEachGesture -> awaitPointerEventScope = Lor1;.L0 -> suspendCancellableCoroutine)
set -u
cd /home/z/my-project
OUT=tmp/train7_pmc6_out
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_PMC_TRACE="Lj6;|invoke,Ldr;|invoke,Lkv1;|invoke,Lpv;|invoke,Lor1;|L0"
timeout 580 ./miniandroid/build/miniandroid run upload/canonical_apks/dooz_23_toplevel.apk \
  --width 1080 --height 1920 --frames 26 \
  --max-seconds 560 \
  --tap 765,1830@12 \
  -o "$OUT" 2>"$OUT/pmc6.log"
echo "exit=$?"
echo "=== ENTER counts ==="
grep "PMC] ENTER" "$OUT/pmc6.log" | sort | uniq -c | sort -rn
echo "=== Lj6;.invoke pcs (first 40) ==="
grep "\[PMC\] Lj6;.invoke " "$OUT/pmc6.log" | head -40
