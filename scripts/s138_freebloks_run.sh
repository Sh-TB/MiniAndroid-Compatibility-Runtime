#!/usr/bin/env bash
# S138 train #9 (worklist): Freebloks vc184 FIRST RUN — the 3D board line
# (Compose UI + libgdx/ktx native 3D rendering, GPL-2.0).
set -u
cd /home/z/my-project
OUT=run/s138_freebloks
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_THROW_TRACE=1
export MINIANDROID_CANVAS_OP_TRACE="$OUT/canvas_ops.jsonl"
timeout 420 ./miniandroid/build/miniandroid run upload/canonical_apks/de.saschahlusiak.freebloks_184.apk \
  --width 1080 --height 1920 --frames 30 \
  --max-seconds 360 \
  --dump-view-tree -o "$OUT" 2>"$OUT/throw.log"
echo "exit=$?"
if [ -f "$OUT/screenshot.png" ]; then sha256sum "$OUT/screenshot.png" | cut -c1-16; else echo NO_SCREENSHOT; fi
