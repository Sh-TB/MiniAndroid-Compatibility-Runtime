#!/bin/bash
cd /home/z/my-project/miniandroid
T0=$(date +%s)
make --no-print-directory all -j1 > /tmp/w15_build.log 2>&1 || { echo "STATIC_FAIL"; tail -3 /tmp/w15_build.log; exit 1; }
T1=$(date +%s)
make --no-print-directory test-core -j1 >> /tmp/w15_build.log 2>&1
T2=$(date +%s)
make --no-print-directory dev-so -j1 >> /tmp/w15_build.log 2>&1 || { echo "DEVSO_FAIL"; exit 1; }
T3=$(date +%s)
echo "TIMING: static=$((T1-T0))s tests=$((T2-T1))s devso=$((T3-T2))s"
A_PZ=/home/z/my-project/upload/handoff_apks/name.livitski.games.puzzle.android_2.apk
mkdir -p /tmp/w15
./build_dev_so/miniandroid_dev run --max-seconds 200 --frames 50 --trace --tap 197,112@25 \
  -o /tmp/w15/pz_base --execution-mode real-dalvik $A_PZ > /tmp/w15/pz_base.log 2>&1
echo "rc=$?"
grep -a "ITEM_CLICK adapter=156\|G08-RESULT\|GamePlay.onActivityResult" /tmp/w15/pz_base.log | head -3 | cut -c1-120
echo REBASE_DONE
