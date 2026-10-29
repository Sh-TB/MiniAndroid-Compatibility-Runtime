#!/bin/bash
# CONT-11 W10 internet-train-6 car 8: WHO constructs Lor1; and with WHAT
# handler arg? S137a probe (MINIANDROID_LOR1_CTOR_TRACE) logs every
# Lor1;.<init> invoke site: caller, receiver id, handler arg class#id.
set -u
cd /home/z/my-project
OUT=tmp/s137_run8
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_CANVAS_OP_TRACE="$OUT/canvas_ops.jsonl"
export MINIANDROID_THROW_TRACE=1
export MINIANDROID_TOUCH_FIELD_TRACE=1
export MINIANDROID_LOR1_CTOR_TRACE=1
./miniandroid/build/miniandroid run upload/canonical_apks/dooz_23_toplevel.apk \
  --width 1080 --height 1920 \
  --frames 14 --frame-delay 500 \
  --max-seconds 540 \
  --tap 765,1830@5 \
  --dump-view-tree \
  -o "$OUT" 2>"$OUT/throw_sites.log"
echo "EXIT=$?"
echo "=== LOR1-CTOR lines:"
grep 'LOR1-CTOR' "$OUT/throw_sites.log"
echo "count: $(grep -c 'LOR1-CTOR' "$OUT/throw_sites.log")"
