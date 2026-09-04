#!/usr/bin/env bash
# ============================================================================
# build_windows.sh — reproducible Windows x64 build of the MiniAndroid runtime.
#
# Produces MiniAndroid.exe: PE32+ x86-64 console binary, statically linked
# against all third-party codecs (zlib/libpng/libjpeg/freetype/harfbuzz/
# fribidi/webp). Runtime DLL deps: UCRT + KERNEL32 only (present on every
# Windows 10/11 install).
#
# Toolchain: llvm-mingw (https://github.com/mstorsjo/llvm-mingw) — clang-based
#   mingw-w64 cross toolchain, Linux-hosted binaries from GitHub releases.
#   Set MINGW_DIR to an existing llvm-mingw root to skip the download.
#
# Usage:  MINIANDROID_WIN_OUT=<dir> ./scripts/build_windows.sh
# ============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RA="$REPO_ROOT/miniandroid"
WORK="${MINIANDROID_WIN_WORK:-$RA/build-win/work}"
OUT_DIR="${MINIANDROID_WIN_OUT:-$RA/build-win}"
DEP=$WORK/win_deps
SRC=$WORK/win_src
mkdir -p "$DEP/include" "$DEP/lib" "$SRC"

# ---- pinned upstream dependency versions (all official repos) --------------
ZLIB_VER=1.3.1            ZLIB_URL="https://github.com/madler/zlib/archive/refs/tags/v1.3.1.tar.gz"
LIBPNG_VER=1.6.44         LIBPNG_URL="https://github.com/pnggroup/libpng/archive/refs/tags/v1.6.44.tar.gz"
FT_VER=2.13.3             FT_URL="https://github.com/freetype/freetype/archive/refs/tags/VER-2-13-3.tar.gz"
FT_DIR=freetype-VER-2-13-3
HB_VER=8.5.0              HB_URL="https://github.com/harfbuzz/harfbuzz/archive/refs/tags/8.5.0.tar.gz"
FRIBIDI_VER=1.0.16        FRIBIDI_URL="https://github.com/fribidi/fribidi/archive/refs/tags/v1.0.16.tar.gz"
WEBP_VER=1.4.0            WEBP_URL="https://github.com/webmproject/libwebp/archive/refs/tags/v1.4.0.tar.gz"
IJG_URL="https://www.ijg.org/files/jpegsr9f.zip"   # IJG jpeg-9f reference

# ---- toolchain -------------------------------------------------------------
MINGW_DIR="${MINGW_DIR:-}"
if [ -z "$MINGW_DIR" ]; then
  MINGW_DIR="$WORK/llvm-mingw"
  if [ ! -x "$MINGW_DIR/bin/x86_64-w64-mingw32-g++" ]; then
    echo "[windows-build] downloading llvm-mingw toolchain (linux-hosted)..."
    curl -sL --max-time 600 -o "$WORK/llvm-mingw.tar.xz" \
      "https://github.com/mstorsjo/llvm-mingw/releases/download/20260826/llvm-mingw-20260826-ucrt-ubuntu-22.04-x86_64.tar.xz"
    tar xf "$WORK/llvm-mingw.tar.xz" -C "$WORK"
    mv "$WORK"/llvm-mingw-20260826-ucrt-ubuntu-22.04-x86_64 "$MINGW_DIR"
  fi
fi
export PATH="$MINGW_DIR/bin:$PATH"
CC=x86_64-w64-mingw32-gcc
CXX=x86_64-w64-mingw32-g++
AR=x86_64-w64-mingw32-ar
CF="-O2 -D_FILE_OFFSET_BITS=64 -DNDEBUG -fno-strict-aliasing"

fetch() { # fetch <url> <file>
  [ -s "$SRC/$2" ] || { echo "[windows-build] GET $1"; curl -sL --max-time 400 -o "$SRC/$2" "$1"; }
  [ -s "$SRC/$2" ]
}

# ---- zlib ------------------------------------------------------------------
if [ ! -s "$DEP/lib/libz.a" ]; then
  fetch "$ZLIB_URL" zlib.tgz && tar xf "$SRC/zlib.tgz" -C "$SRC"
  ( cd "$SRC"/zlib-1.3.1 && $CC $CF -I. -c adler32.c crc32.c deflate.c gzclose.c gzlib.c gzread.c gzwrite.c infback.c inffast.c inflate.c inftrees.c trees.c uncompr.c zutil.c compress.c && $AR rcs "$DEP/lib/libz.a" *.o && cp -f zlib.h zconf.h "$DEP/include/" && rm -f *.o )
fi

# ---- libpng ----------------------------------------------------------------
if [ ! -s "$DEP/lib/libpng16.a" ]; then
  fetch "$LIBPNG_URL" libpng.tgz && tar xf "$SRC/libpng.tgz" -C "$SRC"
  ( cd "$SRC"/libpng-1.6.44 && cp -f scripts/pnglibconf.h.prebuilt pnglibconf.h && \
    P="png.c pngerror.c pngget.c pngmem.c pngpread.c pngread.c pngrio.c pngrtran.c pngrutil.c pngset.c pngtrans.c pngwio.c pngwrite.c pngwtran.c pngwutil.c" && \
    $CC $CF -DPNG_ARM_NEON_OPT=0 -DPNG_INTEL_SSE_OPT=0 -DPNG_MIPS_MSA_OPT=0 -DPNG_POWERPC_VSX_OPT=0 -I. -I"$SRC/zlib-1.3.1" -c $P && \
    $AR rcs "$DEP/lib/libpng16.a" *.o && cp -f png.h pngconf.h pnglibconf.h "$DEP/include/" && rm -f *.o )
fi

# ---- libjpeg (IJG 9f reference, same API Android's libjpeg-turbo exposes) --
if [ ! -s "$DEP/lib/libjpeg.a" ]; then
  fetch "$IJG_URL" jpeg.zip && ( cd "$SRC" && unzip -qo jpeg.zip )
  ( cd "$SRC/jpeg-9f" && cp -f jconfig.txt jconfig.h && \
    JL=$(ls j*.c | grep -vE "jmemansi|jmemname|jmemdos|jmemmac|cjpeg|djpeg|jpegtran|ckconfig|example") && \
    $CC $CF -I. -c $JL && $AR rcs "$DEP/lib/libjpeg.a" *.o && \
    cp -f jpeglib.h jerror.h jmorecfg.h jconfig.h "$DEP/include/" && rm -f *.o )
fi

# ---- freetype (docs/INSTALL.ANY file list; config/ftmodule.h ships in tree) -
if [ ! -s "$DEP/lib/libfreetype.a" ]; then
  fetch "$FT_URL" ft.tgz && tar xf "$SRC/ft.tgz" -C "$SRC"
  ( cd "$SRC/$FT_DIR" && \
    FTL="src/autofit/autofit.c src/base/ftbase.c src/base/ftbbox.c src/base/ftbdf.c src/base/ftbitmap.c src/base/ftcid.c src/base/ftfstype.c src/base/ftgasp.c src/base/ftglyph.c src/base/ftgxval.c src/base/ftinit.c src/base/ftmm.c src/base/ftotval.c src/base/ftpatent.c src/base/ftpfr.c src/base/ftstroke.c src/base/ftsynth.c src/base/ftsystem.c src/base/fttype1.c src/base/ftwinfnt.c src/bdf/bdf.c src/cache/ftcache.c src/cff/cff.c src/cid/type1cid.c src/gzip/ftgzip.c src/lzw/ftlzw.c src/pcf/pcf.c src/pfr/pfr.c src/psaux/psaux.c src/pshinter/pshinter.c src/psnames/psnames.c src/raster/raster.c src/sfnt/sfnt.c src/smooth/smooth.c src/svg/svg.c src/sdf/sdf.c src/truetype/truetype.c src/type1/type1.c src/type42/type42.c" && \
    $CC $CF -std=c99 -DFT2_BUILD_LIBRARY -Iinclude -c $FTL && $AR rcs "$DEP/lib/libfreetype.a" *.o && \
    cp -rf include/ft2build.h include/freetype "$DEP/include/" && rm -f *.o )
fi

# ---- harfbuzz (upstream amalgamation src/harfbuzz.cc + hb-ft.cc) ------------
if [ ! -s "$DEP/lib/libharfbuzz.a" ]; then
  fetch "$HB_URL" hb.tgz && tar xf "$SRC/hb.tgz" -C "$SRC"
  ( cd "$SRC"/harfbuzz-8.5.0 && \
    $CXX -std=c++17 -O2 -DNDEBUG -DHAVE_FREETYPE -DHB_NO_PRAGMA_GCC_DIAGNOSTIC_ERROR -Isrc -I"$DEP/include" -c src/harfbuzz.cc src/hb-ft.cc && \
    $AR rcs "$DEP/lib/libharfbuzz.a" harfbuzz.o hb-ft.o && \
    mkdir -p "$DEP/include/harfbuzz" && cp -f src/hb*.h "$DEP/include/harfbuzz/" && cp -f src/hb.h "$DEP/include/hb.h" && rm -f *.o )
fi

# ---- fribidi (bidi tables generated from official Unicode UCD 16.0.0) ------
if [ ! -s "$DEP/lib/libfribidi.a" ]; then
  fetch "$FRIBIDI_URL" fribidi.tgz && tar xf "$SRC/fribidi.tgz" -C "$SRC"
  U="$SRC/fribidi-1.0.16/gen.tab/unidata"; mkdir -p "$U"
  for f in UnicodeData.txt ArabicShaping.txt BidiMirroring.txt BidiBrackets.txt; do
    fetch "https://www.unicode.org/Public/16.0.0/ucd/$f" "ucd_$f" && cp "$SRC/ucd_$f" "$U/$f"
  done
  ( cd "$SRC/fribidi-1.0.16" && \
    cat > fribidi-config.h <<'EOC'
#define HAVE_STDLIB_H 1
#define HAVE_STRING_H 1
#define HAVE_SYS_TYPES_H 1
#define HAVE_MEMSET 1
#define HAVE_STRDUP 1
#define HAVE_STRINGIZE 1
#define FRIBIDI_ENTRY
#define FRIBIDI_LIB_STATIC 1
#define SIZEOF_INT 4
#define SIZEOF_LONG 8
#define SIZEOF_VOID_P 8
EOC
    cat > lib/fribidi-unicode-version.h <<'EOV'
/* fribidi-unicode-version.h
 * generated by gen-unicode-version (GNU FriBidi 1.0.16)
 * from the file ReadMe.txt */

#define FRIBIDI_UNICODE_VERSION "16.0.0"
#define FRIBIDI_UNICODE_MAJOR_VERSION 16
#define FRIBIDI_UNICODE_MINOR_VERSION 0
#define FRIBIDI_UNICODE_MICRO_VERSION 0

/* End of generated fribidi-unicode-version.h */
EOV
    ( cd gen.tab && cp -f ../lib/fribidi-unicode-version.h . 2>/dev/null || true; \
      for g in gen-bidi-type-tab gen-joining-type-tab gen-arabic-shaping-tab gen-mirroring-tab gen-brackets-tab gen-brackets-type-tab; do \
        gcc -O2 -Wno-implicit-function-declaration -Wno-builtin-declaration-mismatch -Wno-int-conversion -I. -I.. -I../lib -DFRIBIDI_NAME='"fribidi"' -DFRIBIDI_VERSION='"1.0.16"' -o $g $g.c packtab.c; done; \
      ./gen-bidi-type-tab 7 unidata/UnicodeData.txt fribidi-unicode-version.h > ../lib/bidi-type.tab.i; \
      ./gen-joining-type-tab 4 unidata/UnicodeData.txt unidata/ArabicShaping.txt fribidi-unicode-version.h > ../lib/joining-type.tab.i; \
      ./gen-arabic-shaping-tab 4 unidata/UnicodeData.txt fribidi-unicode-version.h > ../lib/arabic-shaping.tab.i; \
      ./gen-mirroring-tab 4 unidata/BidiMirroring.txt fribidi-unicode-version.h > ../lib/mirroring.tab.i; \
      ./gen-brackets-tab 4 unidata/BidiBrackets.txt unidata/UnicodeData.txt fribidi-unicode-version.h > ../lib/brackets.tab.i; \
      ./gen-brackets-type-tab 4 unidata/BidiBrackets.txt fribidi-unicode-version.h > ../lib/brackets-type.tab.i ) && \
    FL=$(ls lib/*.c | grep -v fribidi-deprecated) && \
    $CC $CF -DFRIBIDI_NAME='"fribidi"' -DFRIBIDI_VERSION='"1.0.16"' -DFRIBIDI_INTERFACE_VERSION_STRING='"1.0.16"' -I. -Ilib -c $FL && \
    $AR rcs "$DEP/lib/libfribidi.a" *.o && mkdir -p "$DEP/include/fribidi" && \
    cp -f lib/fribidi.h lib/fribidi-*.h "$DEP/include/fribidi/" && rm -f *.o )
fi

# ---- libwebp ---------------------------------------------------------------
if [ ! -s "$DEP/lib/libwebp.a" ]; then
  fetch "$WEBP_URL" webp.tgz && tar xf "$SRC/webp.tgz" -C "$SRC"
  ( cd "$SRC/libwebp-1.4.0" && \
    WL=$(find src/dec src/demux src/dsp src/enc src/utils -name "*.c") && \
    $CC $CF -I. -c $WL && $AR rcs "$DEP/lib/libwebp.a" *.o && \
    cp -rf src/webp "$DEP/include/" && rm -f *.o )
fi

# ---- MiniAndroid runtime -> MiniAndroid.exe --------------------------------
cd "$RA"
B="$OUT_DIR/obj"; mkdir -p "$B"
CXXFLAGS="-std=c++17 -O2 -DNDEBUG -DMINIANDROID_HAVE_WEBP=1 -DMINIANDROID_HAVE_LOTTIE=0 -DWIN32_LEAN_AND_MEAN -DNOMINMAX"
INC="-Isrc -Isrc/apk -Isrc/dex -Isrc/runtime -Isrc/api -Isrc/graphics -Isrc/diagnostics -Isrc/resources -Isrc/renderer -Isrc/framework -Isrc/storage -Ithird_party/nlohmann_json/include -I$DEP/include"
SRCS="src/apk/apk_parser.cpp src/apk/manifest_reader.cpp
src/dex/dex_parser.cpp src/dex/class_resolver.cpp src/dex/dex_interpreter_batch.cpp src/dex/dalvik_engine.cpp src/dex/trace_exporter.cpp
src/runtime/execution_engine.cpp src/runtime/application_runtime.cpp
src/diagnostics/trace_engine.cpp
src/resources/res_config.cpp src/resources/resource_parser.cpp src/resources/arsc_parser.cpp src/resources/axml_parser.cpp src/resources/layout_inflater.cpp src/resources/resource_runtime.cpp
src/renderer/software_renderer.cpp
src/framework/android_shadows.cpp src/framework/shadow_registry.cpp src/framework/dialog_shadow.cpp src/framework/canvas_shadow.cpp
src/api/application_context.cpp src/api/shared_prefs.cpp"
SRCS="$SRCS $(ls src/storage/*.cpp)"
SRCS="$SRCS src/main.cpp"

for s in $SRCS; do
  o="$B/$(echo "$s" | tr '/' '_' | sed 's/\.cpp$/.o/')"
  [ -f "$o" ] || $CXX $CXXFLAGS $INC -c "$s" -o "$o"
done

$CXX $CXXFLAGS -o "$OUT_DIR/MiniAndroid.exe" \
  $(ls "$B"/*.o | grep -v "src_main") "$B/src_main.o" \
  -L"$DEP/lib" -static -lz -ljpeg -lwebp -lpng16 -lfreetype -lharfbuzz -lfribidi -static -lstdc++ -lm -lpthread

echo "[windows-build] DONE: $OUT_DIR/MiniAndroid.exe"
ls -la "$OUT_DIR/MiniAndroid.exe"
