#!/bin/bash
# cont28_f141_trace.sh — CONT-28 W1: live trace of the f141-null-recv family
# (webstack <clinit> pc=47 + audiobook Lhm;.n pc=30) to find the
# null-producing framework API — the family root behind 3+ census titles.
set -uo pipefail
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/cont28/f141
mkdir -p "$OUT"

for t in webstack audiobook; do
  case "$t" in
    webstack)  APK="$BASE/upload/fdroid_batch/com.chiranth7.webstack_6.apk";;
    audiobook) APK="$BASE/upload/fdroid_batch/de.ph1b.audiobook_5410002.apk";;
  esac
  ST="$OUT/store_$t"
  if [ ! -d "$ST" ]; then
    "$BIN" install "$APK" --data-root "$ST" > "$OUT/${t}_install.log" 2>&1
    echo "$t install rc=$?"
  fi
  # PKG = derive from apk filename
  case "$t" in
    webstack)  PKG=com.chiranth7.webstack;;
    audiobook) PKG=de.ph1b.audiobook;;
  esac
  mkdir -p "$OUT/$t"
  MINIANDROID_F141_DIAG=1 MINIANDROID_COMPOSE_MEASURE_TRACE=1 \
    "$BIN" run --package "$PKG" --data-root "$ST" \
    --max-seconds 90 --frames 20 -o "$OUT/$t" \
    > "$OUT/$t/run.log" 2> "$OUT/$t/diag.txt"
  echo "$t run rc=$?"
done

echo "=== webstack: the exact pc=47 face + surrounding ==="
grep -n "f141-null-recv" "$OUT/webstack/diag.txt" | head -3
echo "=== webstack: clinit trace around Lru1; ==="
grep -n "Lru1;" "$OUT/webstack/diag.txt" | head -20
echo "=== audiobook: Lhm;.n face ==="
grep -n "f141-null-recv" "$OUT/audiobook/diag.txt" | head -3
grep -n "Lhm;" "$OUT/audiobook/diag.txt" | head -12
