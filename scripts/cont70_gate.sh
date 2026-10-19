#!/usr/bin/env bash
# cont70_gate.sh — CONT-70 ant-army wall (updated WANT for g2048/tttdeluxe canvas-text law).
# Usage: cont68_reval_gate.sh <row>   (row = app name or dooz180; one row = 3 runs)
# Every row prints MATCH/CHANGED/FAIL vs the recorded wall.
set -uo pipefail
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/cont70/regression
mkdir -p "$OUT"
ROW=$1
declare -A APK WANT SECS
A=$BASE/upload
# CONT-108 adjudication (build-lineage face flip, F-NEW-443 precedent): the face
# flipped d3c26b73ee21e571 -> 5c4a0172628849ba at the fresh-worktree rebuild used
# for the F-NEW-453 decode (prewt @ 44bbcb21 + probes, BEFORE any CONT-108 fix
# code — bracketed: the flip is build-lineage-bound, not fix-bound; the same sha
# reproduces on the final probe-free fix binary). d3c26b73 = GL-path face of the
# long-lived incremental lineage (compose title+digits); 5c4a0172 = software-path
# windowBackground face of the fresh lineage (compose draw frontier remains the
# named open gap, same family as dooz F-NEW-443). Re-pinned x3 deterministic.
APK[csw]="$A/cont54_refetch/com.justdeax.composeStopwatch_1009011.apk";  WANT[csw]=5c4a0172628849ba;  SECS[csw]=15
# CONT-105 adjudication: fresh FULL rebuild (no incremental .o lineage) produces the
# software-path windowBackground face d602648e8e401895 (uniform @0xfffafafa painted
# by EXT01-WINBG law; compose content draw = known open frontier, ops=0). The old
# 31ddd4d5b8e6d18e = uniform-white GL-path face of the long-lived incremental build
# lineage. Both faces are background-only; the fafafa face is AOSP-true (theme
# windowBackground painted behind the not-yet-drawn compose tree). Re-pinned x3
# deterministic; full decode in evidence/cont105/ + registry F-NEW-443.
APK[dooz]="$A/canonical_apks/io.github.yamin8000.dooz_23.apk";           WANT[dooz]=d602648e8e401895; SECS[dooz]=15
APK[flappycow]="$A/flappycow_rebuilt.apk";                               WANT[flappycow]=13cf47464d9787f4; SECS[flappycow]=15
APK[g2048]="$A/s80_games/build_2048/g2048_v1.0_vc1.apk";                 WANT[g2048]=f43face08299ffc6; SECS[g2048]=15
APK[gmdice]="$A/canonical_apks/de.duenndns.gmdice_8.apk";                WANT[gmdice]=3891679dff449331; SECS[gmdice]=15
APK[microtimer]="$A/canonical_apks/dubrowgn.microtimer_8.apk";           WANT[microtimer]=bbd350b6c14fbd52; SECS[microtimer]=15
# CONT-107 adjudication (F-NEW-450 TypedArray dimension law): the old face
# f25b754c4565c38b encoded SlidingUpPanelLayout umanoPanelHeight answered as the
# RAW complex word (10497) — AOSP-true is complexToDimensionPixelSize = 41dp x
# 2.625 density = 108px. Under the correct law the layout chain diverges (F-NEW-451
# downstream content gap registered: keypad-only face, text/drawables missing).
# Both faces deterministic x3; the 13d2d6d8 face is the AOSP-true-dims face.
# CONT-108 adjudication (F-NEW-453 degenerate self-report law): the CONT-107 face
# 13d2d6d836f75e7f encoded the app-bundled androidx ConstraintLayout solver's
# degenerate setMeasuredDimension(0,0) surviving the DEX readback — the umano
# coverage law then compared two identical zero-size rects and hid the keypad
# (F-NEW-451). Under the F-NEW-453 law (degenerate EXACTLY>0 self-reports route
# to the canonical container law; stale dex_measured invalidated at the
# R-NEW-438 takeover) the full keypad renders. AOSP-true: opencalc shows its
# keypad on real ART; the collapsed 41dp panel handle occupies the bottom 108px.
# Re-pinned x3 deterministic; decode chain in run/c108/ + evidence/cont108/.
APK[opencalc]="$A/opencalculator_53.apk";                                WANT[opencalc]=d5f3c7b5e9936ae6; SECS[opencalc]=15
APK[simplecalc]="$A/cont54_refetch/com.simplemobiletools.calculator_8.apk"; WANT[simplecalc]=2ac5d8d0cbf9552a; SECS[simplecalc]=15
# CONT-108 adjudication (F-NEW-453 improvement): the old face afe0bd8dd4d09ca6
# was the GREY-200 fill face (F-NEW-338 family) hiding the app's real preference
# content behind the app-bundled ConstraintLayout solver's degenerate 0x0
# self-report. Under F-NEW-453 the native/canonical measure law feeds the real
# box and the notification-settings text rows render (Notification settings /
# Ongoing notification / Lock screen notification labels). IMPROVEMENT drift,
# re-pinned x3 deterministic (10174486e7753fb6).
APK[tanana]="$A/cont54_refetch/com.tananaev.calculator_11.apk";          WANT[tanana]=10174486e7753fb6; SECS[tanana]=15
APK[tttdeluxe]="$A/s83_games/build_ttt/tictactoe_deluxe_v1.0_vc1.apk";   WANT[tttdeluxe]=db1d633d77b5819a; SECS[tttdeluxe]=15
APK[unote]="$A/canonical_apks/app.varlorg.unote_30.apk";                 WANT[unote]=90a67cc1ddda57b7; SECS[unote]=15
APK[dooz180]="$A/canonical_apks/io.github.yamin8000.dooz_23.apk";        WANT[dooz180]=c94da5a928ea213b; SECS[dooz180]=180
name=$ROW
apk="${APK[$name]:-}"; want="${WANT[$name]:-}"; secs="${SECS[$name]:-15}"
if [ -z "$apk" ]; then echo "unknown row $ROW"; exit 2; fi
for i in 1 2 3; do
  o="$OUT/${name}_r$i"; rm -rf "$o"; mkdir -p "$o"
  timeout 135 "$BIN" run "$apk" --width 1080 --height 1920 --frames 5 --max-seconds "$secs" -o "$o" > "$o/run.log" 2>&1
  rc=$?
  sha=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
  verdict="DRIFT"; [ "$sha" = "$want" ] && verdict="MATCH"
  [ "$sha" != "$want" ] && [ $rc -eq 0 ] && verdict="CHANGED"
  [ $rc -ne 0 ] && [ -z "$sha" ] && verdict="FAIL"
  echo "GATE $name r$i rc=$rc sha=$sha want=$want $verdict"
done
