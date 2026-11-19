#!/bin/bash
cd /home/z/my-project/miniandroid
T0=$(date +%s)
make --no-print-directory all -j1 > /tmp/w14_probe_build.log 2>&1 || { echo STATIC_FAIL; grep -E "error" /tmp/w14_probe_build.log | head -5; exit 1; }
T1=$(date +%s)
make --no-print-directory dev-so -j1 >> /tmp/w14_probe_build.log 2>&1 || { echo DEVSO_FAIL; tail -3 /tmp/w14_probe_build.log; exit 1; }
T2=$(date +%s)
echo "TIMING: static_inc=$((T1-T0))s devso_relink=$((T2-T1))s"
A_PZ=/home/z/my-project/upload/handoff_apks/name.livitski.games.puzzle.android_2.apk
./build_dev_so/miniandroid_dev run --max-seconds 150 --frames 30 --trace --click-test \
  -o /tmp/w14/pz_probe --execution-mode real-dalvik $A_PZ > /tmp/w14/pz_probe.log 2>&1
echo "rc=$?"
echo "== F719-STORE:"; grep -a "F719-STORE" /tmp/w14/pz_probe.log | head -4
echo "== item probes:"; grep -a "AdapterView item(s)\|ITEM_CLICK_TAP\|ITEM_CLICK " /tmp/w14/pz_probe.log | head -8 | cut -c1-140
echo "== result chain:"; grep -a "G08-RESULT\|G07-FINISH\|G08-RESTORE.*onActivityResult\|G08-DBG" /tmp/w14/pz_probe.log | head -10 | cut -c1-140
echo PROBE_DONE
