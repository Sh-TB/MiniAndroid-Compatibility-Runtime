#!/usr/bin/env bash
# w23_flagprobe.sh — probe compile-time flags on the heaviest TU
# (execution_engine.cpp, 38 s in the canonical profile).
# Tiers: current production (-g) vs engine-family contract (-g0) vs -g1
# vs LLVM-style pass pruning (-fno-tree-pre -fno-code-hoisting), stacked.
set -x
cd /home/z/my-project/miniandroid
INC="-Isrc -Isrc/webview -Isrc/apk -Isrc/dex -Isrc/runtime -Isrc/api -Isrc/graphics -Isrc/diagnostics -Isrc/resources -Isrc/renderer -Isrc/framework -Isrc/storage -Isrc/fonts -Isrc/gles -Isrc/jni -Isrc/audio -Ithird_party/portablegl -I/usr/include/freetype2 -Ithird_party/nlohmann_json/include -Ibuild/generated"
probe() { # $1=label $2...=extra flags
  local label="$1"; shift
  { time g++ -std=c++17 -w -O2 -DMINIANDROID_HAVE_WEBP $INC \
    -c -o /tmp/w23probe_$label.o src/runtime/execution_engine.cpp "$@" ; } 2> /tmp/w23probe_$label.txt
  echo "PROBE $label: $(grep -a real /tmp/w23probe_$label.txt) $(grep -a 'Maximum resident' /tmp/w23probe_$label.txt)"
}
probe g0 -g0
probe g1 -g1
probe g1_pre -g1 -fno-tree-pre -fno-code-hoisting
probe g0_pre -g0 -fno-tree-pre -fno-code-hoisting
probe g_pre -g -fno-tree-pre -fno-code-hoisting
echo PROBES_DONE
