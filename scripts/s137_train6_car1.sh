#!/bin/bash
# CONT-11 W10 internet-train-6 car 1: isolate SuspendingPointerInputModifierNodeImpl.
# Train-5 next leg (evidence train5_dooz_awaiter_scope.json /next_leg_precise):
#   (a) does ANY onPointerEvent frame execute during the touch window? -> PTE_TRACE
#   (b) inside Lhz0;.e dispatchForKind, which class does the A=4 virtual filter
#       invoke resolve to, per event? -> INVOKE_TARGET_TRACE='Lhz0;|e'
# Read-only stderr probes, bounded. ZERO-LOG: artifacts stay in tmp/.
set -u
cd /home/z/my-project
OUT=tmp/s137_run1
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_CANVAS_OP_TRACE="$OUT/canvas_ops.jsonl"
export MINIANDROID_THROW_TRACE=1
export MINIANDROID_TOUCH_FIELD_TRACE=1
export MINIANDROID_PTE_TRACE=1
export MINIANDROID_INVOKE_TARGET_TRACE='Lhz0;|e'
./miniandroid/build/miniandroid run upload/canonical_apks/dooz_23_toplevel.apk \
  --width 1080 --height 1920 \
  --frames 14 --frame-delay 500 \
  --max-seconds 540 \
  --tap 765,1830@5 \
  --dump-view-tree \
  -o "$OUT" 2>"$OUT/throw_sites.log"
echo "EXIT=$?"
echo "=== PTE-DISPATCH lines:"
grep -c 'PTE-DISPATCH' "$OUT/throw_sites.log" 2>/dev/null || echo 0
grep 'PTE-DISPATCH' "$OUT/throw_sites.log" 2>/dev/null | head -40
echo "=== ITT (invoke target) lines:"
grep -c 'ITT' "$OUT/throw_sites.log" 2>/dev/null || echo 0
grep 'ITT' "$OUT/throw_sites.log" 2>/dev/null | head -60
echo "=== artifacts:"
ls -la "$OUT" 2>/dev/null | head -12
