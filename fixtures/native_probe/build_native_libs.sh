#!/usr/bin/env bash
# build_native_libs.sh — compile the S-2 native-execution fixture library
# for both ABIs from the single deterministic source native_probe.c.
#
#   x86_64  — host gcc (the ABI the runtime can genuinely execute)
#   arm64   — zig cc -target aarch64-linux-musl (extraction fixture;
#             honest ELF, never executable by the x86_64 host runtime)
#
# Determinism: fixed optimization flags, no build paths embedded
# (-ffile-prefix-map), fixed -frandom-seed.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$HERE"
ZIG="${ZIG:-/tmp/zig-linux-x86_64-0.13.0/zig}"

CFLAGS="-O2 -fPIC -fno-ident -frandom-seed=s2probe -ffile-prefix-map=$HERE=."

echo "[x86_64] host gcc"
gcc $CFLAGS -shared -o "$OUT/lib/x86_64/libprobe.so" "$HERE/native_probe.c"

if [ -x "$ZIG" ]; then
    echo "[arm64]  zig cc -target aarch64-linux-musl"
    "$ZIG" cc $CFLAGS -target aarch64-linux-musl -shared \
        -o "$OUT/lib/arm64/libprobe.so" "$HERE/native_probe.c"
    # Android ABI tree spelling
    mkdir -p "$OUT/lib/arm64-v8a"
    cp "$OUT/lib/arm64/libprobe.so" "$OUT/lib/arm64-v8a/libprobe.so"
else
    echo "zig missing — arm64 fixture not rebuilt" >&2
fi

file "$OUT/lib/x86_64/libprobe.so" 2>/dev/null || true
[ -f "$OUT/lib/arm64-v8a/libprobe.so" ] && file "$OUT/lib/arm64-v8a/libprobe.so"
sha256sum "$OUT/lib/x86_64/libprobe.so" "$OUT/lib/arm64-v8a/libprobe.so" | cut -c1-20
