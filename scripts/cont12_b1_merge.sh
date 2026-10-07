#!/bin/bash
# cont12_b1_merge.sh — CONT-12 PHASE 3 experiment B (literal): dooz APK
# + real matching Compose artifacts (classes.jar set, D8-merged) → TEST APK.
# The renamed references in dooz's own DEX bind to the renamed classes;
# the real-name classes are added dead. Purpose: MEASURE the binding wall
# (expected: byte-identical baseline anchor).
set -uo pipefail
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
WORK=$BASE/tmp/cont12_b1
OUT=$BASE/run/w8
CLS=$BASE/upstream/cont12_maven/classes
mkdir -p "$WORK/dex" "$OUT"
cp "$BASE/upload/canonical_apks/io.github.yamin8000.dooz_23.apk" "$OUT/dooz_b1_merged.apk"
# D8-merge the real artifacts into secondary dex files
ls "$CLS"/*.jar | while read -r j; do
  [ -f "$j" ] && head -c 2 "$j" | grep -q "PK" && echo "$j"
done > "$WORK/jars.txt"
java -Xmx2g -cp "$BASE/tools/toolchain/r8.jar" com.android.tools.r8.D8 --release --min-api 26 \
  --lib "$BASE/tools/toolchain/android-34.jar" --output "$WORK/dex" @"$WORK/jars.txt" 2>&1 | grep -cE "Warning" || true
cd "$WORK/dex" && for d in *.dex; do zip -j -X "$OUT/dooz_b1_merged.apk" "$d" > /dev/null; done
cd "$BASE"
echo "merged apk: $(sha256sum "$OUT/dooz_b1_merged.apk" | cut -c1-16)"
unzip -l "$OUT/dooz_b1_merged.apk" | grep -cE "classes.*\.dex"
# install + run x3
ST="$OUT/store_b1"; rm -rf "$ST"
"$BIN" install "$OUT/dooz_b1_merged.apk" --data-root "$ST" > /dev/null 2>&1; echo "install rc=$?"
for i in 1 2 3; do
  o="$OUT/b1_run$i"; rm -rf "$o"; mkdir -p "$o"
  "$BIN" run --package io.github.yamin8000.dooz --data-root "$ST" \
    --trace --max-seconds 120 --frames 40 -o "$o" > "$o/run.log" 2>&1
  echo "b1_run$i sha=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)"
done
