#!/usr/bin/env bash
# cont9_rebuild_gate_a_probe.sh — rebuild fixtures/gate_a_probe into
# gate_a_probe.apk at the repo root (the canonical probe for Gate A,
# negatives 19/19 and skill OP-1). Real toolchain: aapt2 link, ECJ 1.8,
# D8 release, gcc for the x86_64 native lib, apksigner-free debug zip
# repack preserving aapt2 entry metadata (W4 lesson: STORED assets).
set -euo pipefail
cd /home/z/my-project
FIX=fixtures/gate_a_probe
WORK=tmp/gatea_rebuild
rm -rf "$WORK"; mkdir -p "$WORK/gen" "$WORK/obj" "$WORK/dex" "$WORK/apk"

AAPT2=tools/toolchain/aapt2
D8=tools/d8
BOOT=tools/toolchain/android-34.jar
ECJ=tools/toolchain/ecj.jar
D8JAR=tools/toolchain/r8.jar

# 1. resources → proto + java ids
"$AAPT2" compile --dir "$FIX/res" -o "$WORK/res.zip"
"$AAPT2" link -o "$WORK/apk/resources.apk" -I "$BOOT" \
  --manifest "$FIX/AndroidManifest.xml" --java "$WORK/gen" \
  --auto-add-overlay "$WORK/res.zip"

# 2. java → class
find "$FIX/src" "$WORK/gen" -name "*.java" > "$WORK/sources.txt"
java -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" \
  -cp "$BOOT" @"$WORK/sources.txt"

# 3. dex
find "$WORK/obj" -name "*.class" > "$WORK/classes.txt"
java -cp "$D8JAR" com.android.tools.r8.D8 --release \
  --lib "$BOOT" --output "$WORK/dex" @"$WORK/classes.txt"

# 4. native lib (x86_64, real gcc) — JNI_OnLoad + a callable symbol
cat > "$WORK/probe.c" <<'EOF'
#include <stdint.h>
/* Minimal JNI surface (no jni.h in container): the engine's dlopen bridge
   only needs the symbols to exist with System-V x86_64 calling convention.
   JNI_VERSION_1_6 == 0x00010006. */
typedef struct _JavaVM _JavaVM;
typedef struct _JNIEnv _JNIEnv;
typedef int32_t jint;
typedef int64_t jlong;
typedef void* jclass;
#define JNIEXPORT __attribute__((visibility("default")))
#define JNICALL
jint JNI_OnLoad(_JavaVM* vm, void* reserved) {
    return 0x00010006;
}
JNIEXPORT jlong JNICALL Java_com_probe_gatea_MainActivity_probeFib(_JNIEnv* e, jclass c, jlong n) {
    jlong a = 0, b = 1;
    for (jlong i = 0; i < n; ++i) { jlong t = a + b; a = b; b = t; }
    return a;
}
EOF
gcc -shared -fPIC -O2 -o "$WORK/apk/libx8664.so" "$WORK/probe.c"
echo "libprobe sha16: $(sha256sum "$WORK/apk/libx8664.so" | cut -c1-16)"
cd /home/z/my-project   # restore cwd for all following relative paths

# 5. assemble the APK: aapt2's resources.apk + classes.dex + native lib
#    + assets — aapt2 entry metadata preserved (W4 lesson). All absolute.
ROOT=/home/z/my-project
cp "$WORK/apk/resources.apk" "$ROOT/gate_a_probe.apk"
( cd "$WORK/apk" && zip -j -q -X "$ROOT/gate_a_probe.apk" "$ROOT/$WORK/dex/classes.dex" )
mkdir -p "$WORK/apk/lib/x86_64"
cp "$WORK/apk/libx8664.so" "$WORK/apk/lib/x86_64/libprobe.so"
( cd "$WORK/apk" && zip -q -X "$ROOT/gate_a_probe.apk" lib/x86_64/libprobe.so )
# W4 law: asset entries must stay STORED (uncompressed) — openFd
# (FD-01..03) requires a map-able raw entry, DEFLATE breaks it.
( cd "$ROOT/$FIX" && zip -q -r -0 -X "$ROOT/gate_a_probe.apk" assets )
echo "gate_a_probe.apk sha256: $(sha256sum gate_a_probe.apk | cut -c1-32)"
