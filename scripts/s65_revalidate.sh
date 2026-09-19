#!/usr/bin/env bash
# s65_revalidate.sh — §12: rerun the three S65 apps on the F-120 engine,
# capture full frames + independent metrics, compare SHAs against the S65
# report values (F-120 law change is EXPECTED to move Button-family labels).
set -uo pipefail
REPO=/home/z/my-project
BIN="$REPO/miniandroid/build/miniandroid"
OUT="$REPO/run/s66_reval"
mkdir -p "$OUT"

echo "════ FishRings (S10 recipe) ════"
timeout 500 "$BIN" run --execution-mode real-dalvik --frames 9 --frame-delay 1500 \
  --tap 5,5 --tap 5,5 --tap 5,5 --tap 5,5 \
  --tap 540,960 --tap 270,960 --tap 810,960 \
  -o "$OUT/fishrings" "$REPO/upload/s65_apks/fishrings_v1.23_vc6.apk" \
  > "$OUT/fishrings_stdout.log" 2>&1
echo "rc=$?"
ls "$OUT/fishrings/frames/" 2>/dev/null | head -12

echo "════ TriPeaks lobby probe (verbose, find New Game bounds) ════"
timeout 500 "$BIN" run --execution-mode real-dalvik --frames 5 --frame-delay 1500 \
  --tap 5,5 -v \
  -o "$OUT/tripeaks_probe" "$REPO/upload/s65_apks/tripeaks_v1.2.1_vc4.apk" \
  > "$OUT/tripeaks_probe.log" 2>&1
echo "rc=$?"
grep -E "EXP092-RENDER" "$OUT/tripeaks_probe.log" | grep -iE "lobby|game|button" | head -12

echo "════ OPMT (S6 recipe: menu tap → GameActivity) ════"
timeout 500 "$BIN" run --execution-mode real-dalvik --frames 6 --frame-delay 1500 \
  --tap 277,1379 \
  -o "$OUT/opmt" "$REPO/upload/s65_apks/opmt_v0.1.2_vc1.apk" \
  > "$OUT/opmt_stdout.log" 2>&1
echo "rc=$?"
ls "$OUT/opmt/frames/" 2>/dev/null | head -8
