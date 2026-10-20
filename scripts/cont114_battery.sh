#!/usr/bin/env bash
# cont114_battery.sh — CONT-114 full verification battery
# Fixes: F-NEW-462 renderer-receiver law (GL frame pump), F-NEW-463
# java.nio view-buffer family + GLES20 state-query-into-buffer, F-NEW-464
# initializer-default ()V ctor execution. Probes: f462 rows + full wall.
set -u
cd /home/z/my-project
mkdir -p run/c114
LOG=run/c114/battery.log
: > "$LOG"
echo "== binary ==" | tee -a "$LOG"
sha256sum miniandroid/build/miniandroid | cut -c1-16 | tee -a "$LOG"

echo "== f462 probe rows (F-NEW-462/463 lever) ==" | tee -a "$LOG"
timeout 90 ./miniandroid/build/miniandroid run run/c114/f462.apk --width 1080 --height 1920 --frames 3 --max-seconds 30 -o run/c114/f462_bat > /dev/null 2> run/c114/f462_bat.log
rg -o "C462-.*" run/c114/f462_bat.log | tee -a "$LOG"

echo "== c448 probe rows (CONT-111 regression) ==" | tee -a "$LOG"
timeout 90 ./miniandroid/build/miniandroid run run/c111/c448.apk --width 1080 --height 1920 --frames 3 --max-seconds 30 -o run/c114/c448_run > /dev/null 2> run/c114/c448.log
rg -o "C448-.*" run/c114/c448.log | tee -a "$LOG"

echo "== c449 probe rows (CONT-112 regression) ==" | tee -a "$LOG"
timeout 90 ./miniandroid/build/miniandroid run run/c112/c449.apk --width 1080 --height 1920 --frames 3 --max-seconds 30 -o run/c114/c449_run > /dev/null 2> run/c114/c449.log
rg -o "C449-.*|FLOOR-.*|DEREF-.*" run/c114/c449.log | head -8 | tee -a "$LOG"

echo "== wall gate 4 rows x3 ==" | tee -a "$LOG"
for row in dooz opencalc unote microtimer; do
  bash scripts/cont70_gate.sh "$row" >> "$LOG" 2>&1
done
rg "MATCH|CHANGED|FAIL" "$LOG" | tail -12 | tee -a "$LOG"

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

echo "== prior probe re-validated (c74esc) ==" | tee -a "$LOG"
timeout 90 ./miniandroid/build/miniandroid run run/cont74/c74esc.apk --width 1080 --height 1920 --frames 3 --max-seconds 30 -o run/c114/p_c74esc > /dev/null 2> run/c114/p_c74esc.log
rg -o "C74-.*|LEAK.*|V1-ESC.*" run/c114/p_c74esc.log | head -8 | tee -a "$LOG"

echo "BATTERY DONE" | tee -a "$LOG"
