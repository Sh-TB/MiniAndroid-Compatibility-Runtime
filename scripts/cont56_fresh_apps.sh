#!/usr/bin/env bash
# cont56_fresh_apps.sh — CONT-56 Phase-A: fresh measured answer to the
# standing user question "did the work move Dooz and the calculators?".
# Runs at the current HEAD binary; the canonical config (--frames 5
# --max-seconds 15); dooz also at the fair 180 s budget (the CONT-43
# case-E face). Every face is kept under run/cont56/ for pixel analysis.
set -uo pipefail
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/cont56
mkdir -p "$OUT"
echo "binary: $(sha256sum $BIN | cut -c1-16)  head: $(git -C $BASE rev-parse --short HEAD)"

run1() { # run1 <label> <apkpath> <budget-seconds> <want-sha16|none>
  local label="$1" apk="$2" secs="$3" want="${4:-none}"
  local o="$OUT/$label"; rm -rf "$o"; mkdir -p "$o"
  timeout $((secs + 120)) "$BIN" run "$apk" --width 1080 --height 1920 \
    --frames 5 --max-seconds "$secs" -o "$o" > "$o/run.log" 2>&1
  local rc=$?
  local sha
  sha=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
  local verdict="recorded"
  [ "$want" != "none" ] && { verdict="DRIFT"; [ "$sha" = "$want" ] && verdict="MATCH"; }
  echo "FRESH $label rc=$rc sha=$sha want=$want $verdict"
}

case "${1:-apps}" in
apps)
  # --- calculators x3 (the standing anchors) ---
  for i in 1 2 3; do
    run1 "opencalc_r$i"  "$BASE/upload/opencalculator_53.apk"                          15 a976d2f9fb675cb3
    run1 "simplecalc_r$i" "$BASE/upload/cont54_refetch/com.simplemobiletools.calculator_8.apk" 15 e847ca0346708f07
    run1 "tanana_r$i"    "$BASE/upload/cont54_refetch/com.tananaev.calculator_11.apk"  15 5f7e0114c3bfd6b5
    run1 "bmi_r$i"       "$BASE/upload/cont11_apks/bmi_402.apk"                        15 b52252c2de19b03a
    run1 "alex_r$i"      "$BASE/upload/cont11_apks/alexcalc_20.apk"                    15 c8d69f811b23f245
  done
  # --- dooz 15s honest face x3 ---
  for i in 1 2 3; do
    run1 "dooz_r$i"      "$BASE/upload/canonical_apks/io.github.yamin8000.dooz_23.apk" 15 31ddd4d5b8e6d18e
  done
  echo "APPS-DONE"
  ;;
dooz180)
  # --- dooz at the fair budget (the case-E content face) ---
  for i in 1 2; do
    run1 "dooz180_r$i"   "$BASE/upload/canonical_apks/io.github.yamin8000.dooz_23.apk" 180 6841d52a20e6597e
  done
  echo "DOOZ180-DONE"
  ;;
esac
