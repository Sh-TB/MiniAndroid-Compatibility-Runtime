#!/usr/bin/env bash
# cont48_trains.sh — «چند قطار» wave: 9 deep trains (121f) on the fresh sandbox
# binary. Targets: 1 new NOT_TESTED unlock (APP-016 forkgram) + 8 deep re-runs
# of FLAT/shallow faces (M2 law: deeper runs upgrade FLAT -> RENDERED).
# ZERO-LOG: outputs untracked under run/cont48/trains/, evidence sha-only.
set -uo pipefail
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/cont48/trains
mkdir -p "$OUT"
cd "$BASE"

# --- roster: label|apk  (paths verified on disk) ---
ROSTER=$(mktemp)
cat > "$ROSTER" <<'EOF'
forkgram|upload/canonical_apks/forkgram_709208.apk
ball2box|upload/cont73_apks/com.simondalvai.ball2box_69.apk
klondike|upload/klondike_veldsoft_3.apk
opmt|upload/opmt_v0.1.2_vc1.apk
andstatus2048|upload/cont73_apks/org.andstatus.game2048_47.apk
chessjwtc|upload/chess_jwtc_298.apk
secusomemory|upload/canonical_apks/org.secuso.privacyfriendlymemory_100.apk
secusodame|upload/cont73_apks/org.secuso.privacyfriendlydame_101.apk
secusosolitaire|upload/cont73_apks/org.secuso.privacyfriendlysolitaire_4.apk
EOF

run_train() {
  local label="$1" apk="$BASE/$2"
  [ -f "$apk" ] || { echo "TRAIN|$label|SKIP-noapk"; return; }
  local o="$OUT/$label"
  rm -rf "$o"; mkdir -p "$o"
  timeout 240 "$BIN" run "$apk" --width 1080 --height 1920 \
    --frames 121 --max-seconds 60 --dump-view-tree -o "$o" \
    > "$o/run.log" 2>&1
  local rc=$?
  local sha face
  sha=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
  face=$(python3 "$BASE/scripts/cont48_face.py" "$o/screenshot.png" 2>/dev/null)
  echo "TRAIN|$label|rc=$rc|sha=$sha|$face"
}
export -f run_train
export BIN OUT BASE

echo "== launching $(wc -l < "$ROSTER") deep trains (P=5) =="
while IFS='|' read -r label rel; do
  echo "$label $rel"
done < "$ROSTER" | xargs -P 5 -n 2 bash -c 'run_train "$0" "$1"' \
  2>&1 | tee "$OUT/summary.txt" | grep -E "TRAIN"

echo "TRAINS-DONE rows=$(grep -c TRAIN "$OUT/summary.txt" 2>/dev/null)"
