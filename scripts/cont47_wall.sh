#!/usr/bin/env bash
# cont47_wall.sh — regression wall for measure-law changes (T7).
# Runs the pinned apps on the CURRENT binary and prints PNG sha16 pins.
# Usage: cont47_wall.sh <outdir>
set -u
OUT="$1"; shift || true
mkdir -p "$OUT"
declare -A APPS=(
  [dooz]="upload/canonical_apks/io.github.yamin8000.dooz_23.apk|851cc1761a1dfcdf|121"
  [gmdice]="upload/canonical_apks/de.duenndns.gmdice_8.apk|3891679dff449331|121"
  [opencalc]="upload/opencalculator_53.apk|63020bc7334048fe|121"
)
for name in dooz gmdice opencalc; do
  IFS='|' read -r apk pin frames <<< "${APPS[$name]}"
  o="$OUT/$name"
  timeout 240 miniandroid/build/miniandroid run "$apk" \
    --width 1080 --height 1920 --frames "$frames" --max-seconds 150 \
    -o "$o" >/dev/null 2>&1
  rc=$?
  sha=$(sha256sum "$o/screenshot.png" 2>/dev/null | cut -c1-16)
  verdict="DRIFT"
  [ "$sha" = "$pin" ] && verdict="MATCH"
  [ -z "$sha" ] && verdict="NO-SHOT(rc=$rc)"
  echo "WALL $name rc=$rc sha16=$sha pin=$pin $verdict"
done
