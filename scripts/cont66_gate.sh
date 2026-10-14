#!/usr/bin/env bash
# cont66_gate.sh — chunked anchor wall at the F-NEW-360 binary.
# Usage: cont66_gate.sh <row 1..11>   (one app, 3 repetitions)
# Every row prints MATCH/CHANGED/FAIL vs the CONT-62/64/65 recorded wall.
set -uo pipefail
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/cont66/regression
mkdir -p "$OUT"
ROW=$1
declare -A APK WANT
A=$BASE/upload
APK[csw]="$A/cont54_refetch/com.justdeax.composeStopwatch_1009011.apk";  WANT[csw]=d3c26b73ee21e571
APK[dooz]="$A/canonical_apks/io.github.yamin8000.dooz_23.apk";           WANT[dooz]=31ddd4d5b8e6d18e
APK[flappycow]="$A/flappycow_rebuilt.apk";                               WANT[flappycow]=13cf47464d9787f4
APK[g2048]="$A/s80_games/build_2048/g2048_v1.0_vc1.apk";                 WANT[g2048]=59ca1526611c4622
APK[gmdice]="$A/canonical_apks/de.duenndns.gmdice_8.apk";                WANT[gmdice]=3891679dff449331
APK[microtimer]="$A/canonical_apks/dubrowgn.microtimer_8.apk";           WANT[microtimer]=bbd350b6c14fbd52
APK[opencalc]="$A/opencalculator_53.apk";                                WANT[opencalc]=f25b754c4565c38b
APK[simplecalc]="$A/cont54_refetch/com.simplemobiletools.calculator_8.apk"; WANT[simplecalc]=2ac5d8d0cbf9552a
APK[tanana]="$A/cont54_refetch/com.tananaev.calculator_11.apk";          WANT[tanana]=afe0bd8dd4d09ca6
APK[tttdeluxe]="$A/s83_games/build_ttt/tictactoe_deluxe_v1.0_vc1.apk";   WANT[tttdeluxe]=af6094295ecb50e3
APK[unote]="$A/canonical_apks/app.varlorg.unote_30.apk";                 WANT[unote]=90a67cc1ddda57b7
name=$(echo $ROW | cut -d: -f1)
apk="${APK[$name]}"; want="${WANT[$name]}"
for i in 1 2 3; do
  o="$OUT/${name}_r$i"; rm -rf "$o"; mkdir -p "$o"
  timeout 135 "$BIN" run "$apk" --width 1080 --height 1920 --frames 5 --max-seconds 15 -o "$o" > "$o/run.log" 2>&1
  rc=$?
  sha=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
  verdict="DRIFT"; [ "$sha" = "$want" ] && verdict="MATCH"
  [ "$sha" != "$want" ] && [ $rc -eq 0 ] && verdict="CHANGED"
  [ $rc -ne 0 ] && [ -z "$sha" ] && verdict="FAIL"
  echo "GATE $name r$i rc=$rc sha=$sha want=$want $verdict"
done
