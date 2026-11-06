#!/bin/bash
# S188: recompile the four theme-law-dependent TUs (no sed — pure bash substitution).
set -e
cd /home/z/my-project/miniandroid
INC="-Isrc -Isrc/apk -Isrc/resources -Isrc/renderer -Isrc/framework -Isrc/runtime -Isrc/dex -Isrc/api -Isrc/diagnostics -Isrc/storage -Isrc/jni -Isrc/fonts -Isrc/gles -Isrc/webview -Isrc/audio -Isrc/quickjs -Ithird_party/nlohmann_json/include -Ithird_party/audio -Ithird_party/quickjs -Ithird_party/portablegl -I/usr/include/freetype2 -I/usr/include/harfbuzz"
for f in src/framework/android_shadows.cpp src/runtime/execution_engine.cpp src/resources/layout_inflater.cpp src/webview/webview_engine.cpp; do
  base="${f#src/}"
  o="build/obj/${base//\//_}"
  o="${o%.cpp}.o"
  echo "compiling $f -> $o"
  g++ -std=c++17 -O1 -g0 -w $INC -c "$f" -o "$o"
done
echo TU_OK
