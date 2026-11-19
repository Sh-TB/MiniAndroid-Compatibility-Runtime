#!/bin/bash
# P0 gate — 5/6 canonical APK screenshot-hash battery (W14/W16/W17 procedure:
# pz x3, guess x3, np x3, dice x1, ttt x1; sha256 of screenshot.png, 16 hex).
cd /home/z/my-project/miniandroid
A_PZ=/home/z/my-project/upload/handoff_apks/name.livitski.games.puzzle.android_2.apk
A_NP=/home/z/my-project/upload/handoff_apks/com.farmerbb.notepad_122.apk
A_GUESS=/home/z/my-project/upload/handoff_apks/ru.zxalexis.ugaday_15.apk
A_DICE=/home/z/my-project/upload/handoff_apks/tech.gaskell.diceroller_1_debug.apk
A_TTT=/home/z/my-project/upload/handoff_apks/com.itsfrz.tictactoe_5.apk
OUT=${1:-/tmp/p0_gate}
mkdir -p $OUT
for RUN in 1 2 3; do
  ./build_dev_so/miniandroid_dev run --max-seconds 200 --frames 50 --trace \
    --tap 197,112@25 -o $OUT/pz_r$RUN --execution-mode real-dalvik $A_PZ \
    > $OUT/pz_r$RUN.log 2>&1
  ./build_dev_so/miniandroid_dev run --max-seconds 120 --frames 30 -o $OUT/guess_r$RUN \
    --execution-mode real-dalvik $A_GUESS > $OUT/guess_r$RUN.log 2>&1
  ./build_dev_so/miniandroid_dev run --max-seconds 90 --frames 30 --trace \
    -o $OUT/np_r$RUN --execution-mode real-dalvik $A_NP > $OUT/np_r$RUN.log 2>&1
done
./build_dev_so/miniandroid_dev run --max-seconds 120 --frames 30 -o $OUT/dice \
  --execution-mode real-dalvik $A_DICE > $OUT/dice.log 2>&1
./build_dev_so/miniandroid_dev run --max-seconds 120 --frames 30 -o $OUT/ttt \
  --execution-mode real-dalvik $A_TTT > $OUT/ttt.log 2>&1
for R in pz_r1 pz_r2 pz_r3 guess_r1 guess_r2 guess_r3 np_r1 np_r2 np_r3 dice ttt; do
  S=$(sha256sum $OUT/$R/screenshot.png 2>/dev/null | cut -c1-16)
  echo "$R sha=$S"
done
echo P0_GATE_DONE
