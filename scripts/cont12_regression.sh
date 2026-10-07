#!/bin/bash
# cont12_regression.sh — CONT-12: full regression battery at the F-NEW-266
# binary (0ee46f5a719d2a8c). Contract: dooz + anchors byte-identical, f259
# probes PASS, negatives green, gate A, skill selftest.
set -uo pipefail
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/w8/reg
mkdir -p "$OUT"
echo "binary: $(sha256sum $BIN | cut -c1-16)"

run3() { # run3 <pkg> <store> <label> [extra]
  local pkg="$1" store="$2" label="$3"; shift 3
  for i in 1 2 3; do
    o="$OUT/${label}_$i"; rm -rf "$o"; mkdir -p "$o"
    "$BIN" run --package "$pkg" --data-root "$store" "$@" \
      --max-seconds 120 --frames 40 -o "$o" > "$o/run.log" 2>&1
    echo "$label run$i sha=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)"
  done
}

ST=$BASE/run/w8/store_dooz
[ -d "$ST" ] || "$BIN" install "$BASE/upload/canonical_apks/io.github.yamin8000.dooz_23.apk" --data-root "$ST" > /dev/null 2>&1
run3 io.github.yamin8000.dooz "$ST" dooz --trace

# anchors (opencalc/chess/microtimer/unote/sudoku_secuso)
for apkdir in "$BASE/upload/canonical_apks"/*.apk; do :; done
declare -A PKGS
PKGS["opencalc.apk"]="com.fmsys.opencalc"
PKGS["chess.apk"]="jp.sblo.pandora1.chess"
for f in "$BASE/upload/canonical_apks"/*.apk; do
  b=$(basename "$f")
  p="${PKGS[$b]}"
  if [ -n "$p" ]; then
    SA="$OUT/store_$b"; [ -d "$SA" ] || "$BIN" install "$f" --data-root "$SA" > /dev/null 2>&1
    run3 "$p" "$SA" "anchor_$b"
  fi
done
echo "battery part 1 done"
