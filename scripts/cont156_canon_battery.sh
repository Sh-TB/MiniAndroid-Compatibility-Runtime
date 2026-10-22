#!/bin/bash
# cont156_canon_battery.sh — the 22 canonical APKs on the CONT-156 binary.
# Usage: cont156_canon_battery.sh <from> <to> (1-based, same order as cont129).
set -u
cd /home/z/my-project
B=./miniandroid/build/miniandroid
CA=upload/canonical_apks
mkdir -p run/c156/canon
declare -A APKS=(
  [dooz]="$CA/io.github.yamin8000.dooz_23.apk"
  [klondike]=upload/klondike_veldsoft_3.apk
  [unote]="$CA/app.varlorg.unote_30.apk"
  [chess]=upload/chess_jwtc_298.apk
  [telegram]=upload/telegram_official.apk
  [tower3d]="$CA/stack.tower3d_1.apk"
  [opencalc]=upload/opencalculator_53.apk
  [microtimer]="$CA/dubrowgn.microtimer_8.apk"
  [sudoku]=upload/sudoku_secuso_101.apk
  [tictactoe]="$CA/com.emmanuelmess.tictactoe_3.apk"
  [stopwatch]="$CA/com.github.muellerma.stopwatch_6.apk"
  [gmdice]="$CA/de.duenndns.gmdice_8.apk"
  [bouncy]="$CA/com.dozingcatsoftware.bouncy_43.apk"
  [tripeaks]="$CA/tripeaks_v1.2.1_vc4.apk"
  [fishrings]="$CA/fishrings_v1.23_vc6.apk"
  [memory]="$CA/org.secuso.privacyfriendlymemory_100.apk"
  [opmt]="$CA/opmt_v0.1.2_vc1.apk"
  [chessclock]=upload/chessclock_29.apk
  [flappycow]=upload/flappycow_rebuilt.apk
  [forkgram]=upload/forkgram_709208.apk
  [notes]=upload/notes_secuso_105.apk
  [whatsapp]=upload/whatsapp.apk
)
ORDER="dooz klondike unote chess telegram tower3d opencalc microtimer sudoku tictactoe stopwatch gmdice bouncy tripeaks fishrings memory opmt chessclock flappycow forkgram notes whatsapp"
n=0
for app in $ORDER; do
  n=$((n+1))
  [ "$n" -ge "$1" ] && [ "$n" -le "$2" ] || continue
  ms=25; [ "$app" = telegram ] && ms=60
  if [ -f "run/c156/canon/$app.log" ] && grep -q "rc=" "run/c156/canon/$app.log" 2>/dev/null; then
    echo "SKIP $app" >> run/c156/canon/battery.log; continue
  fi
  timeout 120 "$B" run "${APKS[$app]}" --width 1080 --height 1920 --frames 5 \
    --max-seconds "$ms" -o "run/c156/canon/$app" > /dev/null 2> "run/c156/canon/$app.log"
  echo "rc=$? $app" >> run/c156/canon/battery.log
done
echo "CANON CHUNK $1-$2 DONE" >> run/c156/canon/battery.log
