#!/usr/bin/env bash
# s72_w4_corpus.sh — W4 fresh-evidence corpus re-run (constitution §18-22):
# same canonical recipe as s72_w3_corpus.sh on the SAME binary (a3f09ef2,
# HEAD 048b0e31) to (a) confirm W3 baselines hold with fresh SHAs and
# (b) measure constitution-impact deltas vs the W1 pre-constitution dashboard.
set -uo pipefail
ROOT=/home/z/my-project
ENG=$ROOT/miniandroid/build/miniandroid
CORPUS=$ROOT/upload/canonical_apks
OUT=$ROOT/run/s72_w4_corpus
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

# dooz determinism x3 (canonical recipe, independent runs)
for i in 1 2 3; do
  d="$OUT/dooz_det$i"
  rm -rf "$d"; mkdir -p "$d"
  (cd "$d" && timeout 150 "$ENG" run --execution-mode real-dalvik \
     --frames 9 --frame-delay 1500 \
     -o . "$CORPUS/dooz_23_toplevel.apk" > engine.log 2>&1)
done
echo "S72-W4 corpus re-run complete: $OUT"
