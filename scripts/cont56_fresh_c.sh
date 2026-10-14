#!/usr/bin/env bash
# cont56_fresh.sh — user-facing six-app honest scoreboard at HEAD (fresh binary cb1d33e62ad18fe0).
# Runs the 4 view-based calculators x3 + dooz 180s x2. opencalc x3 already done (anchors gate).
B=/home/z/my-project/miniandroid/build/miniandroid
OUT=/home/z/my-project/run/cont56c
mkdir -p "$OUT"
declare -A APK=(
  [simplecalc]=/home/z/my-project/upload/cont54_refetch/com.simplemobiletools.calculator_8.apk
  [tanana]=/home/z/my-project/upload/cont54_refetch/com.tananaev.calculator_11.apk
  [bmi]=/home/z/my-project/upload/cont11_apks/bmi_402.apk
  [alex]=/home/z/my-project/upload/cont11_apks/alexcalc_20.apk
)
declare -A PKG=(
  [simplecalc]=com.simplemobiletools.calculator
  [tanana]=com.tananaev.calculator
  [bmi]=com.zola.bmi
  [alex]=net.alexbarry.calc_android
)
for name in simplecalc tanana bmi alex; do
  st="$OUT/store_$name"
  if [ ! -d "$st/data/app/${PKG[$name]}" ]; then
    "$B" install "${APK[$name]}" --data-root "$st" > /dev/null 2>&1
  fi
  shas=""
  for i in 1 2 3; do
    o="$OUT/${name}_run$i"
    rm -rf "$o"; mkdir -p "$o"
    "$B" run --package "${PKG[$name]}" --data-root "$st" --trace --max-seconds 90 --frames 40 -o "$o" > "$o/run.log" 2>&1 || true
    s=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
    shas="$shas $s"
  done
  echo "$name:$shas"
done
# dooz 180s budget face x2 (reuses anchors store_dooz)
dst="$OUT/anchors/store_dooz"
shas=""
for i in 1 2; do
  o="$OUT/dooz180_run$i"
  rm -rf "$o"; mkdir -p "$o"
  "$B" run --package io.github.yamin8000.dooz --data-root "$dst" --trace --max-seconds 180 --frames 40 -o "$o" > "$o/run.log" 2>&1 || true
  s=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
  shas="$shas $s"
done
echo "dooz180:$shas"
