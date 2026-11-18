#!/bin/bash
cd /home/z/my-project/miniandroid
make --no-print-directory all -j1 > /tmp/w12_f1_build.log 2>&1 || { echo "BUILD_FAIL"; exit 1; }
make --no-print-directory test-core -j1 >> /tmp/w12_f1_build.log 2>&1
make --no-print-directory build/tests/f709_filedescriptor_law_test >> /tmp/w12_f1_build.log 2>&1
./build/tests/f709_filedescriptor_law_test > /tmp/w12_f1_t709.log 2>&1
make --no-print-directory dev-so -j1 >> /tmp/w12_f1_build.log 2>&1
make --no-print-directory dev-so-test -j1 >> /tmp/w12_f1_build.log 2>&1
echo "battery: $(grep -c '\[PASS\]' /tmp/w12_f1_build.log) dev_pass=$(grep -c '\[PASS\]' /tmp/w12_f1_build.log) t709=$(grep -c PASS /tmp/w12_f1_t709.log)"
A_PZ=/home/z/my-project/upload/handoff_apks/name.livitski.games.puzzle.android_2.apk
./build_dev_so/miniandroid_dev run --max-seconds 150 --frames 60 --trace --click-test \
  -o /tmp/w12_fix1_npuzzle --execution-mode real-dalvik $A_PZ > /tmp/w12_fix1_npuzzle.log 2>&1
echo "npuzzle rc=$?"
A_NP=/home/z/my-project/upload/handoff_apks/com.farmerbb.notepad_122.apk
./build_dev_so/miniandroid_dev run --max-seconds 150 --frames 60 --trace \
  -o /tmp/w12_fix1_notepad --execution-mode real-dalvik $A_NP > /tmp/w12_fix1_notepad.log 2>&1
echo "notepad rc=$?"
echo "F712:"; grep -a "F712-MEASURE" /tmp/w12_fix1_npuzzle.log | head -3
echo "F713:"; grep -a "F713-GSS-NULL" /tmp/w12_fix1_notepad.log | head -4
echo FIX1_DONE
