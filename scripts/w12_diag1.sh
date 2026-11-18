#!/bin/bash
cd /home/z/my-project/miniandroid
make --no-print-directory dev-so -j1 > /tmp/w12_diag_build.log 2>&1 || { echo BUILD_FAIL; tail -5 /tmp/w12_diag_build.log; exit 1; }
A_NP=/home/z/my-project/upload/handoff_apks/com.farmerbb.notepad_122.apk
./build_dev_so/miniandroid_dev run --max-seconds 60 --frames 10 --trace \
  -o /tmp/w12_diag_notepad --execution-mode real-dalvik $A_NP > /tmp/w12_diag_notepad.log 2>&1
echo "notepad rc=$?"
echo "P-site (PIC R339):"; grep -a "F713P-GSS" /tmp/w12_diag_notepad.log | head -5
echo "B-site null (bridge):"; grep -a "F713-GSS-NULL" /tmp/w12_diag_notepad.log | head -4
echo "A-site null (monolith):"; grep -a "F713A-GSS-NULL" /tmp/w12_diag_notepad.log | head -4
echo "R339 answers:"; grep -a "R339-SVC" /tmp/w12_diag_notepad.log | head -4
echo DIAG1_DONE
