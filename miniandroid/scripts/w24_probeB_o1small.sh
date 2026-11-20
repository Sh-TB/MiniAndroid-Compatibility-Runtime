#!/usr/bin/env bash
# w24_probeB_o1small.sh — EXP-A tier-2 probe: small tail TUs at -O1 vs -O2
# (FASTPROFILE flags -g1), ALTERNATING ORDER x2 reps. Sizes the CPU saving
# available in the 62-TU small tail (150 CPU-s today) before any full build.
set -x
cd /home/z/my-project/miniandroid
INC="-Isrc -Isrc/webview -Isrc/apk -Isrc/dex -Isrc/runtime -Isrc/api -Isrc/graphics -Isrc/diagnostics -Isrc/resources -Isrc/renderer -Isrc/framework -Isrc/storage -Isrc/fonts -Isrc/gles -Isrc/jni -Isrc/audio -Ithird_party/portablegl -I/usr/include/freetype2 -Ithird_party/nlohmann_json/include -Ibuild/generated"
BASE="-std=c++17 -w -O2 -g1 -DMINIANDROID_HAVE_WEBP $INC"

run() { # $1=label $2=src $3=-O level
  local label="$1"; local src="$2"; local o="$3"
  { time g++ $BASE $o -c -o /tmp/w24b_$label.o "$src" ; } 2> /tmp/w24b_$label.txt
  echo "PROBE $label: $(grep -a real /tmp/w24b_$label.txt)"
}

for rep in 1 2; do
  run P${rep}_resparse_o2 src/resources/resource_parser.cpp -O2
  run P${rep}_resparse_o1 src/resources/resource_parser.cpp -O1
  run P${rep}_sqlsh_o1    src/storage/sqlite_shadow.cpp     -O1
  run P${rep}_sqlsh_o2    src/storage/sqlite_shadow.cpp     -O2
  run P${rep}_dexparse_o1 src/dex/dex_parser.cpp           -O1
  run P${rep}_dexparse_o2 src/dex/dex_parser.cpp           -O2
done
echo PROBEB_DONE
