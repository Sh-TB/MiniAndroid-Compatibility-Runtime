#!/usr/bin/env bash
# s73_corpus.sh — S73 historical-corpus re-run (PART B): 10 canonical APKs on
# the CURRENT binary (rebuild + F-117 scheduled-tap extension), canonical
# recipe (same as s72_w4_corpus.sh) + AndroidGameSnake + dooz det x3.
# Output: run/s73_corpus/<app>/ {engine.log, frames/, screenshot.png,
# view_tree.json, api_trace.json, lifecycle_trace.json}
set -uo pipefail
ROOT=/home/z/my-project
ENG=$ROOT/miniandroid/build/miniandroid
CORPUS=$ROOT/upload/canonical_apks
OUT=$ROOT/run/s73_corpus
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

# AndroidGameSnake (S72-W4 target, no taps: launch-state baseline)
d="$OUT/androidgamesnake"
rm -rf "$d"; mkdir -p "$d"
(cd "$d" && timeout 150 "$ENG" run --execution-mode real-dalvik \
   --frames 9 --frame-delay 250 \
   --dump-api-trace --dump-view-tree \
   -o . "$ROOT/upload/s72_w4_apks/snake_v1.0_vc1.apk" > engine.log 2>&1)
echo "androidgamesnake rc=$?"

# dooz determinism x3 (canonical recipe, independent runs)
for i in 1 2 3; do
  d="$OUT/dooz_det$i"
  rm -rf "$d"; mkdir -p "$d"
  (cd "$d" && timeout 150 "$ENG" run --execution-mode real-dalvik \
     --frames 9 --frame-delay 1500 \
     -o . "$CORPUS/dooz_23_toplevel.apk" > engine.log 2>&1)
done
echo "S73 corpus re-run complete: $OUT"
