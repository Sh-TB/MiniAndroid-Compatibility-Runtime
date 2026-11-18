#!/bin/bash
# W12 Phase 1: 3-run baseline of Notepad + n-Puzzle with full evidence
cd /home/z/my-project/miniandroid
mkdir -p /tmp/w12_baseline
A_NP=/home/z/my-project/upload/handoff_apks/com.farmerbb.notepad_122.apk
A_PZ=/home/z/my-project/upload/handoff_apks/name.livitski.games.puzzle.android_2.apk
for RUN in 1 2 3; do
  ./build_dev_so/miniandroid_dev run --max-seconds 150 --frames 60 --trace --dump-api-trace --dump-view-tree \
    -o /tmp/w12_baseline/notepad_r$RUN --execution-mode real-dalvik $A_NP > /tmp/w12_baseline/notepad_r$RUN.log 2>&1
  echo "notepad r$RUN rc=$?"
  ./build_dev_so/miniandroid_dev run --max-seconds 150 --frames 60 --trace --dump-api-trace --dump-view-tree --click-test \
    -o /tmp/w12_baseline/npuzzle_r$RUN --execution-mode real-dalvik $A_PZ > /tmp/w12_baseline/npuzzle_r$RUN.log 2>&1
  echo "npuzzle r$RUN rc=$?"
done
# one interaction run for npuzzle: tap footer license link
./build_dev_so/miniandroid_dev run --max-seconds 150 --frames 60 --trace --tap 985,1898 --dump-api-trace \
  -o /tmp/w12_baseline/npuzzle_tap --execution-mode real-dalvik $A_PZ > /tmp/w12_baseline/npuzzle_tap.log 2>&1
echo "npuzzle tap rc=$?"
echo BASELINES_DONE
