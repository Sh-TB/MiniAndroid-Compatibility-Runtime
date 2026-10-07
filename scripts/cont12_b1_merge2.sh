#!/bin/bash
# cont12_b1_merge2.sh — experiment B (literal) v2: fresh re-zip merge
# (no in-place append; dooz entries + real-Compose secondary dexes).
set -uo pipefail
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
WORK=$BASE/tmp/cont12_b1
OUT=$BASE/run/w8
CLS=$BASE/upstream/cont12_maven/classes
rm -rf "$WORK/rezip"; mkdir -p "$WORK/rezip" "$OUT"
# 1) D8-merge real artifacts into secondary dexes (already built in $WORK/dex)
ls "$WORK/dex"/*.dex > /dev/null 2>&1 || { echo "no dexes"; exit 1; }
# 2) unpack dooz and re-zip fresh
D="$WORK/rezip/apk"; mkdir -p "$D"
unzip -q -o "$BASE/upload/canonical_apks/io.github.yamin8000.dooz_23.apk" -d "$D"
for d in "$WORK/dex"/*.dex; do
  b=$(basename "$d"); n=2
  while [ -f "$D/classes$n.dex" ]; do n=$((n+1)); done
  cp "$d" "$D/classes$n.dex"
done
# arsc STORED (AOSP requirement), everything else deflated
cd "$D"
zip -q -X -r /tmp/b1_new.apk . -x resources.arsc > /dev/null
zip -q -X -0 /tmp/b1_new.apk resources.arsc > /dev/null
cd "$BASE"
cp /tmp/b1_new.apk "$OUT/dooz_b1_merged.apk"
echo "merged apk: $(sha256sum "$OUT/dooz_b1_merged.apk" | cut -c1-16) size=$(stat -c%s "$OUT/dooz_b1_merged.apk")"
unzip -l "$OUT/dooz_b1_merged.apk" | grep -E "classes.*\.dex" 
# 3) install + run x3
ST="$OUT/store_b1"; rm -rf "$ST"
"$BIN" install "$OUT/dooz_b1_merged.apk" --data-root "$ST" > /dev/null 2>&1; echo "install rc=$?"
for i in 1 2 3; do
  o="$OUT/b1_run$i"; rm -rf "$o"; mkdir -p "$o"
  "$BIN" run --package io.github.yamin8000.dooz --data-root "$ST" \
    --trace --max-seconds 120 --frames 40 -o "$o" > "$o/run.log" 2>&1
  v=$(grep -oE 'verdict=[A-Z_]+' "$o/run.log" | head -1)
  echo "b1_run$i sha=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16) $v"
done
grep -E "EXP088-MD-INJECT|EXP068" b1_run1/run.log | head -3
