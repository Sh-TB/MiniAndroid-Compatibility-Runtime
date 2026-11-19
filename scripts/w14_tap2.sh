#!/bin/bash
cd /home/z/my-project/miniandroid
T0=$(date +%s)
make --no-print-directory dev-so -j1 > /tmp/w14_tap2_build.log 2>&1 || { echo BUILD_FAIL; grep -E "error" /tmp/w14_tap2_build.log | head -5; exit 1; }
T1=$(date +%s)
echo "incremental_devso= $((T1-T0))s"
A_PZ=/home/z/my-project/upload/handoff_apks/name.livitski.games.puzzle.android_2.apk
./build_dev_so/miniandroid_dev run --max-seconds 200 --frames 50 --trace \
  --tap 197,112@25 \
  -o /tmp/w14/pz_tap2 --execution-mode real-dalvik $A_PZ > /tmp/w14/pz_tap2.log 2>&1
echo "rc=$?"
echo "== F721:"; grep -a "F721-ADDALL" /tmp/w14/pz_tap2.log | head -4
echo "== item click + NPE:"; grep -a "ITEM_CLICK\|f141-null-recv" /tmp/w14/pz_tap2.log | head -4 | cut -c1-160
echo "== result chain:"; grep -a "G08-RESULT\|G07-FINISH\|onActivityResult\|G08-RESTORE" /tmp/w14/pz_tap2.log | head -10 | cut -c1-140
echo "== app reaction:"; grep -a "selectImage\|showImageBoard\|resizeContent\|F716\|GameBoard" /tmp/w14/pz_tap2.log | head -6 | cut -c1-140
echo TAP2_DONE
