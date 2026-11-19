#!/usr/bin/env bash
# w23_shrink_probe.sh — W23-03 phase 3: shrink the public types header.
#
# After the verbatim split, dalvik_engine_types.h still carries the 13 heavy
# project includes the CLASS (dalvik_engine_impl.h) needs. This script probes,
# one include at a time, whether the public types surface still compiles with
# that include removed from types.h (and, when removal succeeds, the include is
# appended to impl.h instead). Probes compile two representative public-surface
# consumers with -fsyntax-only:
#   - src/dex/trace_exporter.cpp   (small, fast)
#   - src/runtime/execution_engine.cpp   (the 38 s TU; frontend-only probe)
#
# On probe failure the include is restored in types.h. A summary of moved vs
# kept includes is printed at the end. Run AFTER w23_split_engine_header.py +
# w23_repoint_includes.sh.
set -uo pipefail
REPO=${MINIANDROID_REPO:-/home/z/my-project/miniandroid}
cd "$REPO"

TYPES=src/dex/dalvik_engine_types.h
IMPL=src/dex/dalvik_engine_impl.h
FLAGS="-std=c++17 -fsyntax-only -DMINIANDROID_HAVE_WEBP -Isrc -Isrc/webview -Isrc/apk -Isrc/dex -Isrc/runtime -Isrc/api -Isrc/graphics -Isrc/diagnostics -Isrc/resources -Isrc/renderer -Isrc/framework -Isrc/storage -Isrc/fonts -Isrc/gles -Isrc/jni -Isrc/audio -Ithird_party/portablegl -I/usr/include/freetype2 -Ithird_party/nlohmann_json/include -Ibuild/generated"

probe() {
  g++ $FLAGS src/dex/trace_exporter.cpp 2>/dev/null && \
  g++ $FLAGS src/runtime/execution_engine.cpp 2>/dev/null
}

# candidate heavy project includes (exact include lines as written)
CANDIDATES=(
  '#include "dex_parser.h"'
  '#include "class_resolver.h"'
  '#include "../apk/manifest_reader.h"'
  '#include "c7_package_index.h"'
  '#include "../runtime/runtime_metadata.h"'
  '#include "../runtime/vtable_dispatch.h"'
  '#include "../api/android_stubs.h"'
  '#include "../resources/arsc_parser.h"'
  '#include "../resources/attribute_set_store.h"'
  '#include "../resources/res_config.h"'
  '#include "../storage/sqlite_shadow.h"'
  '#include "../storage/data_root.h"'
  '#include "../framework/adapter_scrap_bin.h"'
)

MOVED=(); KEPT=()
for inc in "${CANDIDATES[@]}"; do
  if ! grep -qF "$inc" "$TYPES"; then
    echo "SKIP (not found in types.h): $inc"; continue
  fi
  # comment it out in types.h
  sed -i "s|^${inc} \$|// W23-SHRINK moved candidate: ${inc}|" "$TYPES" || true
  sed -i "s|^${inc}|// W23-SHRINK moved candidate: ${inc}|" "$TYPES"
  if probe; then
    # success: delete from types.h, add to impl.h (before the namespace open)
    sed -i "\|^// W23-SHRINK moved candidate: ${inc}|d" "$TYPES"
    sed -i "s|^#include \"dalvik_engine_types.h\"|#include \"dalvik_engine_types.h\"\n${inc}|" "$IMPL"
    MOVED+=("$inc"); echo "MOVED: $inc"
  else
    # restore
    sed -i "s|^// W23-SHRINK moved candidate: ${inc}|${inc}|" "$TYPES"
    KEPT+=("$inc"); echo "KEPT (still needed by public surface): $inc"
  fi
done

echo "--- moved ${#MOVED[@]}, kept ${#KEPT[@]}"
printf 'MOVED:\n'; printf '  %s\n' "${MOVED[@]:-none}"
printf 'KEPT:\n'; printf '  %s\n' "${KEPT[@]:-none}"
