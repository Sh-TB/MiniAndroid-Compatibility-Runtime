#!/bin/bash
cd /home/z/my-project/miniandroid
A_PZ=/home/z/my-project/upload/handoff_apks/name.livitski.games.puzzle.android_2.apk
MINIANDROID_M71_TRACE=1 ./build_dev_so/miniandroid_dev run --max-seconds 150 --frames 30 --trace \
  -o /tmp/w12_f8_npuzzle --execution-mode real-dalvik $A_PZ > /tmp/w12_f8_npuzzle.log 2>&1
echo "rc=$?"
grep -a "M71-DISP" /tmp/w12_f8_npuzzle.log | head -8
echo "==="; grep -a "DEX-MEASURE" /tmp/w12_f8_npuzzle.log | head -4
echo FIX8_DONE
