#!/bin/bash
cd /home/z/my-project/miniandroid
make --no-print-directory test-core -j1 > /tmp/w14_gate.log 2>&1
make --no-print-directory build/tests/f709_filedescriptor_law_test build/tests/f714_measurespec_law_test build/tests/f716_view_tag_law_test >> /tmp/w14_gate.log 2>&1
T709=$(./build/tests/f709_filedescriptor_law_test 2>/dev/null | tail -1)
T714=$(./build/tests/f714_measurespec_law_test 2>/dev/null | tail -1)
T716=$(./build/tests/f716_view_tag_law_test 2>/dev/null | tail -1)
make --no-print-directory dev-so-test -j1 >> /tmp/w14_gate.log 2>&1
DEV_PASS=$(grep -c '\[PASS\]' /tmp/w14_gate.log)
A_PZ=/home/z/my-project/upload/handoff_apks/name.livitski.games.puzzle.android_2.apk
A_NP=/home/z/my-project/upload/handoff_apks/com.farmerbb.notepad_122.apk
A_GUESS=/home/z/my-project/upload/handoff_apks/ru.zxalexis.ugaday_15.apk
A_DICE=/home/z/my-project/upload/handoff_apks/tech.gaskell.diceroller_1_debug.apk
A_TTT=/home/z/my-project/upload/handoff_apks/com.itsfrz.tictactoe_5.apk
mkdir -p /tmp/w14/gate
for RUN in 1 2 3; do
  ./build_dev_so/miniandroid_dev run --max-seconds 200 --frames 50 --trace --tap 197,112@25 -o /tmp/w14/gate/pz_r$RUN --execution-mode real-dalvik $A_PZ > /tmp/w14/gate/pz_r$RUN.log 2>&1
  ./build_dev_so/miniandroid_dev run --max-seconds 120 --frames 30 -o /tmp/w14/gate/guess_r$RUN --execution-mode real-dalvik $A_GUESS > /tmp/w14/gate/guess_r$RUN.log 2>&1
  ./build_dev_so/miniandroid_dev run --max-seconds 90 --frames 30 --trace -o /tmp/w14/gate/np_r$RUN --execution-mode real-dalvik $A_NP > /tmp/w14/gate/np_r$RUN.log 2>&1
done
./build_dev_so/miniandroid_dev run --max-seconds 120 --frames 30 -o /tmp/w14/gate/dice --execution-mode real-dalvik $A_DICE > /tmp/w14/gate/dice.log 2>&1
./build_dev_so/miniandroid_dev run --max-seconds 120 --frames 30 -o /tmp/w14/gate/ttt --execution-mode real-dalvik $A_TTT > /tmp/w14/gate/ttt.log 2>&1
echo "GATE: battery=$DEV_PASS | $T709 | $T714 | $T716"
for R in pz_r1 pz_r2 pz_r3 guess_r1 guess_r2 guess_r3 np_r1 np_r2 np_r3 dice ttt; do
  S=$(sha256sum /tmp/w14/gate/$R/screenshot.png 2>/dev/null | cut -c1-16)
  echo "$R sha=$S"
done
echo "== chain x3:"
for R in pz_r1 pz_r2 pz_r3; do
  C=$(grep -ac "G08-RESULT\|onActivityResult.*dispatched..true" /tmp/w14/gate/$R.log)
  echo "$R result_chain_hits=$C"
done
grep -ac "ITEM_CLICK" /tmp/w14/gate/pz_r1.log
echo GATE_DONE
