#!/bin/bash
# s202_build_gdx_freetype_host.sh — rebuild tools/native_host/libgdx-freetype64.so
# the S202 way (Coder-3 finding): the s183 2.9.1 in-tree build segfaults in
# FT_Lookup_Renderer (ftmodule.h amalgamation gap on new gcc, no renderer
# registered). The sqlite law says BRING THE REAL LIBRARY — so build the gdx
# JNI WRAPPER ONLY and link it against the HOST freetype 2.13.3 (-lfreetype).
# Every Java_* JNI symbol the DEX resolves stays identical (jniigen layout).
set -e
SRC=/tmp/libgdx_src
OUT=/home/z/my-project/tools/native_host

if [ ! -d "$SRC/extensions/gdx-freetype/jni" ]; then
  echo "libGDX sources missing at $SRC" >&2; exit 1
fi

JH="-I $SRC/gdx/jni/jni-headers -I $SRC/gdx/jni/jni-headers/linux"
mkdir -p "$OUT"
B=/tmp/s202ftbuild; rm -rf $B; mkdir -p $B
cd "$SRC/extensions/gdx-freetype/jni"
INC="-I . $JH $(pkg-config --cflags freetype2)"
echo "== 1) gdx FreeType JNI wrapper against HOST freetype =="
g++ -c -O2 -m64 -fPIC $INC com.badlogic.gdx.graphics.g2d.freetype.FreeType.cpp \
    -o $B/FreeType.o
echo "== 2) memcpy_wrap =="
gcc -c -O2 -m64 -fPIC $INC memcpy_wrap.c -o $B/memcpy_wrap.o
echo "== 3) link against host freetype =="
g++ -shared -o "$OUT/libgdx-freetype64.so" $B/*.o -lfreetype
echo "== DONE =="
ls -la "$OUT/libgdx-freetype64.so"
echo "JNI symbols: $(nm -D $OUT/libgdx-freetype64.so | grep -c ' Java_')"
