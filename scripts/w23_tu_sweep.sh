#!/usr/bin/env bash
# w23_tu_sweep.sh — sequential per-TU timing sweep at -g1 (FASTPROFILE flags)
# to rank the heaviest non-engine-family TUs, then probe wave-7 inline-budget
# params (--param inline-unit-growth=15 --param large-function-growth=120)
# on the top candidates.
set -x
cd /home/z/my-project/miniandroid
INC="-Isrc -Isrc/webview -Isrc/apk -Isrc/dex -Isrc/runtime -Isrc/api -Isrc/graphics -Isrc/diagnostics -Isrc/resources -Isrc/renderer -Isrc/framework -Isrc/storage -Isrc/fonts -Isrc/gles -Isrc/jni -Isrc/audio -Ithird_party/portablegl -I/usr/include/freetype2 -Ithird_party/nlohmann_json/include -Ibuild/generated"
BASE="-std=c++17 -w -O2 -g1 -DMINIANDROID_HAVE_WEBP"
PARAMS="--param inline-unit-growth=15 --param large-function-growth=120"

t() { # $1=label $2=src $3...=extra flags
  local label="$1"; local src="$2"; shift 2
  { time g++ $BASE "$@" $INC -c -o /tmp/w23sweep_$label.o "$src" ; } 2> /tmp/w23sweep_$label.txt
  echo "SWEEP $label: $(grep -a real /tmp/w23sweep_$label.txt)"
}

# ranking sweep (all -g1, production-equivalent flags)
t execeng   src/runtime/execution_engine.cpp
t apprt     src/framework/application_runtime.cpp
t softrend  src/renderer/software_renderer.cpp
t vecdec    src/renderer/vector_decode.cpp
t sqlshadow src/storage/sqlite_shadow.cpp
t apkparse  src/apk/apk_parser.cpp
t dexparse  src/dex/dex_parser.cpp
t resdir    src/resources/resource_directory.cpp
t resparse  src/resources/resource_parser.cpp
t canvas    src/graphics/canvas.cpp
echo PARAM_PROBES
# param probes on the two heaviest (filled after looking at sweep output)
t execeng_p src/runtime/execution_engine.cpp $PARAMS
t apprt_p   src/framework/application_runtime.cpp $PARAMS
echo SWEEP_DONE
