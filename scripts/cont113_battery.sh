#!/usr/bin/env bash
# cont112_battery.sh — CONT-112 full verification battery
# Fix family: F-NEW-454/454b (framework-style routing + style-ref raw law) +
# F-NEW-454c/455 (TypedArray dimension reader deref law) + F-NEW-456
# (runtime-class virtual dispatch start) + F-NEW-457 (recs-scan ordering) +
# F-NEW-458 (android:min*/style attr id laws). Probes: c449 rows + chess
# toolbar A/B (app bracket) + full regression wall.
set -u
cd /home/z/my-project
mkdir -p run/c113
LOG=run/c113/battery.log
: > "$LOG"
echo "== binary ==" | tee -a "$LOG"
sha256sum miniandroid/build/miniandroid | cut -c1-16 | tee -a "$LOG"

echo "== c449 probe rows (law family) ==" | tee -a "$LOG"
timeout 90 ./miniandroid/build/miniandroid run run/c113/c449.apk --width 1080 --height 1920 --frames 3 --max-seconds 30 -o run/c113/c449_run > /dev/null 2> run/c113/c449.log
rg -o "C449-.*" run/c113/c449.log | tee -a "$LOG"

echo "== c448 probe rows (CONT-111 regression) ==" | tee -a "$LOG"
timeout 90 ./miniandroid/build/miniandroid run run/c111/c448.apk --width 1080 --height 1920 --frames 3 --max-seconds 30 -o run/c113/c448_run > /dev/null 2> run/c113/c448.log
rg -o "C448-.*" run/c113/c448.log | tee -a "$LOG"

echo "== chess toolbar (F-NEW-448 layer-2) ==" | tee -a "$LOG"
timeout 240 ./miniandroid/build/miniandroid run upload/chess_jwtc_298.apk --width 1080 --height 1920 --frames 5 --max-seconds 30 -o run/c113/chess_final > /dev/null 2> run/c113/chess_final.log
rg -o "node=\d+ class=Landroidx/appcompat/widget/Toolbar;.*" run/c113/chess_final.log | tail -2 | tee -a "$LOG"
sha256sum run/c113/chess_final/screenshot.png | cut -c1-16 | tee -a "$LOG"

echo "== wall gate 4 rows ==" | tee -a "$LOG"
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

echo "== prior probes re-validated at new binary ==" | tee -a "$LOG"
timeout 90 ./miniandroid/build/miniandroid run run/cont107/c106a.apk --width 1080 --height 1920 --frames 3 --max-seconds 30 -o run/c113/p_c106a > /dev/null 2> run/c113/p_c106a.log
rg -o "\[C106-[A-Z0-9]+\].*|\[F447-NPE\].*" run/c113/p_c106a.log | head -6 | tee -a "$LOG"
timeout 90 ./miniandroid/build/miniandroid run run/cont107/c106b2.apk --width 1080 --height 1920 --frames 3 --max-seconds 30 -o run/c113/p_c106b2 > /dev/null 2> run/c113/p_c106b2.log
rg -o "C106B2-.*|dim=.*" run/c113/p_c106b2.log | head -6 | tee -a "$LOG"
timeout 90 ./miniandroid/build/miniandroid run run/cont74/c74esc.apk --width 1080 --height 1920 --frames 3 --max-seconds 30 -o run/c113/p_c74esc > /dev/null 2> run/c113/p_c74esc.log
rg -o "C74-.*|LEAK.*|V1-ESC.*" run/c113/p_c74esc.log | head -8 | tee -a "$LOG"

echo "BATTERY DONE" | tee -a "$LOG"
