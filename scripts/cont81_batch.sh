#!/bin/bash
# cont81_batch.sh — CONT-78 corpus expansion batch (26 NEW + 6 controls).
# Resume-friendly: one python invocation per APK; skip if row.json exists.
# The container resets periodically — this loop survives by design.
set -u
ROOT=/home/z/my-project
cd "$ROOT"
OUT="$ROOT/run/cont81/corpus_cont81_batch1"
STORE="$OUT/store"
MAN="$ROOT/run/cont75/interaction_manifest.json"
AAPT2="$ROOT/tools/toolchain/aapt2"
mkdir -p "$OUT" "$STORE"

APKS=(
  upload/telegram_official.apk
  upload/tg/forkgram.apk
  upload/cont50_apks/de.tobiasbielefeld.solitaire_71.apk
  upload/cont11_apks/alexcalc_20.apk
  upload/notes_secuso_105.apk
  upload/klondike_veldsoft_3.apk
  upload/canonical_apks/stack.tower3d_1.apk
  tmp/flappycow/app/release/app-release.apk
  upload/flappycow_rebuilt.apk
  upload/chess_jwtc_298.apk
  upload/canonical_apks/com.dozingcatsoftware.bouncy_43.apk
  upload/s105_apks/de.georgsieber.ballbreak_10.apk
  upload/cont54_refetch/com.tananaev.calculator_11.apk
  upload/cont11_apks/bmi_402.apk
  upload/cont54_refetch/com.simplemobiletools.calculator_8.apk
  upload/canonical_apks/com.github.muellerma.stopwatch_6.apk
  upload/canonical_apks/tripeaks_v1.2.1_vc4.apk
  upload/canonical_apks/fishrings_v1.23_vc6.apk
  upload/canonical_apks/opmt_v0.1.2_vc1.apk
  upload/s72_w4_apks/snake_v1.0_vc1.apk
  upload/s80_games/build_tetris/tetris_v1.0_vc1.apk
  upload/s80_games/build_sd/snake_deluxe_v1.0_vc1.apk
  upload/s80_games/build_2048/g2048_v1.0_vc1.apk
  upload/s98_games/build_snakeneon/snakeneon_v1.0_vc1.apk
  upload/s83_games/build_ttt/tictactoe_deluxe_v1.0_vc1.apk
  upload/s86_games/build_minicraft/minicraft_v1.0_vc1.apk
  upload/canonical_apks/dooz_23_toplevel.apk
  upload/opencalculator_53.apk
  upload/canonical_apks/app.varlorg.unote_30.apk
  upload/canonical_apks/de.duenndns.gmdice_8.apk
  upload/canonical_apks/dubrowgn.microtimer_8.apk
  upload/chessclock_29.apk
)

DONE=0; SKIP=0; FAIL=0
for apk in "${APKS[@]}"; do
  [ -f "$apk" ] || { echo "MISSING $apk"; FAIL=$((FAIL+1)); continue; }
  pkg=$("$AAPT2" dump badging "$apk" 2>/dev/null | grep -oP "package: name='\K[^']+")
  pkg="${pkg:-$(basename "$apk")}"
  if [ -f "$OUT/$pkg/row.json" ]; then
    SKIP=$((SKIP+1)); continue
  fi
  echo "=== RUN $pkg ($apk)"
  timeout 540 python3 scripts/cont81_corpus_runner.py "$apk" \
    --out "$OUT" --store "$STORE" \
    --frames 5 --budget 90 --repeat 1 \
    --manifest "$MAN" --label cont81_batch1
  rc=$?
  if [ -f "$OUT/$pkg/row.json" ]; then DONE=$((DONE+1)); else
    FAIL=$((FAIL+1)); echo "NO-ROW rc=$rc $pkg"
  fi
done

echo "=== COLLECT (done=$DONE skipped=$SKIP fail=$FAIL)"
python3 scripts/cont81_corpus_runner.py --collect --out "$OUT" \
  --label cont81_batch1
echo "BATCH_RC=$?"
