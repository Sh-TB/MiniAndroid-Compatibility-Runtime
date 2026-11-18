#!/bin/bash
cd /home/z/my-project/miniandroid
rm -f build/runtime/execution_engine.o
make --no-print-directory all -j1 > /tmp/w12_f4_build.log 2>&1 || { echo BUILD_FAIL; tail -4 /tmp/w12_f4_build.log; exit 1; }
make --no-print-directory test-core -j1 >> /tmp/w12_f4_build.log 2>&1
make --no-print-directory dev-so -j1 >> /tmp/w12_f4_build.log 2>&1
make --no-print-directory dev-so-test -j1 >> /tmp/w12_f4_build.log 2>&1
echo "battery=$(grep -c '\[PASS\]' /tmp/w12_f4_build.log)"
A_PZ=/home/z/my-project/upload/handoff_apks/name.livitski.games.puzzle.android_2.apk
A_NP=/home/z/my-project/upload/handoff_apks/com.farmerbb.notepad_122.apk
./build_dev_so/miniandroid_dev run --max-seconds 150 --frames 60 --trace --click-test \
  -o /tmp/w12_f4_npuzzle --execution-mode real-dalvik $A_PZ > /tmp/w12_f4_npuzzle.log 2>&1
echo "npuzzle rc=$?"
./build_dev_so/miniandroid_dev run --max-seconds 60 --frames 10 --trace \
  -o /tmp/w12_f4_notepad --execution-mode real-dalvik $A_NP > /tmp/w12_f4_notepad.log 2>&1
echo "notepad rc=$?"
echo "== F712 npuzzle:"; grep -a "F712-MEASURE" /tmp/w12_f4_npuzzle.log | head -4
echo "== F712 notepad:"; grep -a "F712-MEASURE" /tmp/w12_f4_notepad.log | head -4
echo "== npuzzle verdict:"; python3 -c "
import json
s = json.load(open('/tmp/w12_f4_npuzzle/trace_summary.json'))
fa = s.get('frame_analysis', {})
print(fa.get('verdict'), 'app_px=', fa.get('app_owned_pixels'), 'ops=', fa.get('app_draw_ops'))"
echo "== npuzzle tag evidence (setTag prints):"; grep -ac "setTag" /tmp/w12_f4_npuzzle.log
echo "== click:"; grep -a "\[CLICK-TEST\]" /tmp/w12_f4_npuzzle.log | head -2
echo FIX4_DONE
