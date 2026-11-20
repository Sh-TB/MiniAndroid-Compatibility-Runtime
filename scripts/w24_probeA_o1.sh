#!/usr/bin/env bash
# w24_probeA_o1.sh — EXP-A probe: bridge domains at -O1 -g0 vs -O2 -g0,
# ALTERNATING ORDER (ABBA) x2 TUs — the BUG-5 page-cache-order lesson.
# Probe decides candidacy; the full-build A/B is the decisive measurement.
set -x
cd /home/z/my-project/miniandroid
INC="-Isrc -Isrc/webview -Isrc/apk -Isrc/dex -Isrc/runtime -Isrc/api -Isrc/graphics -Isrc/diagnostics -Isrc/resources -Isrc/renderer -Isrc/framework -Isrc/storage -Isrc/fonts -Isrc/gles -Isrc/jni -Isrc/audio -Ithird_party/portablegl -I/usr/include/freetype2 -Ithird_party/nlohmann_json/include -Ibuild/generated"

run() { # $1=label $2=src $3...=extra flags
  local label="$1"; local src="$2"; shift 2
  { time g++ -std=c++17 -w $INC -c -o /tmp/w24a_$label.o "$src" "$@" ; } 2> /tmp/w24a_$label.txt
  echo "PROBE $label: $(grep -a real /tmp/w24a_$label.txt)"
}

# ABBA x2 domains (jdk: cheapest of the 5, ui_graphics: the heaviest)
for rep in 1 2; do
  run A${rep}_jdk_o2  src/dex/dalvik_bridge_domain_jdk.cpp        -O2 -g0 -DMINIANDROID_HAVE_WEBP
  run A${rep}_jdk_o1  src/dex/dalvik_bridge_domain_jdk.cpp        -O1 -g0 -DMINIANDROID_HAVE_WEBP
  run A${rep}_uig_o1  src/dex/dalvik_bridge_domain_ui_graphics.cpp -O1 -g0 -DMINIANDROID_HAVE_WEBP
  run A${rep}_uig_o2  src/dex/dalvik_bridge_domain_ui_graphics.cpp -O2 -g0 -DMINIANDROID_HAVE_WEBP
done
echo PROBEA_DONE
