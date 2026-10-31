#!/usr/bin/env bash
# CONT-11 TRAIN-7 probe 5: did the coroutine state machine EVER start?
# Lru;.q = invokeSuspend (744 insns state machine), .o = create, .h = invoke bridge.
# Ls;.h0 = AbstractCoroutine.start (kotlinx), Lxz1;.I = launch.
set -u
cd /home/z/my-project
OUT=tmp/train7_pmc5_out
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_PMC_TRACE="Lru;|q,Lru;|h,Lru;|o,Ls;|h0,Lxz1;|I"
timeout 580 ./miniandroid/build/miniandroid run upload/canonical_apks/dooz_23_toplevel.apk \
  --width 1080 --height 1920 --frames 26 \
  --max-seconds 560 \
  --tap 765,1830@12 \
  -o "$OUT" 2>"$OUT/pmc5.log"
echo "exit=$?"
echo "=== ENTER counts ==="
grep "PMC] ENTER" "$OUT/pmc5.log" | sort | uniq -c | sort -rn
echo "=== Lru;.q pcs (first 40) ==="
grep "\[PMC\] Lru;.q " "$OUT/pmc5.log" | head -40
