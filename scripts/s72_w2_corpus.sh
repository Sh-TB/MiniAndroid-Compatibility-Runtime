#!/usr/bin/env bash
# s72_w2_corpus.sh — F-142 fix regression: full 10-APK corpus re-run with the
# SAME canonical recipe as s71_live_runs.sh (Rule 1/2: no second system).
# Fresh evidence on current binary (constitution #9/#64): per-run frame_008
# nonwhite + screenshot sha. Determinism x3 for fishrings (RULE 63/124).
set -uo pipefail
ROOT=/home/z/my-project
ENG=$ROOT/miniandroid/build/miniandroid
CORPUS=$ROOT/upload/canonical_apks
OUT=$ROOT/run/s72_w2_corpus
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
  (cd "$d" && timeout 150 "$ENG" run --execution-mode real-dalvik \
     --frames 9 --frame-delay 1500 \
     --dump-api-trace --dump-view-tree \
     -o . "$CORPUS/$apk" > engine.log 2>&1)
  echo "$name rc=$?"
done

# fishrings determinism x3 (canonical recipe, independent runs)
for i in 1 2 3; do
  d="$OUT/fishrings_det$i"
  rm -rf "$d"; mkdir -p "$d"
  (cd "$d" && timeout 150 "$ENG" run --execution-mode real-dalvik \
     --frames 9 --frame-delay 1500 \
     -o . "$CORPUS/fishrings_v1.23_vc6.apk" > engine.log 2>&1)
done
echo "S72-W2 corpus re-run complete: $OUT"
