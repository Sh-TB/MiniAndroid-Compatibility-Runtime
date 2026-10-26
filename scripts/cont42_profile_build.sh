#!/bin/bash
# cont42_profile_build.sh — TRAIN 2 (CONT-42): gprof profile build.
# Builds a -pg instrumented binary into build_prof/ WITHOUT touching the
# canonical build/ tree. Flags replicate the canonical compile lines exactly
# (extracted from the build log) plus -pg.
set -e
cd /home/z/my-project/miniandroid
PGFLAGS="-std=c++17 -Wall -Wextra -g -O2 -pg -MMD -MP -DMINIANDROID_HAVE_WEBP"
INC="-Isrc -Isrc/webview -Isrc/apk -Isrc/dex -Isrc/runtime -Isrc/api -Isrc/graphics -Isrc/diagnostics -Isrc/resources -Isrc/renderer -Isrc/framework -Isrc/storage -Isrc/fonts -Ithird_party/portablegl -I/usr/include/freetype2 -Ithird_party/nlohmann_json/include"
make -j1 BUILDDIR=build_prof CXXFLAGS="$PGFLAGS" INCLUDES="$INC" LIBS="-lz -ljpeg -lstdc++ -lm -lpthread -lsqlite3 -lssl -lcrypto -lmpg123 -lsndfile -lwebp -lwebpdemux" FONTS_LIBS="-lfreetype -lharfbuzz -lfribidi -lpng" miniandroid
echo "PROFILE BUILD DONE: build_prof/miniandroid"
