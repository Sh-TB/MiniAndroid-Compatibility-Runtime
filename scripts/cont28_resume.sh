#!/usr/bin/env bash
# cont28_resume.sh — resume the CONT-28 regression gate: verify completed
# run dirs against expectations, re-run only missing ones. rc-truth law.
set -uo pipefail
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/cont28/regression
LOG=$BASE/run/cont28/regression_gate.log
mkdir -p "$OUT"

declare -A WANT=(
  [dooz]=d602648e8e401895 [microtimer]=da73010a37dd0189 [unote]=4f1a9e4e8f64fae8
  [gmdice]=f3b483fe7b7cf51b [opencalc]=a976d2f9fb675cb3 [tttdeluxe]=af6094295ecb50e3
  [flappycow]=13cf47464d9787f4 [g2048]=59ca1526611c4622
)
declare -A APK
APK[dooz]=$BASE/upload/canonical_apks/io.github.yamin8000.dooz_23.apk
APK[microtimer]=$BASE/upload/canonical_apks/dubrowgn.microtimer_8.apk
APK[unote]=$BASE/upload/canonical_apks/app.varlorg.unote_30.apk
APK[gmdice]=$BASE/upload/canonical_apks/de.duenndns.gmdice_8.apk
APK[opencalc]=$BASE/upload/opencalculator_53.apk
APK[tttdeluxe]=$BASE/upload/s83_games/build_ttt/tictactoe_deluxe_v1.0_vc1.apk
APK[flappycow]=$BASE/upload/flappycow_rebuilt.apk
APK[g2048]=$BASE/upload/s80_games/build_2048/g2048_v1.0_vc1.apk

run1() { # run1 <label> <apk> <want|none>
  local label="$1" apk="$2" want="${3:-none}"
  local o="$OUT/$label"; rm -rf "$o"; mkdir -p "$o"
  timeout 300 "$BIN" run "$apk" --width 1080 --height 1920 \
    --frames 5 --max-seconds 15 -o "$o" > "$o/run.log" 2>&1
  local rc=$? sha verdict="DRIFT"
  sha=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
  [ "$sha" = "$want" ] && verdict="MATCH"
  [ "$want" = "none" ] && verdict="recorded"
  echo "REG $label rc=$rc sha=$sha want=$want $verdict" | tee -a "$LOG"
}

echo "=== RESUME GATE $(date -u +%H:%M:%S) ===" | tee -a "$LOG"

# 1) verify/complete anchors x3
for t in dooz microtimer unote gmdice opencalc tttdeluxe flappycow g2048; do
  for r in 1 2 3; do
    lbl="${t}_r$r"
    d="$OUT/$lbl"
    sha=$(sha256sum "$d/screenshot.png" 2>/dev/null | cut -c1-16)
    if [ "$sha" = "${WANT[$t]}" ]; then
      echo "REG $lbl KEEP sha=$sha MATCH" | tee -a "$LOG"
    else
      run1 "$lbl" "${APK[$t]}" "${WANT[$t]}"
    fi
  done
done

# 2) oracle + simplecalc x3 (recorded)
ORACLE=$BASE/run/w8/oracle12.apk
SIMPLECALC=$BASE/tmp/cont26_apks/simplecalc_8.apk
for r in 1 2 3; do
  lbl="oracle_r$r"; d="$OUT/$lbl"
  [ -f "$d/screenshot.png" ] && echo "REG $lbl KEEP sha=$(sha256sum $d/screenshot.png | cut -c1-16)" | tee -a "$LOG" || run1 "$lbl" "$ORACLE" none
  lbl="simplecalc_r$r"; d="$OUT/$lbl"
  if [ -f "$d/screenshot.png" ]; then
    rc=$(grep -oE "rc=[0-9]+" /dev/null 2>/dev/null); echo "REG $lbl KEEP sha=$(sha256sum $d/screenshot.png | cut -c1-16)" | tee -a "$LOG"
  else
    o="$OUT/$lbl"; rm -rf "$o"; mkdir -p "$o"
    timeout 300 "$BIN" run "$SIMPLECALC" --width 1080 --height 1920 --frames 5 --max-seconds 15 -o "$o" > "$o/run.log" 2>&1
    rc=$?
    sha=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
    status=$(grep -E "Status:" "$o/run.log" | tail -1 | cut -c1-40)
    echo "REG $lbl rc=$rc sha=$sha want=none recorded ($status)" | tee -a "$LOG"
  fi
done

# 3) probe battery
if [ ! -f "$BASE/run/w7/fcol.apk" ]; then
  bash $BASE/scripts/cont21_build_probes.sh > "$OUT/probe_build.log" 2>&1 || echo "PROBE BUILD FAILED" | tee -a "$LOG"
fi
probe1() { # probe1 <label> <apk>
  local label="$1" apk="$2"
  local o="$OUT/probe_$label"; rm -rf "$o"; mkdir -p "$o"
  timeout 300 "$BIN" run "$apk" --width 1080 --height 1920 \
    --frames 5 --max-seconds 15 -o "$o" > "$o/run.log" 2>&1
  local rc=$? pass fail
  pass=$(grep -oE "\|PASS\|" "$o/run.log" 2>/dev/null | wc -l)
  fail=$(grep -oE "\|FAIL\|" "$o/run.log" 2>/dev/null | wc -l)
  echo "PROBE $label rc=$rc PASS=$pass FAIL=$fail" | tee -a "$LOG"
}
probe1 fcol  "$BASE/run/w7/fcol.apk"
probe1 f259  "$BASE/run/w7/f259.apk"
probe1 f259g "$BASE/run/w7/f259g.apk"
probe1 f266  "$BASE/run/w8/f266.apk"
probe1 f268  "$BASE/run/cont18g/f268.apk"

echo "RESUME GATE DONE $(date -u +%H:%M:%S)" | tee -a "$LOG"
