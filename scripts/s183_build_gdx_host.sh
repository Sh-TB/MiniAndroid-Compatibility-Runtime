#!/bin/bash
# s183_build_gdx_host.sh — build REAL host-native libgdx64.so, libgdx-box2d64.so, libgdx-freetype64.so
# from the open-source libGDX sources (tag gdx-parent-1.9.10), per the sqlite precedent:
# vendor the real library instead of fighting bionic-vs-glibc ABI.
set -e
SRC=/tmp/libgdx_src
OUT=/home/z/my-project/tools/native_host
JH="-I $SRC/gdx/jni/jni-headers -I $SRC/gdx/jni/jni-headers/linux"
mkdir -p "$OUT"

echo "== 1) gdx core =="
B=/tmp/gdxbuild; rm -rf $B; mkdir -p $B
cd "$SRC/gdx/jni"
INC="-I . -I gdx2d -I etc1 $JH"
for f in com.badlogic.gdx.graphics.g2d.Gdx2DPixmap.cpp com.badlogic.gdx.graphics.glutils.ETC1.cpp \
         com.badlogic.gdx.math.Matrix4.cpp com.badlogic.gdx.utils.BufferUtils.cpp; do
  g++ -c -O2 -m64 -fPIC $INC "$f" -o "$B/$(basename $f .cpp).o"
done
gcc -c -O2 -m64 -fPIC $INC memcpy_wrap.c -o $B/memcpy_wrap.o
gcc -c -O2 -m64 -fPIC $INC gdx2d/gdx2d.c -o $B/gdx2d_core.o
g++ -c -O2 -m64 -fPIC $INC gdx2d/jpgd_c.cpp -o $B/jpgd_c.o
g++ -c -O2 -m64 -fPIC $INC gdx2d/jpgd.cpp -o $B/jpgd.o
g++ -c -O2 -m64 -fPIC $INC etc1/etc1_utils.cpp -o $B/etc1_utils.o
g++ -shared -o "$OUT/libgdx64.so" $B/*.o
echo "   libgdx64.so: $(nm -D $OUT/libgdx64.so | grep -c ' Java_') JNI symbols"

echo "== 2) box2d =="
B=/tmp/b2dbuild; rm -rf $B; mkdir -p $B
cd "$SRC/extensions/gdx-box2d/gdx-box2d/jni"
INC="-I . -I Box2D $JH"
for f in $(find . -name "*.cpp" -not -path "./Box2D/*" | sort); do
  g++ -c -O2 -m64 -fPIC $INC "$f" -o "$B/$(basename $f .cpp).o"
done
for f in $(find Box2D -name "*.cpp" | sort); do
  g++ -c -O2 -m64 -fPIC $INC "$f" -o "$B/box2d_$(basename $f .cpp).o"
done
g++ -shared -o "$OUT/libgdx-box2d64.so" $B/*.o
echo "   libgdx-box2d64.so: $(nm -D $OUT/libgdx-box2d64.so | grep -c ' Java_') JNI symbols"

echo "== 3) freetype =="
B=/tmp/ftbuild; rm -rf $B; mkdir -p $B
cd "$SRC/extensions/gdx-freetype/jni"
INC="-I . -I freetype-2.9.1/include $JH"
g++ -c -O2 -m64 -fPIC $INC com.badlogic.gdx.graphics.g2d.freetype.FreeType.cpp -o $B/FreeType.o
gcc -c -O2 -m64 -fPIC $INC memcpy_wrap.c -o $B/memcpy_wrap.o
FTSRC=$(ls freetype-2.9.1/src/base/*.c | grep -E "ftsystem|ftinit|ftdebug|ftbase|ftbbox|ftglyph|ftbdf|ftbitmap|ftcid|ftfstype|ftgasp|ftgxval|ftmm|ftotval|ftpfr|ftstroke|ftsynth|fttype1|ftwinfnt")
for f in $FTSRC; do
  gcc -c -O2 -m64 -fPIC -DFT2_BUILD_LIBRARY $INC "$f" -o "$B/ft_$(basename $f .c).o"
done
# freetype is built as per-module AMALGAMATION files: autofit.c includes the
# autofit/*.c units, truetype.c includes tt*.c, etc. Compile only the amalgams.
for m in autofit/autofit cff/cff psaux/psaux pshinter/pshinter psnames/psnames raster/raster \
         smooth/smooth sfnt/sfnt truetype/truetype type1/type1 cid/type1cid \
         pcf/pcf pfr/pfr gzip/ftgzip lzw/ftlzw bdf/bdf cache/ftcache \
         gxvalid/ftgxval type42/type42 winfonts/winfnt; do
  f="freetype-2.9.1/src/$m.c"
  [ -f "$f" ] || continue
  gcc -c -O2 -m64 -fPIC -DFT2_BUILD_LIBRARY $INC "$f" -o "$B/ftmod_$(echo $m | tr '/' '_').o"
done
# bzip2 sources may be absent (bundled ft bzip2 needs libbz2) — optional module
g++ -shared -o "$OUT/libgdx-freetype64.so" $B/*.o 2>/dev/null || g++ -shared -o "$OUT/libgdx-freetype64.so" $B/*.o -lbz2
echo "   libgdx-freetype64.so: $(nm -D $OUT/libgdx-freetype64.so | grep -c ' Java_') JNI symbols"

echo "== DONE =="
ls -la "$OUT"
