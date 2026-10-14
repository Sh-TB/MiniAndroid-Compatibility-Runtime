#!/usr/bin/env bash
# cont11_phase1_verify.sh — CONT-11 §2 primary-path verification at HEAD:
# dooz fallback-disabled x3 + F-NEW-259/259b runtime verification (probe
# APKs) + negatives + anchors. Run AFTER the clean rebuild.
BASE=/home/z/my-project
BIN=$BASE/miniandroid/build/miniandroid
OUT=$BASE/run/w7
APK=$BASE/upload/canonical_apks/io.github.yamin8000.dooz_23.apk
mkdir -p "$OUT"
echo "binary sha16: $(sha256sum "$BIN" | cut -c1-16)"

# ── 1) dooz baseline x3 (fallback-free by construction; no F-260 in tree) ──
ST="$OUT/store_dooz"
if [ ! -d "$ST" ]; then
  "$BIN" install "$APK" --data-root "$ST" > /dev/null 2>&1
fi
for i in 1 2 3; do
  o="$OUT/dooz_run$i"; rm -rf "$o"; mkdir -p "$o"
  "$BIN" run --package io.github.yamin8000.dooz --data-root "$ST" \
    --trace --max-seconds 120 --frames 40 -o "$o" > "$o/run.log" 2>&1
  s=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
  v=$(grep -oE '"verdict"[^,}]*|"classification"[^,}]*|VERDICT [A-Z_]+' "$o/run.log" | head -2 | tr '\n' ' ')
  echo "dooz_run$i sha=$s $v"
done

# ── 2) F-NEW-259/259b CONT-10 probe (7 rows) ────────────────────────────────
STP="$OUT/store_f259"
FAPK="$OUT/f259.apk"
if [ ! -f "$FAPK" ]; then bash "$BASE/scripts/cont10_build_probe.sh" > /dev/null 2>&1; fi
if [ ! -d "$STP" ]; then
  "$BIN" install "$FAPK" --data-root "$STP" > /dev/null 2>&1
fi
o="$OUT/f259_run"; rm -rf "$o"; mkdir -p "$o"
"$BIN" run --package com.probe.f259 --data-root "$STP" \
  --dump-view-tree --max-seconds 60 --frames 10 -o "$o" > "$o/run.log" 2>&1
echo "f259 probe view-tree rows:"
grep -oE "F259-[A-G]\|(PASS|FAIL)\|[^\"<]*" "$o/viewtree.txt" 2>/dev/null | head -10 || \
  grep -roE "F259-[A-G]\|(PASS|FAIL)[^\"<]*" "$o" 2>/dev/null | head -10 || \
  echo "  (extraction needs the viewtree dump — check $o/)"

# ── 3) F-NEW-259g genericity probe (rows H..T) ──────────────────────────────
STG="$OUT/store_f259g"
GAPK="$OUT/f259g.apk"
[ -f "$GAPK" ] || GAPK=""
if [ -n "$GAPK" ] && [ ! -d "$STG" ]; then
  "$BIN" install "$GAPK" --data-root "$STG" > /dev/null 2>&1
fi
if [ -n "$GAPK" ]; then
  o="$OUT/f259g_run"; rm -rf "$o"; mkdir -p "$o"
  "$BIN" run --package com.probe.f259g --data-root "$STG" \
    --dump-view-tree --max-seconds 60 --frames 10 -o "$o" > "$o/run.log" 2>&1
  echo "f259g probe rows:"
  grep -roE "F259-[A-T]\|(PASS|FAIL)[^\"<]*" "$o" 2>/dev/null | head -20
fi

# ── 4) fcol collection audit probe (rows K1..K18) ───────────────────────────
STC="$OUT/store_fcol"
CAPK="$OUT/fcol.apk"
if [ -f "$CAPK" ] && [ ! -d "$STC" ]; then
  "$BIN" install "$CAPK" --data-root "$STC" > /dev/null 2>&1
fi
if [ -f "$CAPK" ]; then
  o="$OUT/fcol_run"; rm -rf "$o"; mkdir -p "$o"
  "$BIN" run --package com.probe.fcol --data-root "$STC" \
    --dump-view-tree --max-seconds 60 --frames 10 -o "$o" > "$o/run.log" 2>&1
  echo "fcol probe rows:"
  grep -roE "K[0-9]+\|(PASS|FAIL)[^\"<]*" "$o" 2>/dev/null | head -20
fi
