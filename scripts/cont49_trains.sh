#!/usr/bin/env bash
# cont49_trains.sh — «چند قطار» CONT-49 wave: 36 parallel deep trains (121f)
# on every evidence-less APK on disk (roster from cont49_roster.py).
# Each train = one program through the HEAD engine binary. Face classified by
# cont48_face.py (honest classes: GREEN/RENDERED/DARK/FLAT/BLANK).
# ZERO-LOG: outputs untracked under run/cont49/trains/, evidence sha-only.
set -uo pipefail
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/cont49/trains
ROSTER=$BASE/run/cont49/roster.tsv
mkdir -p "$OUT"
cd "$BASE"

run_train() {
  local label="$1" apk="$2"
  [ -f "$apk" ] || { echo "TRAIN|$label|SKIP-noapk"; return; }
  local o="$OUT/$label"
  rm -rf "$o"; mkdir -p "$o"
  timeout 240 "$BIN" run "$apk" --width 1080 --height 1920 \
    --frames 121 --max-seconds 60 --dump-view-tree -o "$o" \
    > "$o/run.log" 2>&1
  local rc=$?
  local sha face pkg
  sha=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
  face=$(python3 "$BASE/scripts/cont48_face.py" "$o/screenshot.png" 2>/dev/null)
  pkg=$(grep -m1 '^\- \*\*Package:\*\*' "$o/report.md" 2>/dev/null | sed 's/.*`\([^`]*\)`.*/\1/')
  echo "TRAIN|$label|rc=$rc|sha=$sha|$face|pkg=$pkg"
}
export -f run_train
export BIN OUT BASE

echo "== launching $(wc -l < "$ROSTER") trains (P=6) =="
while IFS=$'\t' read -r label apk; do
  echo "$label $apk"
done < "$ROSTER" | xargs -P 6 -n 2 bash -c 'run_train "$0" "$1"' \
  2>&1 | tee "$OUT/summary.txt" | grep -E "TRAIN"

echo "TRAINS-DONE rows=$(grep -c TRAIN "$OUT/summary.txt" 2>/dev/null)"
