#!/usr/bin/env bash
# cont83_build_native_probe.sh — build the F-NEW-387 dependency-law probe.
#
# libnatprobe.so: real host gcc x86_64 .so with
#   - a REAL libm dependency (sin() in the JNI function), and
#   - a HEX-PATCHED DT_NEEDED "libm.so.6" → "libm.so" (the Android platform
#     soname the host loader cannot resolve) — reproducing the exact
#     stack.tower3d failure shape in a minimal, deterministic probe.
# Variants:
#   libnatprobe.so        → DT_NEEDED libm.so    (positive: anchor serves)
#   libnatprobe_noshadow.so → DT_NEEDED libnosuchdep.so (negative: honest
#     missing-honest-block; the dlopen must fail loudly)
#   an ld-script masquerading as libm.so staged into a BAD anchor dir
#     (validation negative: must be rejected, never dlopen'd)
set -euo pipefail
cd /home/z/my-project

AAPT2=tools/toolchain/aapt2
BOOT=tools/toolchain/android-34.jar
ECJ=tools/toolchain/ecj.jar
D8JAR=tools/toolchain/r8.jar

FIX=fixtures/cont83_native_probe
OUT=run/cont83/nat1.apk
WORK=tmp/cont83_native
rm -rf "$WORK"; mkdir -p "$WORK/obj" "$WORK/dex" "$WORK/lib/x86_64" "$(dirname "$OUT")"

# ── 1. native lib: real sin() + JNI, then patch the soname ─────────────
cat > "$WORK/natprobe.c" <<'EOF'
#include <math.h>
#include <stdint.h>
typedef struct _JavaVM _JavaVM;
typedef struct _JNIEnv _JNIEnv;
typedef int32_t jint;
typedef int64_t jlong;
typedef void* jclass;
#define JNIEXPORT __attribute__((visibility("default")))
#define JNICALL
jint JNI_OnLoad(_JavaVM* vm, void* reserved) { return 0x00010006; }
JNIEXPORT jint JNICALL Java_com_probe_nat1_NativeProbe_add3(
        _JNIEnv* e, jclass c, jint a, jint b, jint c2) {
    // Real libm use: the result folds a sin()-derived zero so the DT_NEEDED
    // libm dependency is a real symbol requirement, not decoration.
    double s = sin((double)(a + b + c2));
    return a + b + c2 + (jint)s;
}
JNIEXPORT jint JNICALL Java_com_probe_nat1_NativeProbe_mathCheck(
        _JNIEnv* e, jclass c, jint v) {
    // sqrt+pow chain: returns ((int)sqrt(pow(v,2))) — v when libm resolves.
    return (jint)sqrt(pow((double)v, 2.0));
}
EOF
ANCHORS=miniandroid/build/anchor_libs
echo 'int __no_anchor;' > "$WORK/noanchor.c"
gcc -shared -fPIC -O2 -Wl,-soname,libno.so -o "$WORK/libno.so" "$WORK/noanchor.c"
# POSITIVE: link against the REAL first-party libm.so anchor (its SONAME
# becomes the DT_NEEDED — the exact Android platform-soname shape) with a
# genuine libm symbol requirement (sin/sqrt/pow).
gcc -shared -fPIC -O2 -Wl,-soname,libnatprobe.so -Wl,--no-as-needed \
    "$ANCHORS/libm.so" -o "$WORK/lib/x86_64/libnatprobe.so" "$WORK/natprobe.c"
# NEGATIVE: DT_NEEDED libno.so has no app copy and no anchor — the
# honest missing-honest-block row + loud UnsatisfiedLinkError.
gcc -shared -fPIC -O2 -Wl,-soname,libnatprobe_noshadow.so -Wl,--no-as-needed \
    "$WORK/libno.so" -o "$WORK/lib/x86_64/libnatprobe_noshadow.so" "$WORK/natprobe.c"
readelf -d "$WORK/lib/x86_64/libnatprobe.so" | grep NEEDED
readelf -d "$WORK/lib/x86_64/libnatprobe_noshadow.so" | grep NEEDED

# ── 2. the probe APK (Java side + both libs) ───────────────────────────
MAN=$FIX/AndroidManifest.xml
"$AAPT2" link -o "$WORK/base.apk" -I "$BOOT" --manifest "$MAN" --java "$WORK/gen"
find "$FIX/src" "$WORK/gen" -name "*.java" > "$WORK/sources.txt"
java -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" -cp "$BOOT" @"$WORK/sources.txt"
find "$WORK/obj" -name "*.class" > "$WORK/classes.txt"
java -cp "$D8JAR" com.android.tools.r8.D8 --release \
  --lib "$BOOT" --output "$WORK/dex" @"$WORK/classes.txt"
cp "$WORK/base.apk" "$OUT"
( cd "$WORK/dex" && zip -j -q -X "/home/z/my-project/$OUT" classes.dex )
( cd "$WORK" && zip -q -X "/home/z/my-project/$OUT" \
    lib/x86_64/libnatprobe.so lib/x86_64/libnatprobe_noshadow.so )
echo "built $OUT: $(sha256sum "/home/z/my-project/$OUT" | cut -c1-16)"
echo "libs: $WORK/lib/x86_64/"
