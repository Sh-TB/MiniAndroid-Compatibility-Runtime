#!/bin/bash
cd /home/z/my-project/miniandroid
A_PZ=/home/z/my-project/upload/handoff_apks/name.livitski.games.puzzle.android_2.apk
./build_dev_so/miniandroid_dev run --max-seconds 200 --frames 50 --trace \
  --tap 197,112@25 \
  -o /tmp/w14/pz_tap --execution-mode real-dalvik $A_PZ > /tmp/w14/pz_tap.log 2>&1
echo "rc=$?"
echo "== tap/event:"; grep -a "TAP\|ITEM_CLICK\|onItemClick" /tmp/w14/pz_tap.log | head -6 | cut -c1-140
echo "== result chain:"; grep -a "G08-RESULT\|G07-FINISH\|onActivityResult\|G08-RESTORE" /tmp/w14/pz_tap.log | head -10 | cut -c1-140
echo "== app reaction:"; grep -a "selectImage\|showImageBoard\|BoardView\|resizeContent\|F716\|setTag" /tmp/w14/pz_tap.log | head -8 | cut -c1-140
echo TAP_DONE
