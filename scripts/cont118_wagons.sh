#!/usr/bin/env bash
# cont118_wagons.sh — one app per wagon, 23 wagons. Usage: cont118_wagons.sh <from> <to>
set -u
cd /home/z/my-project
B=./miniandroid/build/miniandroid
LOG=run/c118/wagons.log
mkdir -p run/c118

wagon() { # id name apk frames maxsec anchor(optional)
  local id="$1" name="$2" apk="$3" frames="$4" maxsec="$5" anchor="${6:-}"
  echo "== WAGON $id $name apk=$(basename $apk) frames=$frames max=${maxsec}s ==" | tee -a "$LOG"
  timeout $((maxsec*3+90)) "$B" run "$apk" --width 1080 --height 1920 --frames "$frames" \
    --max-seconds "$maxsec" -o "run/c118/$name" > /dev/null 2> "run/c118/$name.log"
  local rc=$?
  echo "rc=$rc" | tee -a "$LOG"
  local face="NO_SCREENSHOT"
  [ -f "run/c118/$name/screenshot.png" ] && face=$(sha256sum "run/c118/$name/screenshot.png" | cut -c1-16)
  echo "face=$face" | tee -a "$LOG"
  [ -n "$anchor" ] && { [ "$face" = "$anchor" ] && echo "anchor=$anchor MATCH" | tee -a "$LOG" || echo "anchor=$anchor DIFF" | tee -a "$LOG"; }
  local uncaught vrnodes f100 boundary
  uncaught=$(grep -c -iE 'Uncaught|SYNTH-EXC' "run/c118/$name.log" 2>/dev/null || echo 0)
  vrnodes=$(grep -oE 'view_root[^0-9]*[0-9]+' "run/c118/$name.log" 2>/dev/null | head -1)
  f100=$(grep -c 'F100-STATE' "run/c118/$name.log" 2>/dev/null || echo 0)
  boundary=$(grep -c -E 'APP-BOUNDARY|APPLICATION_BOUNDARY' "run/c118/$name.log" 2>/dev/null || echo 0)
  echo "uncaught_or_synthexc=$uncaught f100=$f100 boundary=$boundary vrnodes='$vrnodes'" | tee -a "$LOG"
  grep -E 'SYNTH-EXC|APP-BOUNDARY|first_missing_stage|load_apk' "run/c118/$name.log" 2>/dev/null | head -2 | sed 's/^/  KEY: /' | tee -a "$LOG"
}

case "${1}-${2}" in
  1-4)
    wagon W-01 telegram  upload/telegram_official.apk 5 60 20ac8cbbbb692e63
    wagon W-02 whatsapp  upload/whatsapp.apk 5 30
    wagon W-03 forkgram  upload/forkgram_709208.apk 5 60
    wagon W-04 sudoku    upload/sudoku_secuso_101.apk 5 30 be640e39e82901c9
    ;;
  5-8)
    wagon W-05 dooz      upload/canonical_apks/io.github.yamin8000.dooz_23.apk 5 30 d602648e8e401895
    wagon W-06 tictactoe upload/canonical_apks/com.emmanuelmess.tictactoe_3.apk 5 30
    wagon W-07 bouncy    upload/canonical_apks/com.dozingcatsoftware.bouncy_43.apk 5 30
    wagon W-08 flappycow upload/flappycow_rebuilt.apk 5 30
    ;;
  9-12)
    wagon W-09 gmdice    upload/canonical_apks/de.duenndns.gmdice_8.apk 5 30
    wagon W-10 memory    upload/canonical_apks/org.secuso.privacyfriendlymemory_100.apk 5 30
    wagon W-11 chess     upload/chess_jwtc_298.apk 5 30 a0319686d56ff5c0
    wagon W-12 klondike  upload/klondike_veldsoft_3.apk 5 30 ba50a4d28ea62fe7
    ;;
  13-16)
    wagon W-13 tripeaks  upload/canonical_apks/tripeaks_v1.2.1_vc4.apk 5 30
    wagon W-14 fishrings upload/canonical_apks/fishrings_v1.23_vc6.apk 5 30
    wagon W-15 tower3d   upload/canonical_apks/stack.tower3d_1.apk 5 30 11a38a5aeeff45a6
    wagon W-16 opencalc  upload/opencalculator_53.apk 5 30 d5f3c7b5e9936ae6
    ;;
  17-20)
    wagon W-17 unote     upload/canonical_apks/app.varlorg.unote_30.apk 5 30 90a67cc1ddda57b7
    wagon W-18 notes     upload/notes_secuso_105.apk 5 30
    wagon W-19 stopwatch upload/canonical_apks/com.github.muellerma.stopwatch_6.apk 5 30
    wagon W-20 microtimer upload/canonical_apks/dubrowgn.microtimer_8.apk 5 30 bbd350b6c14fbd52
    ;;
  21-23)
    wagon W-21 chessclock upload/chessclock_29.apk 5 30
    wagon W-22 opmt      upload/canonical_apks/opmt_v0.1.2_vc1.apk 5 30
    echo "== WAGON W-23 signal ==" | tee -a "$LOG"
    echo "BLOCKED_NEEDS_ARTIFACT: no Signal APK in corpus (upload/ + upload/canonical_apks/) — honest, not fabricated" | tee -a "$LOG"
    echo "== DONE ==" | tee -a "$LOG"
    ;;
esac
