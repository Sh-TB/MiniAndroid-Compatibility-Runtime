#!/usr/bin/env bash
# s151_internet_fetch.sh — S151 wave: NEW trains from the internet (F-Droid open-source).
# Directive: «ادامه بده قطار های تعداد بالا سورس کد ها اینترنت و سورس» — raise the
# train count with NEW internet-sourced programs. Phase A probes the F-Droid API for
# suggestedVersionCode; Phase B downloads (cap 25MB) into upload/s151_internet_batch/.
# Every row records its source URL (the app's open-source distribution page).
set -u
cd /home/z/my-project
BATCH=upload/s151_internet_batch
MANI=run/s151/fdroid_manifest.tsv
mkdir -p "$BATCH" run/s151
: > "$MANI"

# NEW candidates only (none of the 94 in upload/fdroid_batch overlap)
CANDIDATES="
com.simplemobiletools.calculator
com.simplemobiletools.draw
org.isoron.uhabits
fr.neamar.kiss
nl.mpcjanssen.simpletask
com.better.alarm
me.jfenn.alarmio
org.y20k.transistor
org.y20k.trackbook
com.veniosg.dir
de.smasi.tickmate
com.zeapo.pwdstore
com.uberspot.a2048
com.github.muellerma.coffee
com.github.muellerma.stopwatch
org.billthefarmer.diary
org.billthefarmer.field
org.billthefarmer.viewer
org.secuso.privacyfriendlyweather
org.secuso.privacyfriendlynetmonitor
org.secuso.privacyfriendlyshoppinglist
org.secuso.privacyfriendlysudoku
org.secuso.privacyfriendlymemory
org.secuso.privacyfriendlyrockpaperscissors
org.secuso.privacyfriendlyboardgameclock
org.secuso.privacyfriendlycipher
org.secuso.privacyfriendlypaindiary
org.secuso.privacyfriendlyquiz
org.secuso.privacyfriendlywifianalyzer
org.secuso.privacyfriendlycornetracker
ca.rmen.android.poetassistant
com.sadellie.unitto
de.grobox.liberario
com.nutomic.syncthingandroid
com.menny.android.anysoftkeyboard
free.rm.skytube.oss
org.secuso.privacyfriendlyvaluesolver
org.secuso.privacyfriendlytaxes
org.secuso.privacyfriendlydrinkwater
org.secuso.privacyfriendlybudget
org.secuso.privacyfriendlysalut
org.secuso.privacyfriendlyexercisetracker
org.secuso.privacyfriendlyhealth
org.secuso.privacyfriendlycities
org.secuso.privacyfriendlyco2
org.secuso.privacyfriendlydocs
"

probe() {
  local pkg="$1"
  local api="https://f-droid.org/api/v1/packages/$pkg"
  local vc
  vc=$(timeout 25 curl -sL --max-time 20 "$api" 2>/dev/null | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin); print(d.get('suggestedVersionCode',''))
except Exception: print('')
" 2>/dev/null)
  if [ -n "$vc" ] && [ "$vc" != "None" ]; then
    echo -e "$pkg\t$vc" >> "$MANI"
    echo "PROBE OK $pkg vc=$vc"
  else
    echo "PROBE MISS $pkg"
  fi
}
export -f probe
export MANI

echo "$CANDIDATES" | tr -s ' \n' '\n\n' | grep -v '^$' | xargs -P 4 -I{} bash -c 'probe "$@"' _ {}

echo "=== probed: $(wc -l < "$MANI") OK of $(echo "$CANDIDATES" | grep -vc '^$') ==="

dl() {
  local pkg="$1" vc="$2"
  local out="$BATCH/${pkg}_${vc}.apk"
  [ -s "$out" ] && { echo "HAVE  $pkg"; return; }
  timeout 90 curl -sL --max-time 80 -o "$out" "https://f-droid.org/repo/${pkg}_${vc}.apk"
  local sz
  sz=$(stat -c%s "$out" 2>/dev/null || echo 0)
  if [ "$sz" -lt 100000 ]; then rm -f "$out"; echo "DL-FAIL $pkg ($sz B)"; return; fi
  if [ "$sz" -gt 26214400 ]; then rm -f "$out"; echo "DL-SKIP $pkg (${sz} B > 25MB cap)"; return; fi
  echo "DL OK $pkg ($sz B)"
}
export -f dl
export BATCH

tail -n +1 "$MANI" | while IFS=$'\t' read -r pkg vc; do dl "$pkg" "$vc"; done

echo "=== fetched: $(ls "$BATCH"/*.apk 2>/dev/null | wc -l) APKs ==="
