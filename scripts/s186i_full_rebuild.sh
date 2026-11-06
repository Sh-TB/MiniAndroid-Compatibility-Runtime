#!/bin/bash
# S186i: full engine rebuild from source after sandbox recycling.
# Unit list = src/**/*.cpp + quickjs C core + stb_vorbis (mirrors the CMake
# target; dalvik_engine.cpp at -O0 -g0 per S186h cc1plus-OOM law).
# Link line = S186h proven link line.
set -e
cd /home/z/my-project/miniandroid
mkdir -p build/obj
INC="-Isrc -Isrc/apk -Isrc/resources -Isrc/renderer -Isrc/framework -Isrc/runtime -Isrc/dex -Isrc/api -Isrc/diagnostics -Isrc/storage -Isrc/jni -Isrc/fonts -Isrc/gles -Isrc/webview -Isrc/audio -Isrc/quickjs -Ithird_party/nlohmann_json/include -Ithird_party/audio -Ithird_party/quickjs -Ithird_party/portablegl -I/usr/include/freetype2 -I/usr/include/harfbuzz"
CXX=g++
CFLAGS="-std=c++17 -O1 -g0 -w"
NPROC=$(nproc)

# 1) dalvik_engine.cpp at -O0 -g0 (76k lines; -O1+ exhausts cc1plus memory)
if [ ! -f build/obj/dalvik_engine.o ]; then
  echo "[1/3] dalvik_engine.cpp (-O0 -g0) ..."
  $CXX -std=c++17 -O0 -g0 -w $INC -c src/dex/dalvik_engine.cpp -o build/obj/dalvik_engine.o &
fi

# 2) all other C++ units
pids=()
for f in $(find src -name "*.cpp" ! -name dalvik_engine.cpp | sort); do
  o=build/obj/$(echo "$f" | sed 's|src/||; s|/|_|g; s|\.cpp$|.o|')
  if [ ! -f "$o" ]; then
    $CXX $CFLAGS $INC -c "$f" -o "$o" &
    pids+=($!)
    while [ "$(jobs -rp | wc -l)" -ge "$NPROC" ]; do sleep 0.3; done
  fi
done

# 3) quickjs + stb_vorbis (C)
for f in third_party/quickjs/cutils.c third_party/quickjs/libregexp.c \
         third_party/quickjs/libunicode.c third_party/quickjs/libbf.c \
         third_party/quickjs/quickjs.c third_party/audio/stb_vorbis.c; do
  o=build/obj/$(echo "$f" | sed 's|third_party/||; s|/|_|g; s|\.c$|.o|')
  if [ ! -f "$o" ]; then
    gcc -O1 -g0 -w -Ithird_party/quickjs -c "$f" -o "$o" &
    while [ "$(jobs -rp | wc -l)" -ge "$NPROC" ]; do sleep 0.3; done
  fi
done

wait
echo "[2/3] compile done: $(find build/obj -name '*.o' | wc -l) objects"

# 4) link
OBJS=$(find build/obj -name "*.o" | sort)
$CXX -std=c++17 -O1 -o build/miniandroid $OBJS \
  -lz -lpng -ljpeg -lsqlite3 -lssl -lcrypto -lfreetype -lharfbuzz -lfribidi \
  -lmpg123 -lsndfile -lwebp -lwebpdemux -lstdc++ -lm -lpthread -ldl
echo "[3/3] BUILD OK"
sha256sum build/miniandroid | cut -c1-16
