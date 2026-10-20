#!/usr/bin/env bash
# cont113_matrix.sh — CONT-113 wagon 1: #366 matrix revalidation at current HEAD.
# 4 working controls (opencalc/unote/microtimer/chess) + 5 white targets
# (stack.tower3d, stopwatch, solitaire, tripeaks, fishrings) per #366 §1.
# Per target: pkginspect identity -> install -> installed-sha proof -> run by
# package (source hidden = run reads the installed base.apk only) -> collect
# trace_summary.json verdicts. White targets run 3x (determinism law).
set -u
cd /home/z/my-project
BIN=miniandroid/build/miniandroid
W=run/c113
STORE=$W/store
mkdir -p "$W" "$STORE"
LOG=$W/matrix.log
: > "$LOG"

run_one() { # name apk pkg runs
  local name="$1" apk="$2" pkg="$3" runs="$4"
  echo "== ROW $name ==" | tee -a "$LOG"
  # identity
  timeout 60 $BIN pkginspect --apk "$apk" --what identity > "$W/$name.identity.json" 2>>"$LOG" || { echo "$name IDENTITY-FAIL" | tee -a "$LOG"; return; }
  local src_sha=$(python3 -c "import json;d=json.load(open('$W/$name.identity.json'));print(d.get('sha256',d.get('apk_sha256',''))[:16])" 2>/dev/null)
  echo "src_sha16=$src_sha" | tee -a "$LOG"
  # install
  timeout 120 $BIN install "$apk" --data-root "$STORE" > "$W/$name.install.json" 2>>"$LOG" || { echo "$name INSTALL-FAIL" | tee -a "$LOG"; return; }
  local inst_sha=$(python3 -c "import json;d=json.load(open('$W/$name.install.json'));print(str(d.get('sha256',d.get('apk_sha256','')))[:16])" 2>/dev/null)
  echo "inst_sha16=$inst_sha" | tee -a "$LOG"
  [ -n "$src_sha" ] && [ "$src_sha" = "$inst_sha" ] && echo "SHA-PROOF MATCH" | tee -a "$LOG" || echo "SHA-PROOF MISMATCH (src=$src_sha inst=$inst_sha)" | tee -a "$LOG"
  # runs
  for i in 1 2 3; do
    [ "$i" -gt "$runs" ] && break
    timeout 180 $BIN run --package "$pkg" --data-root "$STORE" --width 1080 --height 1920 --frames 5 --max-seconds 60 -o "$W/$pkg/r$i" > /dev/null 2> "$W/$name.r$i.log"
    local rc=$?
    echo "run$i rc=$rc" | tee -a "$LOG"
    if [ -f "$W/$pkg/r$i/trace_summary.json" ]; then
      python3 - "$W/$pkg/r$i/trace_summary.json" "$W/$name.r$i.verdict" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
fa = d.get('frame_analysis', {})
out = {
 'verdict': fa.get('verdict'),
 'pixel_class': fa.get('pixel_class'),
 'app_owned_pixels': fa.get('app_owned_pixels'),
 'app_draw_ops': fa.get('app_draw_ops'),
 'first_missing_stage': fa.get('first_missing_stage'),
 'colors': fa.get('unique_colors'),
}
open(sys.argv[2], 'w').write(json.dumps(out))
PY
      echo "verdict$i=$(cat $W/$name.r$i.verdict 2>/dev/null | tr -d '\n')" | tee -a "$LOG"
      [ -f "$W/$pkg/r$i/screenshot.png" ] && echo "shot$i=$(sha256sum $W/$pkg/r$i/screenshot.png | cut -c1-16)" | tee -a "$LOG"
    else
      echo "verdict$i=NO_TRACE_SUMMARY" | tee -a "$LOG"
    fi
  done
}

# ---- 4 working controls (1 run each; wall-anchored separately) ----
run_one opencalc upload/opencalculator_53.apk com.darkempire78.opencalculator 1
run_one unote   upload/canonical_apks/app.varlorg.unote_30.apk app.varlorg.unote 1
run_one microtimer upload/canonical_apks/dubrowgn.microtimer_8.apk dubrowgn.microtimer 1
run_one chess   upload/chess_jwtc_298.apk jwtc.android.chess 1
# ---- 5 white targets (3 runs each) ----
run_one tower3d  upload/canonical_apks/stack.tower3d_1.apk stack.tower3d 3
run_one stopwatch upload/canonical_apks/com.github.muellerma.stopwatch_6.apk com.github.muellerma.stopwatch 3
run_one solitaire upload/cont50_apks/de.tobiasbielefeld.solitaire_71.apk de.tobiasbielefeld.solitaire 3
run_one tripeaks upload/canonical_apks/tripeaks_v1.2.1_vc4.apk eu.veldsoft.tri.peaks 3
run_one fishrings upload/canonical_apks/fishrings_v1.23_vc6.apk eu.veldsoft.fish.rings 3

echo "MATRIX DONE" | tee -a "$LOG"
