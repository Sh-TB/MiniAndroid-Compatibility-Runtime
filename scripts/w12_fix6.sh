#!/bin/bash
cd /home/z/my-project/miniandroid
rm -f build/runtime/execution_engine.o
make --no-print-directory all -j1 > /tmp/w12_f6_build.log 2>&1 || { echo BUILD_FAIL; tail -4 /tmp/w12_f6_build.log; exit 1; }
make --no-print-directory dev-so -j1 >> /tmp/w12_f6_build.log 2>&1
A_PZ=/home/z/my-project/upload/handoff_apks/name.livitski.games.puzzle.android_2.apk
./build_dev_so/miniandroid_dev run --max-seconds 150 --frames 30 --trace --click-test \
  -o /tmp/w12_f6_npuzzle --execution-mode real-dalvik $A_PZ > /tmp/w12_f6_npuzzle.log 2>&1
echo "npuzzle rc=$?"
echo "== F712 sync:"; grep -a "F712-SYNC" /tmp/w12_f6_npuzzle.log | head -4
echo "== M71 dispatch:"; grep -ac "M71-DISP" /tmp/w12_f6_npuzzle.log; MINIANDROID_M71_TRACE=1 true
echo "== setTag evidence:"; grep -ac "setTag" /tmp/w12_f6_npuzzle.log
echo "== verdict:"; python3 -c "
import json
s = json.load(open('/tmp/w12_f6_npuzzle/trace_summary.json'))
fa = s.get('frame_analysis', {})
print(fa.get('verdict'), 'app_px=', fa.get('app_owned_pixels'), 'ops=', fa.get('app_draw_ops'), 'visited=', fa.get('nodes_visited'))"
echo FIX6_DONE
