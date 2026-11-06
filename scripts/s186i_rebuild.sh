#!/bin/bash
# S186i full rebuild, STAGED-FOREGROUND mode (sandbox reaps detached processes;
# S186c lesson: chunked foreground is the only reliable mode here).
# Usage: s186i_rebuild.sh <stage>   stage in {engine, cpp:N:M, c, link}
set -e
cd /home/z/my-project/miniandroid
mkdir -p build/obj
INC="-Isrc -Isrc/apk -Isrc/resources -Isrc/renderer -Isrc/framework -Isrc/runtime -Isrc/dex -Isrc/api -Isrc/diagnostics -Isrc/storage -Isrc/jni -Isrc/fonts -Isrc/gles -Isrc/webview -Isrc/audio -Isrc/quickjs -Ithird_party/nlohmann_json/include -Ithird_party/audio -Ithird_party/quickjs -Ithird_party/portablegl -I/usr/include/freetype2 -I/usr/include/harfbuzz"

case "$1" in
engine)
  g++ -std=c++17 -O0 -g0 -w $INC -c src/dex/dalvik_engine.cpp -o build/obj/dalvik_engine.o
  echo ENGINE_OK $(stat -c%s build/obj/dalvik_engine.o)
  ;;
cpp)
  N=$2; M=$3
  LIST=$(find src -name "*.cpp" ! -name dalvik_engine.cpp | sort | sed -n "$((N+1)),$((N+M))p")
  echo "$LIST" | wc -l
  for f in $LIST; do
    o=build/obj/$(echo "$f" | sed 's|src/||; s|/|_|g; s|\.cpp$|.o|')
    if [ ! -f "$o" ]; then
      g++ -std=c++17 -O1 -g0 -w $INC -c "$f" -o "$o" &
    else
      echo "cached $o"
    fi
    while [ "$(jobs -rp | wc -l)" -ge 2 ]; do sleep 0.3; done
  done
  wait
  echo CPP_CHUNK_OK
  ;;
c)
  for f in third_party/quickjs/cutils.c third_party/quickjs/libregexp.c \
           third_party/quickjs/libunicode.c third_party/quickjs/libbf.c \
           third_party/quickjs/quickjs.c third_party/audio/stb_vorbis.c; do
    o=build/obj/$(echo "$f" | sed 's|third_party/||; s|/|_|g; s|\.c$|.o|')
    if [ ! -f "$o" ]; then gcc -O1 -g0 -w -Ithird_party/quickjs -c "$f" -o "$o"; fi
  done
  echo C_OK
  ;;
link)
  OBJS=$(find build/obj -name "*.o" | sort)
  echo "linking $(echo "$OBJS" | wc -l) objects"
  g++ -std=c++17 -O1 -o build/miniandroid $OBJS \
    -lz -lpng -ljpeg -lsqlite3 -lssl -lcrypto -lfreetype -lharfbuzz -lfribidi \
    -lmpg123 -lsndfile -lwebp -lwebpdemux -lstdc++ -lm -lpthread -ldl
  echo BUILD_OK
  sha256sum build/miniandroid | cut -c1-16
  ;;
*)
  echo "usage: $0 engine|cpp N M|c|link"; exit 1;;
esac
