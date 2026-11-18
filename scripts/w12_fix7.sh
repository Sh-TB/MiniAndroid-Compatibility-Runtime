#!/bin/bash
cd /home/z/my-project/miniandroid
make --no-print-directory dev-so -j1 > /tmp/w12_f7_build.log 2>&1 || { echo BUILD_FAIL; tail -4 /tmp/w12_f7_build.log; exit 1; }
A_PZ=/home/z/my-project/upload/handoff_apks/name.livitski.games.puzzle.android_2.apk
A_NP=/home/z/my-project/upload/handoff_apks/com.farmerbb.notepad_122.apk
./build_dev_so/miniandroid_dev run --max-seconds 150 --frames 30 --trace --click-test \
  -o /tmp/w12_f7_npuzzle --execution-mode real-dalvik $A_PZ > /tmp/w12_f7_npuzzle.log 2>&1
echo "npuzzle rc=$?"
./build_dev_so/miniandroid_dev run --max-seconds 90 --frames 30 --trace \
  -o /tmp/w12_f7_notepad --execution-mode real-dalvik $A_NP > /tmp/w12_f7_notepad.log 2>&1
echo "notepad rc=$?"
echo "== F714:"; grep -a "F714-MSPEC" /tmp/w12_f7_npuzzle.log | head -5
echo "== setTag:"; grep -ac "setTag" /tmp/w12_f7_npuzzle.log
echo "== setImageDrawable:"; grep -ac "setImageDrawable" /tmp/w12_f7_npuzzle.log
echo "== npuzzle verdict:"; python3 -c "
import json
s = json.load(open('/tmp/w12_f7_npuzzle/trace_summary.json'))
fa = s.get('frame_analysis', {})
print(fa.get('verdict'), 'app_px=', fa.get('app_owned_pixels'), 'ops=', fa.get('app_draw_ops'), 'visited=', fa.get('nodes_visited'))"
echo "== npuzzle F712 sync:"; grep -a "F712-SYNC" /tmp/w12_f7_npuzzle.log | head -3
echo "== notepad F713 probes:"; grep -ac "F713P-GSS\|F713-GSS-NULL" /tmp/w12_f7_notepad.log
echo "== notepad errors:"; grep -aE "Type:|Message:" /tmp/w12_f7_notepad/crash.log 2>/dev/null | head -6 | cut -c1-130
echo FIX7_DONE
