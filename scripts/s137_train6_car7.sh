#!/bin/bash
# CONT-11 W10 internet-train-6 car 7: pinpoint the invoke-interface dispatch
# fallthrough for PointerInputEventHandler.invoke on receiver Lpv;#6077.
# Existing env-gated diags (no code change):
#   MINIANDROID_F281_TRACE        -> [F281-IFACE-NAME] / [F281-IFACE-DEFAULT]
#   MINIANDROID_IFACE_FAIL_TRACE  -> [IFACE-RT] success-side return shapes
# plus INVOKE_TARGET_TRACE='Lru;' to anchor the q pc=168 call site.
set -u
cd /home/z/my-project
OUT=tmp/s137_run7
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_CANVAS_OP_TRACE="$OUT/canvas_ops.jsonl"
export MINIANDROID_THROW_TRACE=1
export MINIANDROID_TOUCH_FIELD_TRACE=1
export MINIANDROID_INVOKE_TARGET_TRACE='Lru;'
export MINIANDROID_F281_TRACE=1
export MINIANDROID_IFACE_FAIL_TRACE=1
./miniandroid/build/miniandroid run upload/canonical_apks/dooz_23_toplevel.apk \
  --width 1080 --height 1920 \
  --frames 14 --frame-delay 500 \
  --max-seconds 540 \
  --tap 765,1830@5 \
  --dump-view-tree \
  -o "$OUT" 2>"$OUT/throw_sites.log"
echo "EXIT=$?"
echo "=== F281 lines:"
grep -E 'F281-IFACE|INTERFACE-SIG|INTERFACE-DEFAULT|IFACE-RT' "$OUT/throw_sites.log" | head -40
grep -cE 'F281-IFACE|INTERFACE-SIG|INTERFACE-DEFAULT' "$OUT/throw_sites.log"
