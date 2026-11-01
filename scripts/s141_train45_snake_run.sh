#!/usr/bin/env bash
# s141_train45_snake_run.sh — Snake Neon REAL-INTERACTION run.
# Plan (s141_train45b_snake_plan.py): 6 direction taps, lag-robust for
# 0/1/2-frame tap lag; expected score=30 (3 foods), len=6, alive.
# Frame law: --frame-delay 110 -> tick 220ms = 2 frames exactly; tap at
# frame 2*T-1 lands by tick T+1 (inside the lag-robust envelope).
set -u
cd /home/z/my-project
OUT=run/s141/snake_neon
rm -rf "$OUT"; mkdir -p "$OUT"
APK=run/s141/snake_neon.apk
B=./miniandroid/build/miniandroid
# Phase 1: probe run with view-tree dump to pin button bounds
timeout 90 "$B" run "$APK" --width 1080 --height 1920 --frames 6 \
  --frame-delay 110 --max-seconds 80 --dump-view-tree -o "$OUT/probe" \
  > "$OUT/probe.log" 2>&1
echo "probe exit=$?"
rg -n "btn_left|btn_up|btn_down|btn_right|Button" "$OUT/probe/view_tree.txt" 2>/dev/null | head -12
