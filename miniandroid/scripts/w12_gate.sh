#!/bin/bash
cd /home/z/my-project/miniandroid
make --no-print-directory test-core -j1 > /tmp/w12_gate.log 2>&1
make --no-print-directory build/tests/f709_filedescriptor_law_test build/tests/f714_measurespec_law_test build/tests/f716_view_tag_law_test >> /tmp/w12_gate.log 2>&1
T709=$(./build/tests/f709_filedescriptor_law_test 2>/dev/null | tail -1)
T714=$(./build/tests/f714_measurespec_law_test 2>/dev/null | tail -1)
T716=$(./build/tests/f716_view_tag_law_test 2>/dev/null | tail -1)
make --no-print-directory dev-so -j1 >> /tmp/w12_gate.log 2>&1
make --no-print-directory dev-so-test -j1 >> /tmp/w12_gate.log 2>&1
DEV_PASS=$(grep -c '\[PASS\]' /tmp/w12_gate.log)
make --no-print-directory DALVIK_SPLIT=0 test-core -j1 > /tmp/w12_gate_mono.log 2>&1
MONO_PASS=$(grep -c '\[PASS\]' /tmp/w12_gate_mono.log)
A_GUESS=/home/z/my-project/upload/handoff_apks/ru.zxalexis.ugaday_15.apk
A_DICE=/home/z/my-project/upload/handoff_apks/tech.gaskell.diceroller_1_debug.apk
A_TTT=/home/z/my-project/upload/handoff_apks/com.itsfrz.tictactoe_5.apk
A_PZ=/home/z/my-project/upload/handoff_apks/name.livitski.games.puzzle.android_2.apk
A_NP=/home/z/my-project/upload/handoff_apks/com.farmerbb.notepad_122.apk
mkdir -p /tmp/w12_gate_runs
for RUN in 1 2 3; do
  ./build_dev_so/miniandroid_dev run --max-seconds 120 --frames 30 -o /tmp/w12_gate_runs/guess_r$RUN --execution-mode real-dalvik $A_GUESS > /tmp/w12_gate_runs/guess_r$RUN.log 2>&1
  ./build_dev_so/miniandroid_dev run --max-seconds 150 --frames 30 --trace -o /tmp/w12_gate_runs/pz_r$RUN --execution-mode real-dalvik $A_PZ > /tmp/w12_gate_runs/pz_r$RUN.log 2>&1
  ./build_dev_so/miniandroid_dev run --max-seconds 90 --frames 30 --trace -o /tmp/w12_gate_runs/np_r$RUN --execution-mode real-dalvik $A_NP > /tmp/w12_gate_runs/np_r$RUN.log 2>&1
done
./build_dev_so/miniandroid_dev run --max-seconds 120 --frames 30 -o /tmp/w12_gate_runs/dice --execution-mode real-dalvik $A_DICE > /tmp/w12_gate_runs/dice.log 2>&1
./build_dev_so/miniandroid_dev run --max-seconds 120 --frames 30 -o /tmp/w12_gate_runs/ttt --execution-mode real-dalvik $A_TTT > /tmp/w12_gate_runs/ttt.log 2>&1
echo "GATE: static/dev battery pass=$DEV_PASS | mono pass=$MONO_PASS | $T709 | $T714 | $T716"
for R in guess_r1 guess_r2 guess_r3 dice ttt pz_r1 pz_r2 pz_r3 np_r1 np_r2 np_r3; do
  S=$(sha256sum /tmp/w12_gate_runs/$R/screenshot.png 2>/dev/null | cut -c1-24)
  RC=$(grep -a "Status" /tmp/w12_gate_runs/$R.log 2>/dev/null | head -1 | cut -c1-60)
  echo "$R sha=$S"
done
echo GATE_DONE
