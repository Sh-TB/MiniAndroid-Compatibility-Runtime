#!/bin/bash
cd /home/z/my-project/miniandroid
rm -f build/runtime/execution_engine.o
make --no-print-directory all -j1 > /tmp/w12_f5_build.log 2>&1 || { echo BUILD_FAIL; tail -4 /tmp/w12_f5_build.log; exit 1; }
make --no-print-directory dev-so -j1 >> /tmp/w12_f5_build.log 2>&1
A_PZ=/home/z/my-project/upload/handoff_apks/name.livitski.games.puzzle.android_2.apk
./build_dev_so/miniandroid_dev run --max-seconds 150 --frames 30 --trace \
  -o /tmp/w12_f5_npuzzle --execution-mode real-dalvik $A_PZ > /tmp/w12_f5_npuzzle.log 2>&1
echo "npuzzle rc=$?"
echo "== F712 probe:"; grep -a "F712-PROBE\|F712-MEASURE" /tmp/w12_f5_npuzzle.log | head -8
echo FIX5_DONE
