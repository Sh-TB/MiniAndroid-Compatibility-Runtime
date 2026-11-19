#!/bin/bash
cd /home/z/my-project/miniandroid
T0=$(date +%s)
make --no-print-directory all -j1 > /tmp/w14_build.log 2>&1 || { echo "STATIC_FAIL"; tail -3 /tmp/w14_build.log; exit 1; }
T1=$(date +%s)
make --no-print-directory test-core -j1 >> /tmp/w14_build.log 2>&1
T2=$(date +%s)
make --no-print-directory dev-so -j1 >> /tmp/w14_build.log 2>&1 || { echo "DEVSO_FAIL"; exit 1; }
T3=$(date +%s)
echo "TIMING: static=$((T1-T0))s tests=$((T2-T1))s devso=$((T3-T2))s"
A_PZ=/home/z/my-project/upload/handoff_apks/name.livitski.games.puzzle.android_2.apk
mkdir -p /tmp/w14
./build_dev_so/miniandroid_dev run --max-seconds 150 --frames 30 --trace --click-test \
  -o /tmp/w14/pz_base --execution-mode real-dalvik $A_PZ > /tmp/w14/pz_base.log 2>&1
echo "rc=$?"; grep -a "F717-INFLATE\|F718-REFLECT\|C102-ADAPTER" /tmp/w14/pz_base.log | head -3 | cut -c1-120
echo REBASE_DONE
