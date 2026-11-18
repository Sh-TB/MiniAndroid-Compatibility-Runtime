#!/bin/bash
cd /home/z/my-project/miniandroid
T0=$(date +%s)
make --no-print-directory all -j1 > /tmp/w13_build.log 2>&1 || { echo "STATIC_BUILD_FAIL"; tail -3 /tmp/w12_build.log; exit 1; }
T1=$(date +%s)
make --no-print-directory test-core -j1 >> /tmp/w13_build.log 2>&1
make --no-print-directory build/tests/f709_filedescriptor_law_test build/tests/f714_measurespec_law_test build/tests/f716_view_tag_law_test >> /tmp/w13_build.log 2>&1
T2=$(date +%s)
make --no-print-directory dev-so -j1 >> /tmp/w13_build.log 2>&1 || { echo "DEVSO_FAIL"; exit 1; }
T3=$(date +%s)
make --no-print-directory dev-so-test -j1 >> /tmp/w13_build.log 2>&1
T4=$(date +%s)
# incremental dev-so cycle measurement: touch a PIC TU, rebuild dev-so only
touch src/dex/dalvik_bridge.cpp
make --no-print-directory dev-so -j1 >> /tmp/w13_build.log 2>&1
T5=$(date +%s)
echo "TIMING: full_static=$((T1-T0))s tests_build=$((T2-T1))s dev_so=$((T3-T2))s devso_test=$((T4-T3))s incremental_devso_single_tu=$((T5-T4))s"
A_PZ=/home/z/my-project/upload/handoff_apks/name.livitski.games.puzzle.android_2.apk
./build_dev_so/miniandroid_dev run --max-seconds 150 --frames 30 --trace --click-test \
  -o /tmp/w13_pz_base --execution-mode real-dalvik $A_PZ > /tmp/w13_pz_base.log 2>&1
echo "npuzzle baseline rc=$?"
grep -a "S123-SA\|G08-LIFECYCLE.*ImageSelection" /tmp/w13_pz_base.log | head -3 | cut -c1-140
echo REBUILD_DONE
