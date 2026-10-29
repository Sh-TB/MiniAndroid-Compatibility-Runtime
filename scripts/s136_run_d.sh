#!/bin/bash
# CONT-11 W7 internet-train-3 car: dooz tap-the-New-game-FAB experiment.
# Hypothesis (G3 gate law): board hidden behind AnimatedVisibility(isGameStarted) —
# tap (765,1830)@frame30 (FAB text pixel-verified at (765,1829.976) in train-2)
# should make isGameStarted=true -> after ~1.1s virtual dice-rolling the
# LazyVerticalGrid 9-cell board composes and issues draw ops in y:400-1500.
set -u
cd /home/z/my-project
OUT=tmp/s136_run_d
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_CANVAS_OP_TRACE="$OUT/canvas_ops.jsonl"
export MINIANDROID_THROW_TRACE=1
export MINIANDROID_INVOKE_TARGET_TRACE='Lce0;|b'
export MINIANDROID_TOUCH_FIELD_TRACE=1
b|b
./miniandroid/build/miniandroid run upload/canonical_apks/dooz_23_toplevel.apk \
  --width 1080 --height 1920 \
  --frames 14 --frame-delay 500 \
  --max-seconds 540 \
  --tap 765,1830@5 \
  --dump-view-tree \
  -o "$OUT" 2>"$OUT/throw_sites.log"
echo "EXIT=$?"
echo "=== artifacts:"
ls -la "$OUT" 2>/dev/null | head -12
