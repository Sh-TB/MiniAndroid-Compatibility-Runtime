#!/bin/bash
# EXP-042 Build Script — MiniAndroid Runtime
# Builds the megabatch runtime executable for Telegram APK execution.
set -e

ROOT=/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid
SRC=$ROOT/src
BUILD=$ROOT/build_exp042
OUT=$BUILD/miniandroid_exp042

mkdir -p $BUILD

CXXFLAGS="-std=c++17 -O2 -Wno-unused-result -Wno-trigraphs -I$SRC -I$ROOT/third_party/nlohmann_json/include"

# Sources that the megabatch binary depends on.
SOURCES=(
    "src/apk/apk_parser.cpp"
    "src/apk/manifest_reader.cpp"
    "src/dex/dex_parser.cpp"
    "src/dex/class_resolver.cpp"
    "src/dex/dex_interpreter_batch.cpp"
    "src/dex/dalvik_engine.cpp"
    "src/dex/api_dispatcher.cpp"
    "src/dex/execution_observatory.cpp"
    "src/dex/trace_exporter.cpp"
    "src/runtime/execution_engine.cpp"
    "src/runtime/application_runtime.cpp"
    "src/resources/resource_parser.cpp"
    "src/renderer/software_renderer.cpp"
    "src/diagnostics/trace_engine.cpp"
    "src/api/application_context.cpp"
    "src/api/shared_prefs.cpp"
    "src/storage/file_sandbox.cpp"
    "src/exp007_012_megabatch_main.cpp"
)

OBJS=""
echo "[BUILD] EXP-042 MiniAndroid Runtime"
echo "  SRC: $SRC"
echo "  OUT: $OUT"
echo ""

for src in "${SOURCES[@]}"; do
    obj="$BUILD/$(basename ${src%.cpp}.o)"
    g++ $CXXFLAGS -c "$ROOT/$src" -o "$obj" 2>&1 | head -3 || true
    if [ ! -f "$obj" ]; then
        # Try with stderr captured fully
        if ! g++ $CXXFLAGS -c "$ROOT/$src" -o "$obj" 2>"$BUILD/.last_err"; then
            echo "FAILED: $src"
            cat "$BUILD/.last_err"
            exit 1
        fi
    fi
    OBJS="$OBJS $obj"
done

echo "[LINK] miniandroid_exp042"
g++ $CXXFLAGS -pthread $OBJS -o $OUT -lz -lpthread
echo "[OK]   $OUT"
