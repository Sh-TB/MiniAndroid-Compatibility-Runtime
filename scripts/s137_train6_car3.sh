#!/bin/bash
# CONT-11 W10 internet-train-6 car 3: trace INSIDE all Lor1; frames
# (= SuspendingPointerInputModifierNodeImpl: J=onPointerEvent, M0=dispatchPointerEvent,
#  awaitPointerEventScope family). Questions:
#   Q1 does Lxz1;.I (CoroutineScope.launch) execute inside J?
#   Q2 does M0 execute (dispatchPointerEvent reached)?
#   Q3 does Lzh;.g (pointerAwaiter resume) fire inside M0?
#   Q4 does the launched body register a handler (awaitPointerEventScope sites)?
# Read-only stderr probes, bounded (256 cap). ZERO-LOG: artifacts stay in tmp/.
set -u
cd /home/z/my-project
OUT=tmp/s137_run3
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_CANVAS_OP_TRACE="$OUT/canvas_ops.jsonl"
export MINIANDROID_THROW_TRACE=1
export MINIANDROID_TOUCH_FIELD_TRACE=1
export MINIANDROID_INVOKE_TARGET_TRACE='Lor1;'
./miniandroid/build/miniandroid run upload/canonical_apks/dooz_23_toplevel.apk \
  --width 1080 --height 1920 \
  --frames 14 --frame-delay 500 \
  --max-seconds 540 \
  --tap 765,1830@5 \
  --dump-view-tree \
  -o "$OUT" 2>"$OUT/throw_sites.log"
echo "EXIT=$?"
echo "=== census of invoke targets inside Lor1; frames:"
grep 'INVOKE-TARGET' "$OUT/throw_sites.log" | sed -E 's/ pc=[0-9]+ recv=[^ ]* u[0-9]+=[0-9]+( u[0-9]+=[0-9]+)?//' | sort | uniq -c | sort -rn | head -30
echo "=== Lzh;.g resume fires:"
grep -c 'Lzh;->g' "$OUT/throw_sites.log" 2>/dev/null || echo 0
echo "=== raw tail:"
grep 'INVOKE-TARGET' "$OUT/throw_sites.log" | tail -25
