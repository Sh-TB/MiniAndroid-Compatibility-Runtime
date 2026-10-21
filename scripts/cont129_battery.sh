#!/usr/bin/env bash
# cont129_battery.sh — fresh full-corpus impact battery at current binary. Usage: cont129_battery.sh <from> <to>
# Idempotent: apps with existing logs are skipped, so re-run continues where it stopped.
set -u
cd /home/z/my-project
B=./miniandroid/build/miniandroid
LOG=run/c129/battery.log
mkdir -p run/c129

wagon() { # id name apkpath anchor(optional) maxsec(optional, default 25; telegram wall=60 per CONT-129 adjudication)
  local id="$1" name="$2" apk="$3" anchor="${4:-}" maxsec="${5:-25}"
  if [ -f "run/c129/$name.log" ] && grep -q 'rc=' "run/c129/$name.log" 2>/dev/null; then
    echo "== WAGON $id $name SKIP (done) ==" | tee -a "$LOG"; return 0
  fi
  echo "== WAGON $id $name apk=$(basename $apk) ==" | tee -a "$LOG"
  timeout 170 "$B" run "$apk" --width 1080 --height 1920 --frames 5 \
    --max-seconds "$maxsec" -o "run/c129/$name" > /dev/null 2> "run/c129/$name.log"
  local rc=$?
  echo "rc=$rc" | tee -a "$LOG"
  local face="NO_SCREENSHOT"
  [ -f "run/c129/$name/screenshot.png" ] && face=$(sha256sum "run/c129/$name/screenshot.png" | cut -c1-16)
  echo "face=$face" | tee -a "$LOG"
  if [ -n "$anchor" ]; then
    [ "${face:0:${#anchor}}" = "$anchor" ] && echo "anchor=$anchor MATCH" | tee -a "$LOG" || echo "anchor=$anchor DIFF" | tee -a "$LOG"
  fi
  local uncaught boundary f100 vrnodes
  uncaught=$(grep -c -iE 'Uncaught|SYNTH-EXC' "run/c129/$name.log" 2>/dev/null || true)
  boundary=$(grep -c -E 'APP-BOUNDARY|APPLICATION_BOUNDARY' "run/c129/$name.log" 2>/dev/null || true)
  f100=$(grep -c 'F100-STATE' "run/c129/$name.log" 2>/dev/null || true)
  vrnodes=$(grep -oE 'view_root[^0-9]*[0-9]+' "run/c129/$name.log" 2>/dev/null | head -1)
  echo "uncaught_or_synthexc=$uncaught boundary=$boundary f100=$f100 vrnodes='$vrnodes'" | tee -a "$LOG"
  grep -E 'SYNTH-EXC|APP-BOUNDARY|first_missing_stage' "run/c129/$name.log" 2>/dev/null | head -2 | sed 's/^/  KEY: /' | tee -a "$LOG"
}

CA=upload/canonical_apks
case "${1}-${2}" in
  1-4)   wagon 1 dooz       $CA/io.github.yamin8000.dooz_23.apk d602648e
         wagon 2 klondike   upload/klondike_veldsoft_3.apk 31ddd4d5
         wagon 3 unote      $CA/app.varlorg.unote_30.apk 90a67cc1
         wagon 4 chess      upload/chess_jwtc_298.apk a0319686 ;;
  5-8)   wagon 5 telegram   upload/telegram_official.apk 20ac8cbbbb 60
         wagon 6 tower3d    $CA/stack.tower3d_1.apk 11a38a5a
         wagon 7 opencalc   upload/opencalculator_53.apk d5f3c7b5
         wagon 8 microtimer $CA/dubrowgn.microtimer_8.apk bbd350b6 ;;
  9-12)  wagon 9 sudoku     upload/sudoku_secuso_101.apk be640e39
         wagon 10 tictactoe $CA/com.emmanuelmess.tictactoe_3.apk
         wagon 11 stopwatch $CA/com.github.muellerma.stopwatch_6.apk
         wagon 12 gmdice    $CA/de.duenndns.gmdice_8.apk ;;
  13-16) wagon 13 bouncy    $CA/com.dozingcatsoftware.bouncy_43.apk
         wagon 14 tripeaks  $CA/tripeaks_v1.2.1_vc4.apk
         wagon 15 fishrings $CA/fishrings_v1.23_vc6.apk
         wagon 16 memory    $CA/org.secuso.privacyfriendlymemory_100.apk ;;
  17-22) wagon 17 opmt      $CA/opmt_v0.1.2_vc1.apk
         wagon 18 chessclock upload/chessclock_29.apk
         wagon 19 flappycow upload/flappycow_rebuilt.apk
         wagon 20 forkgram  upload/forkgram_709208.apk
         wagon 21 notes     upload/notes_secuso_105.apk
         wagon 22 whatsapp  upload/whatsapp.apk ;;
  *) echo "usage: $0 <from> <to>" ;;
esac
echo "BATCH ${1}-${2} DONE" | tee -a "$LOG"
