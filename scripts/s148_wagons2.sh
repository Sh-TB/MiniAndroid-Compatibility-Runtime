#!/usr/bin/env bash
# s148_wagons2.sh — microtimer second timer (S147 tap law) + telegram rerun
set -u
B=/home/z/my-project/miniandroid/build/miniandroid
OUT=/home/z/my-project/run/s148_wagons
# microtimer: timer1 key-5 -> START, then timer2 key-3 -> START (S147 coords law)
MINIANDROID_T68_NODE_TRACE=0 "$B" run --execution-mode real-dalvik \
  --package dubrowgn.microtimer --data-root "$OUT/store_micro" \
  -o "$OUT/micro_2timer2" --max-seconds 200 --frames 80 \
  --tap 540,1470@12 --tap 880,1800@22 --tap 380,1470@40 --tap 880,1800@50 \
  > "$OUT/micro_2timer2.txt" 2>&1
echo "micro2 exit=$?"
"$B" run --execution-mode real-dalvik \
  --package org.forkgram.classic --data-root "$OUT/store_tg" \
  -o "$OUT/tg_run2" --max-seconds 150 --frames 60 \
  > "$OUT/tg_run2.txt" 2>&1
echo "tg2 exit=$?"
