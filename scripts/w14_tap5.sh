#!/bin/bash
cd /home/z/my-project/miniandroid
T0=$(date +%s)
make --no-print-directory all -j1 > /tmp/w14_tap5_build.log 2>&1 || { echo STATIC_FAIL; grep -E "error" /tmp/w14_tap5_build.log | head -4; exit 1; }
make --no-print-directory dev-so -j1 >> /tmp/w14_tap5_build.log 2>&1 || { echo DEVSO_FAIL; exit 1; }
T1=$(date +%s)
echo "rebuild= $((T1-T0))s"
A_PZ=/home/z/my-project/upload/handoff_apks/name.livitski.games.puzzle.android_2.apk
./build_dev_so/miniandroid_dev run --max-seconds 200 --frames 50 --trace \
  --tap 197,112@25 \
  -o /tmp/w14/pz_tap5 --execution-mode real-dalvik $A_PZ > /tmp/w14/pz_tap5.log 2>&1
echo "rc=$?"
grep -a "F723-PUTEXTRA\|F722-GIAP" /tmp/w14/pz_tap5.log | head -6 | cut -c1-160
echo "== chain:"; grep -a "G08-RESULT\|G08-DBG.*popped\|IllegalStateException\|selectImage\|showImageBoard" /tmp/w14/pz_tap5.log | head -8 | cut -c1-140
echo TAP5_DONE
