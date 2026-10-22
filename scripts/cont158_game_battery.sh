#!/bin/bash
# cont158_game_battery.sh — CONT-158: 20-row game battery (18 games + 2 labeled reference tools)
# on binary 22578fcb03e0cd15 (CONT-157 deterministic rebuild).
# Instruction: «۱۰ از بازی و ۱۰ تا از گیم‌ها رو بررسی کن — ببین تغییرات اثری داشته»
# Usage: cont158_game_battery.sh <from> <to>
set -u
cd /home/z/my-project
B=./miniandroid/build/miniandroid
CA=upload/canonical_apks
S80=upload/s80_games
mkdir -p run/c158/battery
declare -A APKS=(
  [dooz]="$CA/io.github.yamin8000.dooz_23.apk"
  [dooz_top]="$CA/dooz_23_toplevel.apk"
  [bouncy]="$CA/com.dozingcatsoftware.bouncy_43.apk"
  [bouncy_top]="$CA/bouncy.apk"
  [tictactoe]="$CA/com.emmanuelmess.tictactoe_3.apk"
  [gmdice]="$CA/de.duenndns.gmdice_8.apk"
  [fishrings]="$CA/fishrings_v1.23_vc6.apk"
  [memory]="$CA/org.secuso.privacyfriendlymemory_100.apk"
  [tower3d]="$CA/stack.tower3d_1.apk"
  [tripeaks]="$CA/tripeaks_v1.2.1_vc4.apk"
  [chess]=upload/chess_jwtc_298.apk
  [chessclock]=upload/chessclock_29.apk
  [flappycow]=upload/flappycow_rebuilt.apk
  [klondike]=upload/klondike_veldsoft_3.apk
  [sudoku]=upload/sudoku_secuso_101.apk
  [g2048]="$S80/build_2048/g2048_v1.0_vc1.apk"
  [snake]="$S80/build_sd/snake_deluxe_v1.0_vc1.apk"
  [tetris]="$S80/build_tetris/tetris_v1.0_vc1.apk"
  # reference rows (tools, honestly labeled — white-face trio + calculator family)
  [stopwatch]="$CA/com.github.muellerma.stopwatch_6.apk"
  [opencalc]=upload/opencalculator_53.apk
)
ORDER="dooz dooz_top bouncy bouncy_top tictactoe gmdice fishrings memory tower3d tripeaks chess chessclock flappycow klondike sudoku g2048 snake tetris stopwatch opencalc"
n=0
for app in $ORDER; do
  n=$((n+1))
  [ "$n" -ge "$1" ] && [ "$n" -le "$2" ] || continue
  if [ -f "run/c158/battery/$app.log" ] && grep -q "rc=" "run/c158/battery/$app.log" 2>/dev/null; then
    echo "SKIP $app" >> run/c158/battery/battery.log; continue
  fi
  timeout 120 "$B" run "${APKS[$app]}" --width 1080 --height 1920 --frames 5 \
    --max-seconds 25 -o "run/c158/battery/$app" > /dev/null 2> "run/c158/battery/$app.log"
  echo "rc=$? $app" >> run/c158/battery/battery.log
done
echo "GAME BATTERY CHUNK $1-$2 DONE" >> run/c158/battery/battery.log
