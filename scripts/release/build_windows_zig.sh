#!/usr/bin/env bash
# S214-WP1 Windows cross-compile attempt (#587) — pinned route, honest result.
#
# This script IS the current Windows build attempt: it cross-compiles four
# representative runtime TUs with the pinned zig/llvm-mingw route and reports
# the exact first errors. Exit 1 = Windows artifact remains BLOCKED (the
# expected result until the dependency + POSIX-shim port lands; see
# docs/ci/WINDOWS_TOOLCHAIN.md). Exit 0 = every probe compiled, extend this
# script to the full build (build-exe + package_release.sh --platform windows).
set -u
cd "$(dirname "$0")/../../miniandroid" || exit 1

ZIG_PIN="0.17.1"
ZIG_VERSION="$(python3 -m ziglang version 2>/dev/null || true)"
if [ "$ZIG_VERSION" != "$ZIG_PIN" ]; then
    echo "FAIL pinned toolchain missing: pip install ziglang==${ZIG_PIN} (found: '${ZIG_VERSION}')"
    exit 1
fi
echo "toolchain: ziglang ${ZIG_VERSION} (pip-pinned) -target x86_64-windows-gnu"

INCLUDES="-Isrc -Isrc/apk -Isrc/dex -Isrc/runtime -Isrc/api -Isrc/graphics -Isrc/diagnostics \
-Isrc/resources -Isrc/renderer -Isrc/framework -Isrc/storage -Isrc/fonts -Isrc/gles \
-Isrc/jni -Isrc/audio -Ithird_party/portablegl -Ithird_party/nlohmann_json/include"

TUS="src/dex/dalvik_engine.cpp src/apk/apk_parser.cpp src/main.cpp src/storage/sqlite_shadow.cpp"
FAIL=0
for tu in $TUS; do
    echo "=== probe: $tu"
    if python3 -m ziglang c++ -target x86_64-windows-gnu -std=c++17 -fsyntax-only $INCLUDES "$tu" 2>&1 | grep -E "error" | head -2; then
        FAIL=1
    else
        echo "    compiled clean"
    fi
done

if [ "$FAIL" -eq 1 ]; then
    echo "RESULT: Windows x86_64 artifact BLOCKED — POSIX shims + 11 C-dependency Windows builds required"
    echo "        (exact matrix: docs/ci/WINDOWS_TOOLCHAIN.md; gate: scripts/release/validate_release_manifest.py)"
    exit 1
fi
echo "RESULT: all probes compiled clean — extend to full build"
exit 0
