#!/usr/bin/env bash
# #612-C: solo-compile dalvik_engine.cpp with BOTH flag sets, measure peak RSS.
cd /home/z/my-project/miniandroid
INC="-Isrc -Isrc/apk -Isrc/dex -Isrc/runtime -Isrc/api -Isrc/graphics -Isrc/diagnostics -Isrc/resources -Isrc/renderer -Isrc/framework -Isrc/storage -Isrc/fonts -Isrc/gles -Isrc/jni -Isrc/audio -Isrc/webview -Ithird_party/portablegl -Ithird_party/nlohmann_json/include -I/usr/include/freetype2"
echo "=== CMake flags (Release: -O3 -DNDEBUG -O2 -g0) ==="
python3 /home/z/my-project/scripts/measure_run.py g++ -Wall -Wextra -O3 -DNDEBUG -O2 -std=c++17 -g0 $INC -c -o /tmp/d_cmake.o src/dex/dalvik_engine.cpp
echo "=== Makefile flags (-O2 -g -g0, MINIANDROID_HAVE_*) ==="
python3 /home/z/my-project/scripts/measure_run.py g++ -std=c++17 -Wall -Wextra -O2 -g -g0 -DMINIANDROID_HAVE_WEBP $INC -c -o /tmp/d_mk.o src/dex/dalvik_engine.cpp
ls -la /tmp/d_cmake.o /tmp/d_mk.o 2>/dev/null | awk '{print $5, $9}'
