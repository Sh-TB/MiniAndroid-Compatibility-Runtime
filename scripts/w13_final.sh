#!/bin/bash
cd /home/z/my-project/miniandroid
T0=$(date +%s)
make --no-print-directory all -j1 > /tmp/w13_final_build.log 2>&1 || { echo STATIC_FAIL; tail -3 /tmp/w13_final_build.log; exit 1; }
T1=$(date +%s)
make --no-print-directory test-core -j1 >> /tmp/w13_final_build.log 2>&1
make --no-print-directory build/tests/f709_filedescriptor_law_test build/tests/f714_measurespec_law_test build/tests/f716_view_tag_law_test >> /tmp/w13_final_build.log 2>&1
T2=$(date +%s)
S709=$(./build/tests/f709_filedescriptor_law_test 2>/dev/null | tail -1)
S714=$(./build/tests/f714_measurespec_law_test 2>/dev/null | tail -1)
S716=$(./build/tests/f716_view_tag_law_test 2>/dev/null | tail -1)
make --no-print-directory dev-so -j1 >> /tmp/w13_final_build.log 2>&1
make --no-print-directory dev-so-test -j1 >> /tmp/w13_final_build.log 2>&1
T3=$(date +%s)
DEV_PASS=$(grep -c '\[PASS\]' /tmp/w13_final_build.log)
A_PZ=/home/z/my-project/upload/handoff_apks/name.livitski.games.puzzle.android_2.apk
A_GUESS=/home/z/my-project/upload/handoff_apks/ru.zxalexis.ugaday_15.apk
mkdir -p /tmp/w13_final
for RUN in 1 2 3; do
  ./build_dev_so/miniandroid_dev run --max-seconds 150 --frames 30 --trace -o /tmp/w13_final/pz_r$RUN --execution-mode real-dalvik $A_PZ > /tmp/w13_final/pz_r$RUN.log 2>&1
  ./build_dev_so/miniandroid_dev run --max-seconds 120 --frames 30 -o /tmp/w13_final/guess_r$RUN --execution-mode real-dalvik $A_GUESS > /tmp/w13_final/guess_r$RUN.log 2>&1
done
echo "TIMING: incremental_static=$((T1-T0))s tests=$((T2-T1))s devso=$((T3-T2))s battery=$DEV_PASS | $S709 | $S714 | $S716"
for R in pz_r1 pz_r2 pz_r3 guess_r1 guess_r2 guess_r3; do
  S=$(sha256sum /tmp/w13_final/$R/screenshot.png 2>/dev/null | cut -c1-16)
  echo "$R sha=$S"
done
grep -ac "F718-REFLECT" /tmp/w13_final/pz_r1.log
echo FINAL_DONE
