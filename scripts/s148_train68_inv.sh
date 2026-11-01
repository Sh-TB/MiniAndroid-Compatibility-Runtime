#!/usr/bin/env bash
# s148_train68_inv.sh — TRAIN-68: the invoke-level trace inside Lor1;.J
# (the node dispatch arm) during the tap — the launch-call census per node.
set -u
B=/home/z/my-project/miniandroid/build/miniandroid
OUT=/home/z/my-project/run/s148_train68
STORE=$OUT/store_dooz
mkdir -p "$OUT"

MINIANDROID_INVOKE_TARGET_TRACE="Lor1;|J" \
MINIANDROID_T68_NODE_TRACE=1 \
"$B" run --execution-mode real-dalvik \
  --package io.github.yamin8000.dooz \
  --data-root "$STORE" \
  -o "$OUT/tap_inv" \
  --max-seconds 200 \
  --frames 45 \
  --tap 540,960@20 \
  > "$OUT/tap_inv.txt" 2>&1
echo "exit=$?"
rg -c 'INVOKE-TGT' "$OUT/tap_inv.txt" || true
