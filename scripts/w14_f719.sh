#!/bin/bash
cd /home/z/my-project/miniandroid
T0=$(date +%s)
make --no-print-directory dev-so -j1 > /tmp/w14_f719_build.log 2>&1 || { echo BUILD_FAIL; grep -E "error" /tmp/w14_f719_build.log | head -5; exit 1; }
T1=$(date +%s)
echo "incremental_devso= $((T1-T0))s"
A_PZ=/home/z/my-project/upload/handoff_apks/name.livitski.games.puzzle.android_2.apk
./build_dev_so/miniandroid_dev run --max-seconds 150 --frames 30 --trace --click-test \
  -o /tmp/w14/pz_f719 --execution-mode real-dalvik $A_PZ > /tmp/w14/pz_f719.log 2>&1
echo "rc=$?"
echo "== item probes:"; grep -a "AdapterView item(s)\|ITEM_CLICK" /tmp/w14/pz_f719.log | head -8 | cut -c1-150
echo "== result chain:"; grep -a "G08-RESULT\|G07-FINISH\|G08-RESTORE\|G08-LAUNCH\|onActivityResult" /tmp/w14/pz_f719.log | head -14 | cut -c1-150
echo F719_DONE
