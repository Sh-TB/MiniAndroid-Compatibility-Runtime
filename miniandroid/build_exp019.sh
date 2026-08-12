#!/bin/bash
# Build script for EXP-019 Runtime Integration
# Compiles the required source files in dependency order

set -e

SRC_DIR="/home/z/my-project/miniandroid/src"
BUILD_DIR="/home/z/my-project/miniandroid/build_exp019"
OUTPUT="$BUILD_DIR/miniandroid_exp019"

echo "============================================"
echo "Building MiniAndroid EXP-019"
echo "============================================"

mkdir -p $BUILD_DIR

# Compiler flags
CXXFLAGS="-std=c++17 -Wall -Wextra -O2"
INCLUDES="-I$SRC_DIR -I$SRC_DIR/third_party/nlohmann_json/include -I/home/z/my-project/miniandroid/third_party/nlohmann_json/include"

# Object files
OBJS=""

# Source files in dependency order
SOURCES=(
    "$SRC_DIR/apk/apk_parser.cpp"
    "$SRC_DIR/apk/manifest_reader.cpp"
    "$SRC_DIR/dex/dex_parser.cpp"
    "$SRC_DIR/dex/class_resolver.cpp"
    "$SRC_DIR/dex/dex_interpreter_batch.cpp"
    "$SRC_DIR/runtime/execution_engine.cpp"
    "$SRC_DIR/resources/resource_parser.cpp"
    "$SRC_DIR/renderer/software_renderer.cpp"
    "$SRC_DIR/diagnostics/trace_engine.cpp"
    "$SRC_DIR/runtime/application_runtime.cpp"
    "$SRC_DIR/dex/dex_interpreter_exp018.cpp"
    "$SRC_DIR/runtime/runtime_integration_exp019.cpp"
    "$SRC_DIR/exp019_main.cpp"
)

echo ""
echo "Compiling source files..."
echo ""

for SRC in "${SOURCES[@]}"; do
    if [ -f "$SRC" ]; then
        OBJ="$BUILD_DIR/$(basename ${SRC%.cpp}.o)"
        echo "  [CC] $(basename $SRC)"
        g++ $CXXFLAGS $INCLUDES -c "$SRC" -o "$OBJ" 2>&1 || {
            echo "ERROR: Failed to compile $SRC"
            exit 1
        }
        OBJS="$OBJS $OBJ"
    else
        echo "  [SKIP] $SRC (not found)"
    fi
done

echo ""
echo "Linking..."
echo "  [LD] miniandroid_exp019"

g++ $CXXFLAGS $OBJS -o $OUTPUT -lz 2>&1 || {
    echo "ERROR: Linking failed"
    exit 1
}

echo ""
echo "============================================"
echo "Build successful!"
echo "Output: $OUTPUT"
echo "============================================"
