#!/bin/bash
cd /home/z/my-project/miniandroid
T0=$(date +%s)
make --no-print-directory dev-so -j1 > /tmp/w13_f718_build.log 2>&1 || { echo BUILD_FAIL; tail -4 /tmp/w13_f718_build.log; exit 1; }
T1=$(date +%s)
echo "incremental_devso= $((T1-T0))s"
A_PZ=/home/z/my-project/upload/handoff_apks/name.livitski.games.puzzle.android_2.apk
./build_dev_so/miniandroid_dev run --max-seconds 150 --frames 30 --trace --click-test \
  -o /tmp/w13_pz_f718 --execution-mode real-dalvik $A_PZ > /tmp/w13_pz_f718.log 2>&1
echo "rc=$?"
echo "== F718:"; grep -a "F718-REFLECT" /tmp/w13_pz_f718.log | head -3
echo "== NPE at init:"; grep -a "ARR-LEN-NULL\|EXC-PROPAGATE.*GamePlay" /tmp/w13_pz_f718.log | head -3 | cut -c1-140
echo "== setAdapter/adapter:"; grep -a "setAdapter\|getCount\|getView" /tmp/w13_pz_f718.log | head -4 | cut -c1-140
python3 -c "
import json, hashlib
s = json.load(open('/tmp/w13_pz_f718/trace_summary.json'))
fa = s.get('frame_analysis', {})
print('verdict:', fa.get('verdict'), 'app_px:', fa.get('app_owned_pixels'), 'ops:', fa.get('app_draw_ops'))
h = hashlib.sha256(open('/tmp/w13_pz_f718/screenshot.png','rb').read()).hexdigest()[:16]
print('sha:', h)"
echo F718_DONE
