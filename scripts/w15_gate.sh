#!/bin/bash
cd /home/z/my-project/miniandroid
T0=$(date +%s)
make --no-print-directory all -j1 > /tmp/w15_gate_build.log 2>&1 || { echo STATIC_FAIL; grep -E "error" /tmp/w15_gate_build.log | head -6; exit 1; }
T1=$(date +%s)
make --no-print-directory dev-so -j1 >> /tmp/w15_gate_build.log 2>&1 || { echo DEVSO_FAIL; grep -E "error" /tmp/w15_gate_build.log | head -4; exit 1; }
T2=$(date +%s)
echo "TIMING: static_all=$((T1-T0))s devso=$((T2-T1))s"
make --no-print-directory test-core -j1 >> /tmp/w15_gate_build.log 2>&1
./build/tests/w15_dalvik_lit_from16_law_test 2>/dev/null | tail -1
./build/tests/gp582_engine_probe_test 2>/dev/null | tail -1
./build/tests/s130_laws_test 2>/dev/null | tail -1
make --no-print-directory build/tests/f709_filedescriptor_law_test build/tests/f714_measurespec_law_test build/tests/f716_view_tag_law_test -j1 >> /tmp/w15_gate_build.log 2>&1
for T in f709_filedescriptor f714_measurespec f716_view_tag; do
  ./build/tests/${T}_law_test 2>/dev/null | tail -1
done
mkdir -p /tmp/w15/gate
A_PZ=/home/z/my-project/upload/handoff_apks/name.livitski.games.puzzle.android_2.apk
A_NP=/home/z/my-project/upload/handoff_apks/com.farmerbb.notepad_122.apk
A_GUESS=/home/z/my-project/upload/handoff_apks/ru.zxalexis.ugaday_15.apk
A_DICE=/home/z/my-project/upload/handoff_apks/tech.gaskell.diceroller_1_debug.apk
A_TTT=/home/z/my-project/upload/handoff_apks/com.itsfrz.tictactoe_5.apk
for R in 1 2 3; do
  ./build_dev_so/miniandroid_dev run --max-seconds 200 --frames 50 --trace --tap 197,112@25 -o /tmp/w15/gate/pz_r$R --execution-mode real-dalvik $A_PZ > /tmp/w15/gate/pz_r$R.log 2>&1
  ./build_dev_so/miniandroid_dev run --max-seconds 120 --frames 30 -o /tmp/w15/gate/guess_r$R --execution-mode real-dalvik $A_GUESS > /tmp/w15/gate/guess_r$R.log 2>&1
  ./build_dev_so/miniandroid_dev run --max-seconds 90 --frames 30 --trace -o /tmp/w15/gate/np_r$R --execution-mode real-dalvik $A_NP > /tmp/w15/gate/np_r$R.log 2>&1
done
./build_dev_so/miniandroid_dev run --max-seconds 120 --frames 30 -o /tmp/w15/gate/dice --execution-mode real-dalvik $A_DICE > /tmp/w15/gate/dice.log 2>&1
./build_dev_so/miniandroid_dev run --max-seconds 120 --frames 30 -o /tmp/w15/gate/ttt --execution-mode real-dalvik $A_TTT > /tmp/w15/gate/ttt.log 2>&1
for R in pz_r1 pz_r2 pz_r3 guess_r1 guess_r2 guess_r3 np_r1 np_r2 np_r3 dice ttt; do
  S=$(sha256sum /tmp/w15/gate/$R/screenshot.png 2>/dev/null | cut -c1-16)
  echo "$R sha=$S"
done
for R in pz_r1 pz_r2 pz_r3; do
  C=$(grep -ac "G08-RESULT" /tmp/w15/gate/$R.log)
  echo "$R result_chain=$C"
done
echo GATE_DONE
