#!/usr/bin/env bash
# cont106_battery.sh — full regression battery for the CONT-106 wave
# (F-NEW-446: S123-CLINIT-MAT gated to failed-clinit classes) at the final binary.
set -u
cd /home/z/my-project
mkdir -p run/cont106
LOG=run/cont106/battery.log
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

echo "== c106a probe (POST) ==" | tee -a "$LOG"
timeout 90 ./miniandroid/build/miniandroid run run/cont106/c106a.apk --width 1080 --height 1920 --frames 3 --max-seconds 30 -o run/cont106/batt_c106a > /dev/null 2> run/cont106/batt_c106a.log
rg -o "\[C106-.*" run/cont106/batt_c106a.log | tee -a "$LOG"

echo "== c104i probe (4/4) ==" | tee -a "$LOG"
timeout 90 ./miniandroid/build/miniandroid run run/cont104/c104i.apk --width 1080 --height 1920 --frames 3 --max-seconds 30 -o run/cont106/batt_c104i > /dev/null 2> run/cont106/batt_c104i.log
rg -o "C104-.*" run/cont106/batt_c104i.log | tee -a "$LOG"

echo "== c74esc containment (5/5) ==" | tee -a "$LOG"
timeout 90 ./miniandroid/build/miniandroid run run/cont74/c74esc.apk --width 1080 --height 1920 --frames 3 --max-seconds 30 -o run/cont106/batt_c74esc > /dev/null 2> run/cont106/batt_c74esc.log
rg -o "C74-.*" run/cont106/batt_c74esc.log | tee -a "$LOG"

echo "BATTERY DONE" | tee -a "$LOG"
