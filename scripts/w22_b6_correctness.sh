#!/usr/bin/env bash
# w22_b6_correctness.sh — B6 gates after the knowledge integration:
#   1. dormant monolith dalvik_engine.cpp -fsyntax-only at production flags
#   2. full battery make test-all (serial)
#   3. production-binary original-APK spot checks (3 canonical shas)
#   4. binary identity records
set -u
cd /home/z/my-project/miniandroid
RUN="/usr/bin/python3 /home/z/my-project/scripts/w22_build_run.py"
OUT=evidence/w22/b6_results.jsonl
LOGD=evidence/w22/b6_logs
mkdir -p "$LOGD"
: > "$OUT"

echo "=== [1] engine.cpp dormant syntax check $(date -Is)" | tee -a "$LOGD/progress.txt"
$RUN --log "$LOGD/engine_syntax.log" --out "$OUT" g++ -std=c++17 -Wall -Wextra -O2 -MMD -MP \
  -DMINIANDROID_HAVE_WEBP -Isrc -Isrc/webview -Isrc/apk -Isrc/dex -Isrc/runtime -Isrc/api \
  -Isrc/graphics -Isrc/diagnostics -Isrc/resources -Isrc/renderer -Isrc/framework \
  -Isrc/storage -Isrc/fonts -Isrc/gles -Isrc/jni -Isrc/audio -Ithird_party/portablegl \
  -I/usr/include/freetype2 -Ithird_party/nlohmann_json/include -fsyntax-only \
  src/dex/dalvik_engine.cpp >/dev/null 2>&1
echo "engine_syntax rc=$? (0 = the E-05 edit compiles clean in the dormant monolith)" | tee -a "$LOGD/progress.txt"

echo "=== [2] full battery test-all $(date -Is)" | tee -a "$LOGD/progress.txt"
$RUN --log "$LOGD/testall.log" --out "$OUT" make -j1 --output-sync test-all >/dev/null 2>&1
grep -E "BATTERY SUMMARY|passed|failed" "$LOGD/testall.log" | tail -3 | tee -a "$LOGD/progress.txt"

echo "=== [3] production APK spot checks $(date -Is)" | tee -a "$LOGD/progress.txt"
declare -A CANON=( [ru.zxalexis.ugaday_15]=87fe2676 [tech.gaskell.diceroller_1_debug]=46b07062 [com.itsfrz.tictactoe_5]=d55056a8 )
for apk in ru.zxalexis.ugaday_15 tech.gaskell.diceroller_1_debug com.itsfrz.tictactoe_5; do
  rm -rf "/tmp/w22_spot_$apk"
  ./build/miniandroid run --max-seconds 60 --frames 3 -o "/tmp/w22_spot_$apk" \
      "/home/z/my-project/upload/handoff_apks/$apk.apk" > "$LOGD/spot_$apk.log" 2>&1
  rc=$?
  h=""
  [ -f "/tmp/w22_spot_$apk/screenshot.png" ] && h=$(sha256sum "/tmp/w22_spot_$apk/screenshot.png" | cut -c1-16)
  canon=${CANON[$apk]}
  if [[ "$h" == "$canon"* ]]; then verdict=MATCH; else verdict=DIFFERS; fi
  echo "SPOT $apk rc=$rc sha16=$h canonical=$canon $verdict" | tee -a "$LOGD/progress.txt"
done

echo "=== [4] binary identity $(date -Is)" | tee -a "$LOGD/progress.txt"
sha256sum build/miniandroid | tee -a "$LOGD/progress.txt"
echo "=== B6 DONE" | tee -a "$LOGD/progress.txt"
