#!/bin/bash
cd /home/z/my-project/miniandroid
make --no-print-directory dev-so -j1 > /tmp/w12_f2_build.log 2>&1 || { echo BUILD_FAIL; tail -4 /tmp/w12_f2_build.log; exit 1; }
A_PZ=/home/z/my-project/upload/handoff_apks/name.livitski.games.puzzle.android_2.apk
A_NP=/home/z/my-project/upload/handoff_apks/com.farmerbb.notepad_122.apk
./build_dev_so/miniandroid_dev run --max-seconds 150 --frames 60 --trace --click-test \
  -o /tmp/w12_f2_npuzzle --execution-mode real-dalvik $A_PZ > /tmp/w12_f2_npuzzle.log 2>&1
echo "npuzzle rc=$?"
./build_dev_so/miniandroid_dev run --max-seconds 60 --frames 10 --trace \
  -o /tmp/w12_f2_notepad --execution-mode real-dalvik $A_NP > /tmp/w12_f2_notepad.log 2>&1
echo "notepad rc=$?"
echo "== F712 npuzzle:"; grep -a "F712-MEASURE" /tmp/w12_f2_npuzzle.log | head -3
echo "== F712 notepad:"; grep -a "F712-MEASURE" /tmp/w12_f2_notepad.log | head -3
echo "== npuzzle verdict:"; python3 -c "
import json
s = json.load(open('/tmp/w12_f2_npuzzle/trace_summary.json'))
fa = s.get('frame_analysis', {})
print(fa.get('verdict'), 'app_px=', fa.get('app_owned_pixels'), 'ops=', fa.get('app_draw_ops'))"
echo "== npuzzle setTag/getTag evidence:"; grep -ac "setTag" /tmp/w12_f2_npuzzle.log; grep -a "setTag" /tmp/w12_f2_npuzzle.log | head -3 | cut -c1-150
echo FIX2_DONE
