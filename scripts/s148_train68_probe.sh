#!/usr/bin/env bash
# s148_train68_probe.sh — TRAIN-68: the pointer-input NODE census (T68 probe).
# Deciding experiment: how many SuspendingPointerInputModifierNodeImpl (Lor1;)
# nodes exist, which ones get the DOWN/UP dispatch (M0/J), which LAUNCH their
# block (L0) — is the clickable's detectTapAndPress node in the hit path at all?
set -u
B=/home/z/my-project/miniandroid/build/miniandroid
OUT=/home/z/my-project/run/s148_train68
STORE=$OUT/store_dooz
APK=/home/z/my-project/run/s147_train67/store_dooz/data/app/io.github.yamin8000.dooz/base.apk
mkdir -p "$OUT"

# fresh install (per-session run dirs)
rm -rf "$STORE"
"$B" install "$APK" --data-root "$STORE" > "$OUT/install.txt" 2>&1

# run with the T68 node trace + T67 label trace (the machine chain), tap the cell
MINIANDROID_T68_NODE_TRACE=1 \
MINIANDROID_T67_LABEL_TRACE=1 \
MAX_SECONDS=200 \
"$B" run --execution-mode real-dalvik \
  --package io.github.yamin8000.dooz \
  --data-root "$STORE" \
  -o "$OUT/tap_t68" \
  --max-seconds 200 \
  --frames 45 \
  --tap 540,960@20 \
  > "$OUT/tap_t68.txt" 2>&1
echo "exit=$?"
wc -l "$OUT/tap_t68.txt"
