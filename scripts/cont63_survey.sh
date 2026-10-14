#!/usr/bin/env bash
# cont63_survey.sh — CONT-63 W0 survey: current pixel truth for the 6 user apps
# + dooz180 at the CONT-62 merged binary (5112377f8eadb09a). One run each;
# x3 zero-drift regression happens at W8 after fixes.
set -uo pipefail
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/cont63
mkdir -p "$OUT"
echo "binary: $(sha256sum $BIN | cut -c1-16)  head: $(git -C $BASE rev-parse --short HEAD)"

run1() { # run1 <label> <apkpath> <budget-seconds>
  local label="$1" apk="$2" secs="$3"
  local o="$OUT/$label"; rm -rf "$o"; mkdir -p "$o"
  timeout $((secs + 120)) "$BIN" run "$apk" --width 1080 --height 1920 \
    --frames 5 --max-seconds "$secs" -o "$o" > "$o/run.log" 2>&1
  local rc=$?
  local sha
  sha=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
  echo "SURVEY $label rc=$rc sha=$sha"
}

case "${1:-all}" in
all)
  run1 simplecalc "$BASE/upload/cont54_refetch/com.simplemobiletools.calculator_8.apk" 15
  run1 opencalc  "$BASE/upload/opencalculator_53.apk" 15
  run1 tanana    "$BASE/upload/cont54_refetch/com.tananaev.calculator_11.apk" 15
  run1 bmi       "$BASE/upload/cont11_apks/bmi_402.apk" 15
  run1 alex      "$BASE/upload/cont11_apks/alexcalc_20.apk" 15
  run1 dooz15    "$BASE/upload/canonical_apks/io.github.yamin8000.dooz_23.apk" 15
  run1 dooz180   "$BASE/upload/canonical_apks/io.github.yamin8000.dooz_23.apk" 180
  ;;
single) run1 "$2" "$3" "$4" ;;
esac
