#!/bin/bash
# CONT-11 W10 internet-train-6 car 6: trace INSIDE Lru; frames (R8-merged
# suspend-lambda class; h=create+invokeSuspend entry, q=invokeSuspend state
# machine). Expected healthy: h -> (o=create) -> q label-0 -> invoke-static
# 12549 (PointerInputEventHandler.invoke -> app pointerInput lambda).
# Any missing link localizes the sync-return death precisely.
set -u
cd /home/z/my-project
OUT=tmp/s137_run6
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_CANVAS_OP_TRACE="$OUT/canvas_ops.jsonl"
export MINIANDROID_THROW_TRACE=1
export MINIANDROID_TOUCH_FIELD_TRACE=1
export MINIANDROID_INVOKE_TARGET_TRACE='Lru;'
./miniandroid/build/miniandroid run upload/canonical_apks/dooz_23_toplevel.apk \
  --width 1080 --height 1920 \
  --frames 14 --frame-delay 500 \
  --max-seconds 540 \
  --tap 765,1830@5 \
  --dump-view-tree \
  -o "$OUT" 2>"$OUT/throw_sites.log"
echo "EXIT=$?"
echo "=== invokes inside Lru; frames:"
grep 'INVOKE-TARGET' "$OUT/throw_sites.log" | head -50
grep -c 'INVOKE-TARGET' "$OUT/throw_sites.log"
