#!/usr/bin/env bash
# CONT-11 TRAIN-7 probe 3: does the filter (Lor1; = SuspendingPointerInputModifierNodeImpl)
# receive onPointerEvent? Watch the dispatch tail + the filter methods.
set -u
cd /home/z/my-project
OUT=tmp/train7_pmc3_out
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_PMC_TRACE="Lor1;|J,Lor1;|L0,Lor1;|k0,Lor1;|M0,Lce0;|b,Lce0;|a"
timeout 580 ./miniandroid/build/miniandroid run upload/canonical_apks/dooz_23_toplevel.apk \
  --width 1080 --height 1920 --frames 26 \
  --max-seconds 560 \
  --tap 765,1830@12 \
  -o "$OUT" 2>"$OUT/pmc3.log"
echo "exit=$?"
echo "=== UI-EVENT ==="
grep "UI-EVENT" "$OUT/pmc3.log" | head -6
echo "=== ENTER counts ==="
grep "PMC] ENTER" "$OUT/pmc3.log" | sort | uniq -c | sort -rn
echo "=== Lor1;.J (onPointerEvent) invokes ==="
grep "\[PMC\] Lor1;.J " "$OUT/pmc3.log" | head -30
echo "=== Lce0;.b invokes ==="
grep "\[PMC\] Lce0;.b " "$OUT/pmc3.log" | head -30
