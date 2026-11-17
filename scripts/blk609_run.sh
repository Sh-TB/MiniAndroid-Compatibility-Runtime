#!/bin/bash
# Issue #609 — Blockinger 1.8.2 gameplay completion run harness.
# Usage: blk609_run.sh <stage> [extra args...]
# Stages: menu | game
set -u
cd /home/z/my-project/miniandroid
APK=/home/z/my-project/upload/handoff_apks/org.blockinger.game_14.apk
EV=/home/z/my-project/evidence/issue609_blockinger
mkdir -p "$EV"
STAGE=${1:-menu}
shift || true
OUT="$EV/$STAGE"
mkdir -p "$OUT"
case "$STAGE" in
  menu)
    # Stage 1: boot to menu, render a few frames, dump view tree (button coords).
    timeout 180 ./build/miniandroid run "$APK" -o "$OUT" \
      --max-seconds 90 --frames 4 --frame-delay 500 \
      --dump-view-tree "$@" > "$OUT/run.log" 2>&1
    ;;
  game)
    # Stage 2+: taps passed as extra args (each "x,y@frame").
    timeout 300 ./build/miniandroid run "$APK" -o "$OUT" \
      --max-seconds 240 --frames 40 --frame-delay 500 \
      --dump-view-tree "$@" > "$OUT/run.log" 2>&1
    ;;
esac
rc=$?
echo "== stage=$STAGE rc=$rc =="
grep -E "Status:|Frames Rendered:|Errors:|Screenshot:|TAP|CRASH|FATAL" "$OUT/run.log" | head -20
ls "$OUT/frames/" 2>/dev/null | tail -5
