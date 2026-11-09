#!/usr/bin/env bash
# S206 — build & run the C9 phase-3 law test (link shape: full object set, main.o swapped for the test TU)
set -e
cd /home/z/my-project/miniandroid
INC="-Isrc -Isrc/webview -Isrc/apk -Isrc/dex -Isrc/runtime -Isrc/api -Isrc/graphics -Isrc/diagnostics -Isrc/resources -Isrc/renderer -Isrc/framework -Isrc/storage -Isrc/fonts -Ithird_party/portablegl -I/usr/include/freetype2 -Ithird_party/nlohmann_json/include"
g++ -std=c++17 -Wall -Wextra -g -O2 $INC -c tests/c9_phase3_laws_test.cpp -o build/c9_phase3_laws_test.o
# link: reuse the exact object list from the make log, swap main.o -> test.o
LINK_OBJS=$(sed -n 's/^g++ .* -o build\/miniandroid \(.*\) -lz .*/\1/p' /tmp/s206_make.log | head -1)
LINK_OBJS=${LINK_OBJS//build\/main.o/build\/c9_phase3_laws_test.o}
g++ -std=c++17 -g -O2 -rdynamic -o build/c9_phase3_laws_test $LINK_OBJS -lz -ljpeg -lstdc++ -lm -lpthread -lsqlite3 -lssl -lcrypto -lmpg123 -lsndfile -lwebp -lwebpdemux -lfreetype -lharfbuzz -lfribidi -lpng
echo "BUILD OK"
./build/c9_phase3_laws_test; echo "rc=$?"
