#!/bin/bash
# S186h: recompile only dalvik_engine.cpp (F-NEW-188c law) and relink the
# engine from the existing 75 .o objects (sandbox lost cmake; .o set is the
# CMake build's output, .d files record the unit list).
set -e
cd /home/z/my-project/miniandroid
INC="-Isrc -Isrc/apk -Isrc/resources -Isrc/renderer -Isrc/framework -Isrc/runtime -Isrc/dex -Isrc/api -Isrc/diagnostics -Isrc/storage -Isrc/jni -Isrc/fonts -Isrc/gles -Isrc/webview -Isrc/audio -Isrc/quickjs -Ithird_party/nlohmann_json/include -Ithird_party/audio -Ithird_party/quickjs -Ithird_party/portablegl -I/usr/include/freetype2 -I/usr/include/harfbuzz"
g++ -std=c++17 -O0 -g0 $INC -c src/dex/dalvik_engine.cpp -o build/dex/dalvik_engine.o
# link: all existing objects (reuse), new dalvik_engine.o included
OBJS=$(find build -name "*.o" | sort)
g++ -std=c++17 -g -O1 -o build/miniandroid.new $OBJS \
  -lz -lpng -ljpeg -lsqlite3 -lssl -lcrypto -lfreetype -lharfbuzz -lfribidi \
  -lmpg123 -lsndfile -lwebp -lwebpdemux -lstdc++ -lm -lpthread -ldl
mv build/miniandroid.new build/miniandroid
echo "BUILD OK"
sha256sum build/miniandroid | cut -c1-16
