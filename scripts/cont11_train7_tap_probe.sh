#!/usr/bin/env bash
# CONT-11 TRAIN-7: dooz dispatch->hit-test dynamic probe.
# Source law (compose 1.6.7 pinned sources): dispatchTouchEvent ->
#   q()=isBadMotionEvent -> isAttachedToWindow -> s()=isPositionChanged (MOVE only)
#   -> m()=handleMotionEvent -> sendMotionEvent -> convertToPointerInputEvent
#   -> pointerInputEventProcessor.process -> root.hitTest -> addHitPath ->
#   dispatchChanges -> SuspendingPointerInputFilter (Ljr1;).
# s138 static graph proved pcs 45..240 exist; pcs 131-243 region unidentified
# (no getTag/floatToRawIntBits in 1.6.7 AndroidComposeView source).
# THIS run: dynamic PMC trace of the gates + the whole dispatchTouchEvent body.
set -u
cd /home/z/my-project
OUT=tmp/train7_pmc_out
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_PMC_TRACE="Lt4;|dispatchTouchEvent,Lt4;|q,Lt4;|s,Lt4;|m,Lqd;|<init>,Ljr1;|pointerInputHandler"
timeout 580 ./miniandroid/build/miniandroid run upload/canonical_apks/dooz_23_toplevel.apk \
  --width 1080 --height 1920 --frames 26 \
  --max-seconds 560 \
  --tap 765,1830@12 \
  -o "$OUT" 2>"$OUT/pmc.log"
echo "exit=$?"
echo "=== UI-EVENT lines ==="
grep -c "UI-EVENT" "$OUT/pmc.log" || true
grep "UI-EVENT" "$OUT/pmc.log" | head -10
echo "=== PMC ENTER lines ==="
grep "PMC] ENTER" "$OUT/pmc.log" | sort | uniq -c | sort -rn | head -20
echo "=== PMC total lines ==="
wc -l "$OUT/pmc.log"
