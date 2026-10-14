#!/bin/bash
# cont24_battery.sh — SKEL-LIGHT EXPERIMENT battery (CONT-24, test branch).
# A/B protocol: baseline binary (fa88902f, main-line) vs experiment binary
# (614677b6, skeleton-light hook behind MINIANDROID_SKELETON_LIGHT=1).
# Same canonical run command for both. rc printed per the CONT-22 audit law:
# the engine exits 0 ONLY on full SUCCESS (main.cpp:992).
set -uo pipefail
BASE=/home/z/my-project
BIN=$1                      # baseline | experiment binary path
OUT=$2                      # output root
MODE=${3:-base}             # base | skel
export MINIANDROID_SKELETON_LIGHT=$([ "$MODE" = skel ] && echo 1 || echo 0)

CA=$BASE/upload/canonical_apks
declare -A TARGETS=(
  [dooz]="$CA/dooz_23_toplevel.apk"
  [opencalc]="$BASE/upload/opencalculator_53.apk"
  [unote]="$CA/app.varlorg.unote_30.apk"
  [microtimer]="$CA/dubrowgn.microtimer_8.apk"
  [gmdice]="$CA/de.duenndns.gmdice_8.apk"
  [stopwatch]="$CA/com.github.muellerma.stopwatch_6.apk"
  [tictactoe]="$BASE/upload/s83_games/build_ttt/tictactoe_deluxe_v1.0_vc1.apk"
  [telegram]="$BASE/upload/telegram_official.apk"
  [notes]="$BASE/upload/notes_secuso_105.apk"
  [flappycow]="$BASE/upload/flappycow_rebuilt.apk"
  [ballbreak]="$BASE/upload/s105_apks/de.georgsieber.ballbreak_10.apk"
)

run1() { # label apk
  local label="$1" apk="$2"
  local o="$OUT/$label" rc sha
  rm -rf "$o"; mkdir -p "$o"
  timeout 300 "$BIN" run "$apk" --width 1080 --height 1920 \
    --frames 5 --max-seconds 15 -o "$o" > "$o/run.log" 2>&1
  rc=$?
  sha=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
  local m uncaught touched
  m=$(python3 "$BASE/scripts/cont24_metrics.py" "$o/screenshot.png" 2>/dev/null || echo '{}')
  uncaught=$(grep -c "FATAL\|Uncaught\|uncaught" "$o/run.log" 2>/dev/null || true)
  touched=$(grep -o "SKEL-LIGHT.*" "$o/run.log" 2>/dev/null | head -1)
  echo "BATTERY mode=$MODE t=$label rc=$rc png=$sha metrics=$m uncaught=$uncaught ${touched}"
}

for t in dooz opencalc unote microtimer gmdice stopwatch tictactoe telegram notes flappycow ballbreak; do
  [ -f "${TARGETS[$t]}" ] || { echo "BATTERY mode=$MODE t=$t MISSING_APK"; continue; }
  run1 "$t" "${TARGETS[$t]}"
done
