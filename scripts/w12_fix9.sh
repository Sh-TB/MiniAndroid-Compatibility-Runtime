#!/bin/bash
cd /home/z/my-project/miniandroid
make --no-print-directory dev-so -j1 > /tmp/w12_f9_build.log 2>&1 || { echo BUILD_FAIL; tail -4 /tmp/w12_f9_build.log; exit 1; }
A_PZ=/home/z/my-project/upload/handoff_apks/name.livitski.games.puzzle.android_2.apk
MINIANDROID_M71_TRACE=1 ./build_dev_so/miniandroid_dev run --max-seconds 150 --frames 30 --trace --click-test \
  -o /tmp/w12_f9_npuzzle --execution-mode real-dalvik $A_PZ > /tmp/w12_f9_npuzzle.log 2>&1
echo "npuzzle rc=$?"
echo "== M71:"; grep -a "M71-DISP" /tmp/w12_f9_npuzzle.log | head -4
echo "== F714:"; grep -a "F714-MSPEC" /tmp/w12_f9_npuzzle.log | head -4
echo "== setTag:"; grep -ac "setTag" /tmp/w12_f9_npuzzle.log
echo "== setImageDrawable:"; grep -ac "setImageDrawable" /tmp/w12_f9_npuzzle.log
echo "== verdict:"; python3 -c "
import json, hashlib
s = json.load(open('/tmp/w12_f9_npuzzle/trace_summary.json'))
fa = s.get('frame_analysis', {})
print(fa.get('verdict'), 'app_px=', fa.get('app_owned_pixels'), 'ops=', fa.get('app_draw_ops'), 'visited=', fa.get('nodes_visited'))
h = hashlib.sha256(open('/tmp/w12_f9_npuzzle/screenshot.png','rb').read()).hexdigest()[:16]
print('sha:', h)"
echo FIX9_DONE
