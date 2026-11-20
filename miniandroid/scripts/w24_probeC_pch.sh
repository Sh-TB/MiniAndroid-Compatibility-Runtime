#!/usr/bin/env bash
# w24_probeC_pch.sh — EXP-C probe: common-prefix PCH for the standard-flag TUs.
# NEW hypothesis (distinct from the rejected issue-612 engine-TU PCH):
# the ~100 CPU-s of duplicated frontend work (json.hpp in ~40 TUs, resource
# header cluster in ~25-34 TUs) is concentrated in SHARED headers — a PCH
# prefix can amortize it. Alternating order x2 reps (BUG-5 lesson).
set -x
cd /home/z/my-project/miniandroid
INC="-Isrc -Isrc/webview -Isrc/apk -Isrc/dex -Isrc/runtime -Isrc/api -Isrc/graphics -Isrc/diagnostics -Isrc/resources -Isrc/renderer -Isrc/framework -Isrc/storage -Isrc/fonts -Isrc/gles -Isrc/jni -Isrc/audio -Ithird_party/portablegl -I/usr/include/freetype2 -Ithird_party/nlohmann_json/include -Ibuild/generated"
FLAGS="-std=c++17 -w -O2 -g1 -DMINIANDROID_HAVE_WEBP"
PCHSRC=/tmp/w24_pch_prefix.h
PCHFILE=/tmp/w24_pch_prefix.h.gch

# prefix = headers with >=25 consumers (probe set; may include headers some
# TUs do not include — that is safe for declarations, risky only for macros,
# which the probe will surface)
cat > $PCHSRC <<'EOF'
#include <vector>
#include <string>
#include <map>
#include <unordered_map>
#include <memory>
#include <functional>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <cmath>
#include <algorithm>
#include <fstream>
#include <sstream>
#include <iostream>
#include <nlohmann/json.hpp>
#include "resources/res_config.h"
#include "resources/res_id.h"
#include "resources/arsc_parser.h"
#include "framework/adapter_scrap_bin.h"
#include "renderer/software_renderer.h"
#include "framework/android_shadows.h"
#include "resources/attribute_set_store.h"
EOF

rm -f $PCHFILE
{ time g++ $FLAGS $INC -x c++-header -c -o $PCHFILE $PCHSRC ; } 2> /tmp/w24pch_build.txt
echo "PCH BUILD: $(grep -a real /tmp/w24pch_build.txt) size=$(stat -c%s $PCHFILE 2>/dev/null)"

INC2="$INC -I. "
run() { # $1=label $2=src $3=extra(-include or empty)
  local label="$1"; local src="$2"; local inc="$3"
  { time g++ $FLAGS $INC2 $inc -c -o /tmp/w24c_$label.o "$src" ; } 2> /tmp/w24c_$label.txt
  echo "PROBE $label: $(grep -a real /tmp/w24c_$label.txt) $(grep -ac error /tmp/w24c_$label.txt)"
}

for rep in 1 2; do
  run P${rep}_resparse_no src/resources/resource_parser.cpp ""
  run P${rep}_resparse_p  src/resources/resource_parser.cpp "-include $PCHSRC"
  run P${rep}_apkparse_p  src/apk/apk_parser.cpp "-include $PCHSRC"
  run P${rep}_apkparse_no src/apk/apk_parser.cpp ""
  run P${rep}_sqlsh_p     src/storage/sqlite_shadow.cpp "-include $PCHSRC"
  run P${rep}_sqlsh_no    src/storage/sqlite_shadow.cpp ""
  run P${rep}_layout_p    src/resources/layout_inflater.cpp "-include $PCHSRC"
  run P${rep}_layout_no   src/resources/layout_inflater.cpp ""
  run P${rep}_uig2_p      src/dex/dalvik_bridge_domain_ui_graphics.cpp "-include $PCHSRC"
  run P${rep}_uig2_no     src/dex/dalvik_bridge_domain_ui_graphics.cpp ""
done
echo PROBEC_DONE
