#!/usr/bin/env bash
# cont97_battery.sh — full regression battery for the CONT-98 wave
# (INFRA-BRIDGEINTR-1 bridge intrinsic entry fast path + BRIDGE-CENSUS tool)
# at binary e51d7a643e6817ba.
set -u
cd /home/z/my-project
mkdir -p run/cont98
LOG=run/cont98/battery.log
: > "$LOG"
echo "== binary ==" | tee -a "$LOG"
sha256sum miniandroid/build/miniandroid | cut -c1-16 | tee -a "$LOG"

echo "== wall gate 4 rows x3 ==" | tee -a "$LOG"
for row in dooz opencalc unote microtimer; do
  bash scripts/cont70_gate.sh "$row" >> "$LOG" 2>&1
done
rg "MATCH|CHANGED|FAIL" "$LOG" | tail -12

echo "== goldens ==" | tee -a "$LOG"
timeout 550 python3 scripts/user_golden_gate.py >> "$LOG" 2>&1
echo "goldens rc=$?" | tee -a "$LOG"

echo "== negatives + reinstall ==" | tee -a "$LOG"
timeout 550 python3 scripts/s41_gatea_negative.py >> "$LOG" 2>&1
echo "gatea rc=$?" | tee -a "$LOG"

echo "== MG-310 / MG-150 fences ==" | tee -a "$LOG"
timeout 300 python3 scripts/cont76_fence_mg310.py >> "$LOG" 2>&1
echo "mg310 rc=$?" | tee -a "$LOG"
timeout 300 python3 scripts/cont76_fence_mg150.py >> "$LOG" 2>&1
echo "mg150 rc=$?" | tee -a "$LOG"

echo "== selftests ==" | tee -a "$LOG"
timeout 300 python3 scripts/skill_selftest.py >> "$LOG" 2>&1
echo "selftest rc=$?" | tee -a "$LOG"

echo "== F-NEW-376 fault battery (incl. c72priv rows) ==" | tee -a "$LOG"
timeout 550 python3 scripts/cont73_fault_injection.py >> "$LOG" 2>&1
echo "f376 rc=$?" | tee -a "$LOG"

echo "== fixture anchors: sax1 / clock1 / clinit1 / swipe1 / c74esc / perf1 ==" | tee -a "$LOG"
timeout 120 ./miniandroid/build/miniandroid run run/cont95/sax1.apk --width 1080 --height 1920 --frames 3 --max-seconds 60 -o run/cont98/anchor_sax1 > /dev/null 2> run/cont98/anchor_sax1.log
rg -o "\[SAX1\].*" run/cont98/anchor_sax1.log | tail -1 | tee -a "$LOG"
timeout 120 ./miniandroid/build/miniandroid run run/cont86/clock1.apk --width 1080 --height 1920 --frames 3 --max-seconds 60 -o run/cont98/anchor_clock1 > /dev/null 2> run/cont98/anchor_clock1.log
rg -o "clock1.*" run/cont98/anchor_clock1.log | tail -1 | tee -a "$LOG"
timeout 120 ./miniandroid/build/miniandroid run run/cont87/clinit1.apk --width 1080 --height 1920 --frames 3 --max-seconds 60 -o run/cont98/anchor_clinit1 > /dev/null 2> run/cont98/anchor_clinit1.log
rg -o "\[CLINIT1?\].*|\[C87-.*" run/cont98/anchor_clinit1.log | tail -6 | tee -a "$LOG"
timeout 120 ./miniandroid/build/miniandroid run run/cont86/swipe1.apk --width 1080 --height 1920 --frames 3 --max-seconds 60 -o run/cont98/anchor_swipe1 > /dev/null 2> run/cont98/anchor_swipe1.log
rg -o "\[SWIPE1?\].*|\[C86-.*" run/cont98/anchor_swipe1.log | tail -3 | tee -a "$LOG"
timeout 120 ./miniandroid/build/miniandroid run run/cont74/c74esc.apk --width 1080 --height 1920 --frames 3 --max-seconds 60 -o run/cont98/anchor_c74esc > /dev/null 2> run/cont98/anchor_c74esc.log
rg -o "C74-.*(ESC|OK|LEAK).*" run/cont98/anchor_c74esc.log | tail -4 | tee -a "$LOG"
timeout 150 ./miniandroid/build/miniandroid run run/cont96/perf1.apk --width 1080 --height 1920 --frames 3 --max-seconds 120 -o run/cont98/anchor_perf1 > /dev/null 2> run/cont98/anchor_perf1.log
rg -o "\[PERF1\].*" run/cont98/anchor_perf1.log | tee -a "$LOG"

echo "BATTERY DONE" | tee -a "$LOG"
