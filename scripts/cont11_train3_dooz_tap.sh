#!/usr/bin/env bash
# CONT-11 TRAIN-1: dooz board-gate tap run (600s budget).
# G3 law: board is wrapped in AnimatedVisibility(isGameStarted && !isRollingDices);
# only the "New game" ExtendedFloatingActionButton (~765,1830) starts the game.
# G5 law: engine --tap x,y@frame -> TouchDispatcher -> PerformClick.
set -u
cd /home/z/my-project
OUT=tmp/s134_train3_out
rm -rf "$OUT"; mkdir -p "$OUT"
export MINIANDROID_CANVAS_OP_TRACE="$OUT/canvas_ops.jsonl"
export MINIANDROID_THROW_TRACE=1
timeout 620 ./miniandroid/build/miniandroid run upload/canonical_apks/dooz_23_toplevel.apk \
  --width 1080 --height 1920 --frames 122 \
  --max-seconds 600 \
  --tap 765,1830@30 \
  --dump-view-tree -o "$OUT" 2>"$OUT/throw_sites.log"
echo "exit=$?"
ls "$OUT" | head -20
