#!/usr/bin/env bash
# cont70_wall_sweep.sh — one pass over the 12 wall rows at the wave binary.
# Prints MATCH/CHANGED per row vs the recorded WANT faces.
set -uo pipefail
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/cont70/wall_sweep
mkdir -p "$OUT"
declare -A APK WANT SECS
A=$BASE/upload
APK[csw]="$A/cont54_refetch/com.justdeax.composeStopwatch_1009011.apk";  WANT[csw]=d3c26b73ee21e571;  SECS[csw]=15
APK[dooz]="$A/canonical_apks/io.github.yamin8000.dooz_23.apk";           WANT[dooz]=31ddd4d5b8e6d18e; SECS[dooz]=15
APK[flappycow]="$A/flappycow_rebuilt.apk";                               WANT[flappycow]=13cf47464d9787f4; SECS[flappycow]=15
APK[g2048]="$A/s80_games/build_2048/g2048_v1.0_vc1.apk";                 WANT[g2048]=f43face08299ffc6; SECS[g2048]=15
APK[gmdice]="$A/canonical_apks/de.duenndns.gmdice_8.apk";                WANT[gmdice]=3891679dff449331; SECS[gmdice]=15
APK[microtimer]="$A/canonical_apks/dubrowgn.microtimer_8.apk";           WANT[microtimer]=bbd350b6c14fbd52; SECS[microtimer]=15
APK[opencalc]="$A/opencalculator_53.apk";                                WANT[opencalc]=f25b754c4565c38b; SECS[opencalc]=15
APK[simplecalc]="$A/cont54_refetch/com.simplemobiletools.calculator_8.apk"; WANT[simplecalc]=2ac5d8d0cbf9552a; SECS[simplecalc]=15
APK[tanana]="$A/cont54_refetch/com.tananaev.calculator_11.apk";          WANT[tanana]=afe0bd8dd4d09ca6; SECS[tanana]=15
APK[tttdeluxe]="$A/s83_games/build_ttt/tictactoe_deluxe_v1.0_vc1.apk";   WANT[tttdeluxe]=db1d633d77b5819a; SECS[tttdeluxe]=15
APK[unote]="$A/canonical_apks/app.varlorg.unote_30.apk";                 WANT[unote]=90a67cc1ddda57b7; SECS[unote]=15
APK[dooz180]="$A/canonical_apks/io.github.yamin8000.dooz_23.apk";        WANT[dooz180]=c94da5a928ea213b; SECS[dooz180]=180
for name in csw dooz flappycow g2048 gmdice microtimer opencalc simplecalc tanana tttdeluxe unote dooz180; do
  o="$OUT/${name}_r1"; rm -rf "$o"; mkdir -p "$o"
  timeout 200 "$BIN" run "${APK[$name]}" --width 1080 --height 1920 --frames 5 --max-seconds "${SECS[$name]}" -o "$o" > "$o/run.log" 2>&1
  rc=$?
  got=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
  want="${WANT[$name]}"
  verdict=FAIL
  [ "$got" = "$want" ] && verdict=MATCH
  [ -n "$got" ] && [ "$got" != "$want" ] && verdict=CHANGED
  echo "$name rc=$rc got=$got want=$want $verdict"
done
