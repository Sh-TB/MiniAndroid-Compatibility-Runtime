#!/usr/bin/env bash
# cont66_survey.sh — fresh faces of the 4 named compose lanes at HEAD (6bf640b9):
# opencalc display-empty, bmi row-clip, tanana layout, alex blue-bar. simplecalc = control.
set -uo pipefail
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/cont66/survey
mkdir -p "$OUT"
echo "binary: $(sha256sum $BIN | cut -c1-16)  head: $(git -C $BASE rev-parse --short HEAD)"

run1() { # run1 <label> <apk> <secs>
  local label="$1" apk="$2" secs="$3"
  local o="$OUT/$label"; rm -rf "$o"; mkdir -p "$o"
  timeout $((secs + 120)) "$BIN" run "$apk" --width 1080 --height 1920 \
    --frames 5 --max-seconds "$secs" -o "$o" > "$o/run.log" 2>&1
  local rc=$?
  echo "RUN $label rc=$rc sha=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)"
}

A=$BASE/upload
run1 simplecalc "$A/cont54_refetch/com.simplemobiletools.calculator_8.apk" 15
run1 opencalc   "$A/opencalculator_53.apk" 15
run1 tanana     "$A/cont54_refetch/com.tananaev.calculator_11.apk" 15
run1 bmi        "$A/cont11_apks/bmi_402.apk" 15
run1 alex       "$A/cont11_apks/alexcalc_20.apk" 15
echo "survey done"
