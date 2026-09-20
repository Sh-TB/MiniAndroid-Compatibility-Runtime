#!/usr/bin/env bash
# s71_live_runs.sh — S71 FORENSIC TRIAGE: regenerate the live dispatch-surface
# evidence via the SAME canonical recipe as s69_live_runs.sh (S70 tool reuse —
# Rule 1/2: no second system). Differences: OUT=run/s71_live and api_calls.json
# (raw per-call traces) are retained on disk for the forensic classifier.
set -uo pipefail
ROOT=/home/z/my-project
ENG=$ROOT/miniandroid/build/miniandroid
CORPUS=$ROOT/upload/canonical_apks
OUT=$ROOT/run/s71_live
mkdir -p "$OUT"

APKS=(
  app.varlorg.unote_30.apk
  bouncy.apk
  com.emmanuelmess.tictactoe_3.apk
  com.github.muellerma.stopwatch_6.apk
  de.duenndns.gmdice_8.apk
  dooz_23_toplevel.apk
  dubrowgn.microtimer_8.apk
  fishrings_v1.23_vc6.apk
  opmt_v0.1.2_vc1.apk
  tripeaks_v1.2.1_vc4.apk
)

for apk in "${APKS[@]}"; do
  name="${apk%.apk}"
  d="$OUT/$name"
  rm -rf "$d"; mkdir -p "$d"
  # canonical corpus recipe (S65/S66 session ledger): real-dalvik + 9-frame
  # pump with 1500ms virtual frame delay (splash Timer navigation lands)
  (cd "$d" && timeout 150 "$ENG" run --execution-mode real-dalvik \
     --frames 9 --frame-delay 1500 \
     --dump-api-trace --dump-view-tree \
     -o . "$CORPUS/$apk" > engine.log 2>&1)
  echo "$name rc=$?"
done
echo "S71 live re-run complete: $OUT"
