#!/usr/bin/env bash
# cont111_battery.sh — CONT-111 full verification battery
# Fix: F-NEW-448 suggested-minimum family (View.setMinimumWidth/Height +
# getSuggestedMinimumWidth/Height + XML/style seeding). Probes: c448 rows +
# chess toolbar A/B + stack.tower3d F-NEW-367 refresh + full regression wall.
set -u
cd /home/z/my-project
mkdir -p run/c111
LOG=run/c111/battery.log
: > "$LOG"
echo "== binary ==" | tee -a "$LOG"
sha256sum miniandroid/build/miniandroid | cut -c1-16 | tee -a "$LOG"

echo "== c448 probe rows ==" | tee -a "$LOG"
timeout 90 ./miniandroid/build/miniandroid run run/c111/c448.apk --width 1080 --height 1920 --frames 3 --max-seconds 30 -o run/c111/c448_run > /dev/null 2> run/c111/c448.log
rg -o "C448-.*" run/c111/c448.log | tee -a "$LOG"

echo "== chess toolbar A/B (F-NEW-448) ==" | tee -a "$LOG"
timeout 120 ./miniandroid/build/miniandroid run upload/chess_jwtc_298.apk --width 1080 --height 1920 --frames 5 --max-seconds 30 -o run/c111/chess_post > /dev/null 2> run/c111/chess_post.log
rg -o "\[EXP092-RENDER\] node=\d+ class=[^ ]*Toolbar[^ ]*.*" run/c111/chess_post.log | tail -4 | tee -a "$LOG"
rg -c "EXP092-RENDER" run/c111/chess_post.log | tee -a "$LOG"
rg -o "FRAME-SEQ.*" run/c111/chess_post.log | tail -3 | tee -a "$LOG"

echo "== stack.tower3d (F-NEW-367 refresh) ==" | tee -a "$LOG"
ls upload/ | grep -i "tower\|stack" | head -3 | tee -a "$LOG"

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

echo "== prior probes re-validated at new binary ==" | tee -a "$LOG"
timeout 90 ./miniandroid/build/miniandroid run run/cont107/c106a.apk --width 1080 --height 1920 --frames 3 --max-seconds 30 -o run/c111/p_c106a > /dev/null 2> run/c111/p_c106a.log
rg -o "\[C106-[A-Z0-9]+\].*|\[F447-NPE\].*" run/c111/p_c106a.log | head -6 | tee -a "$LOG"
timeout 90 ./miniandroid/build/miniandroid run run/cont107/c106b2.apk --width 1080 --height 1920 --frames 3 --max-seconds 30 -o run/c111/p_c106b2 > /dev/null 2> run/c111/p_c106b2.log
rg -o "C106B2-.*|dim=.*" run/c111/p_c106b2.log | head -6 | tee -a "$LOG"
timeout 90 ./miniandroid/build/miniandroid run run/cont74/c74esc.apk --width 1080 --height 1920 --frames 3 --max-seconds 30 -o run/c111/p_c74esc > /dev/null 2> run/c111/p_c74esc.log
rg -o "C74-.*|LEAK.*|V1-ESC.*" run/c111/p_c74esc.log | head -8 | tee -a "$LOG"

echo "BATTERY DONE" | tee -a "$LOG"
