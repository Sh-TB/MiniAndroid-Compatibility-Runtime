#!/usr/bin/env bash
# cont46_fanout.sh — CONT-46 Phase-5 real-APK fan-out ×3 on the F-058-R
# binary: BMI, AlexCalc, Solitaire, notes + evidence rows per run.
set -uo pipefail
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/cont46/fanout
mkdir -p "$OUT"
cd "$BASE"

run3() { # run3 <label> <apk> [extra args]
  local label="$1" apk="$2"; shift 2
  for i in 1 2 3; do
    local o="$OUT/${label}_r$i"
    rm -rf "$o"; mkdir -p "$o"
    timeout 300 "$BIN" run "$apk" --width 1080 --height 1920 \
      --frames 5 --max-seconds 20 --dump-view-tree "$@" -o "$o" \
      > "$o/run.log" 2>&1
    local rc=$?
    local sha unc
    sha=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
    unc=$(grep -cE "Uncaught" "$o/run.log" 2>/dev/null)
    echo "FANOUT $label r$i rc=$rc sha=$sha uncaught=$unc"
  done
}

echo "== targets =="
run3 bmi    "$BASE/upload/cont11_apks/bmi_402.apk"
run3 sol    "$BASE/run/cont11/store_solitaire/data/app/de.tobiasbielefeld.solitaire/base.apk"
run3 notes  "$BASE/upload/notes_secuso_105.apk"
run3 alex   "$BASE/upload/cont11_apks/alexcalc_20.apk"

echo "== controls (same binary) =="
run3 dooz   "$BASE/upload/canonical_apks/io.github.yamin8000.dooz_23.apk"
run3 micro  "$BASE/upload/canonical_apks/dubrowgn.microtimer_8.apk"
run3 unote  "$BASE/upload/canonical_apks/app.varlorg.unote_30.apk"
echo "FANOUT-DONE"
