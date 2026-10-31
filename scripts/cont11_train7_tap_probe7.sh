#!/usr/bin/env bash
# CONT-11 TRAIN-7 probe 7: the suspension point internals.
# Law chain: Lru;.q(label) -> builds Let;(I,Object)+Lg8;/Lc7;/Lg; ->
#   Ljn;.o(q50,block,cont) -> Let;.a(r50,cont) [SUSPENDS FOREVER]
set -u
cd /home/z/my-project
OUT=tmp/train7_pmc7_out
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_PMC_TRACE="Let;|a,Ljn;|o,Lg;|q,Lc7;|q,Lg8;|q,Lor1;|L0"
timeout 580 ./miniandroid/build/miniandroid run upload/canonical_apks/dooz_23_toplevel.apk \
  --width 1080 --height 1920 --frames 26 \
  --max-seconds 560 \
  --tap 765,1830@12 \
  -o "$OUT" 2>"$OUT/pmc7.log"
echo "exit=$?"
echo "=== ENTER counts ==="
grep "PMC] ENTER" "$OUT/pmc7.log" | sort | uniq -c | sort -rn
echo "=== Let;.a pcs (first 45) ==="
grep "\[PMC\] Let;.a " "$OUT/pmc7.log" | head -45
