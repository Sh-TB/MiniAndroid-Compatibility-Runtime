#!/usr/bin/env bash
# w23_repoint_includes.sh — W23-03 phase 2: repoint consumers after the
# dalvik_engine.h split (types/impl). Every repoint is a pure include-path
# change with identical resulting translation-unit content:
#   - engine-family TUs + deep consumers  -> dalvik_engine_impl.h
#   - public-surface consumers            -> dalvik_engine_types.h
set -euo pipefail
REPO=${MINIANDROID_REPO:-/home/z/my-project/miniandroid}
cd "$REPO"

# 1) engine family + deep consumers -> impl header
for f in \
  src/dex/dalvik_engine.cpp \
  src/dex/dalvik_engine_core.cpp \
  src/dex/dalvik_engine_invoke.cpp \
  src/dex/dalvik_engine_tail.cpp \
  src/dex/dalvik_interpreter.cpp \
  src/dex/dalvik_opcodes.cpp \
  src/dex/dalvik_opcodes_invoke.cpp \
  src/dex/dalvik_bridge.cpp \
  src/dex/dalvik_value_glue.cpp \
  src/dex/dalvik_bridge_frame.h \
  src/dex/dalvik_engine_internal.h \
  src/runtime/application_runtime.cpp \
  src/dex/trace_exporter.cpp \
  ; do
  sed -i 's|#include "dalvik_engine.h"|#include "dalvik_engine_impl.h"|; s|#include "dex/dalvik_engine.h"|#include "dex/dalvik_engine_impl.h"|' "$f"
done

# 2) public-surface consumer -> types header
sed -i 's|#include "dalvik_engine.h"|#include "dalvik_engine_types.h"|' src/dex/trace_exporter.h

# 3) tests that include the engine header -> impl header (same content as before)
grep -rl 'include.*"\.\./src/dex/dalvik_engine.h"' tests/ | while read -r f; do
  sed -i 's|#include "../src/dex/dalvik_engine.h"|#include "../src/dex/dalvik_engine_impl.h"|' "$f"
done

echo "repoint done:"; grep -rln 'include.*dalvik_engine\.h"' src tests | sort
