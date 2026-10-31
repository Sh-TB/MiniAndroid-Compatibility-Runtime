#!/usr/bin/env bash
# CONT-11 TRAIN-7 probe 2: is process() reached? does hitTest run?
# Watchlist v2 (source-law driven, exact class|method pairs):
#   Lt4;|H    = sendMotionEvent (entered in probe 1, both DOWN+UP)
#   Lhu0;|c   = convertToPointerInputEvent
#   Lfj;|a    = PointerInputEventProcessor.process
#   Lel0;|k   = LayoutNode.hitTest
#   Lqd;|<init> = the unidentified pair-constructed class
# Plus static dump of any Ljr1; method entry during dispatch (s138 cross-check).
set -u
cd /home/z/my-project
OUT=tmp/train7_pmc2_out
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_PMC_TRACE="Lt4;|H,Lhu0;|c,Lfj;|a,Lel0;|k,Lqd;|<init>"
export MINIANDROID_INVOKE_SITES="Ljr1;|"
timeout 580 ./miniandroid/build/miniandroid run upload/canonical_apks/dooz_23_toplevel.apk \
  --width 1080 --height 1920 --frames 26 \
  --max-seconds 560 \
  --tap 765,1830@12 \
  -o "$OUT" 2>"$OUT/pmc2.log"
echo "exit=$?"
echo "=== UI-EVENT ==="
grep "UI-EVENT" "$OUT/pmc2.log" | head -6
echo "=== ENTER counts ==="
grep "PMC] ENTER" "$OUT/pmc2.log" | sort | uniq -c | sort -rn
echo "=== Lhu0;.c executed invokes ==="
grep "\[PMC\] Lhu0;.c " "$OUT/pmc2.log" | head -40
echo "=== Lfj;.a (process) executed invokes ==="
grep "\[PMC\] Lfj;.a " "$OUT/pmc2.log" | head -40
echo "=== Ljr1; static dumps ==="
grep -c "INVOKE-SITE" "$OUT/pmc2.log" || true
