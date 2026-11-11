#!/usr/bin/env bash
# s211_build_probes.sh — build the S211 A-R probes (real aapt2/ECJ/D8 +
# host-native .so for the R1 JNI probe). Adapted from the cont102 recipe;
# paths local to the repo checkout.
set -euo pipefail
BASE=/home/z/my-project/repo
cd "$BASE"

AAPT2="$BASE/tools/toolchain/aapt2"
BOOT="$BASE/tools/toolchain/android-34.jar"
ECJ="$BASE/tools/toolchain/ecj.jar"
D8JAR="$BASE/tools/toolchain/r8.jar"

build_one() { # fix_dir pkg out_apk
  local FIX=$1 PKG=$2 OUT=$3
  local MAN="$FIX/AndroidManifest.xml"
  local WORK="$BASE/tmp/s211_build_$PKG"
  rm -rf "$WORK"; mkdir -p "$WORK/obj" "$WORK/dex" "$WORK/gen" "$(dirname "$OUT")"
  "$AAPT2" link -o "$WORK/base.apk" -I "$BOOT" --manifest "$MAN" --java "$WORK/gen"
  find "$FIX/src" "$WORK/gen" -name "*.java" > "$WORK/sources.txt"
  java -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" -cp "$BOOT" @"$WORK/sources.txt"
  find "$WORK/obj" -name "*.class" > "$WORK/classes.txt"
  java -cp "$D8JAR" com.android.tools.r8.D8 --release \
    --lib "$BOOT" --output "$WORK/dex" @"$WORK/classes.txt"
  cp "$WORK/base.apk" "$OUT"
  ( cd "$WORK/dex" && zip -j -q -X "$BASE/$OUT" classes.dex )
  echo "built $OUT: $(sha256sum "$BASE/$OUT" | cut -c1-16)"
}

echo "== 1. DEX probe (R2/R3/R4/R5) =="
build_one fixtures/s211_ar_probe com.probe.ar run/s211/ar_probe.apk

echo "== 2. native R1 probe: host .so =="
mkdir -p "$BASE/tmp/s211_native/lib/x86_64"
gcc -shared -fPIC -O2 -o "$BASE/tmp/s211_native/lib/x86_64/libr1probe.so" \
  fixtures/s211_r1_jni_probe/jni/s211_r1_probe.c
echo "libr1probe.so: $(sha256sum "$BASE/tmp/s211_native/lib/x86_64/libr1probe.so" | cut -c1-16)"

echo "== 3. R1 APK shell + lib pack =="
build_one fixtures/s211_r1_jni_probe com.probe.r1 run/s211/r1_probe_shell.apk
cp run/s211/r1_probe_shell.apk run/s211/r1_probe.apk
( cd "$BASE/tmp/s211_native" && zip -j -q -X "$BASE/run/s211/r1_probe.apk" \
    lib/x86_64/libr1probe.so 2>/dev/null || \
  cd "$BASE/tmp/s211_native" && zip -q -X "$BASE/run/s211/r1_probe.apk" lib/x86_64/libr1probe.so )
# NOTE: the .so must ride at lib/x86_64/ INSIDE the apk — the -j flatten
# above loses the dir; repack properly:
rm -f run/s211/r1_probe.apk && cp run/s211/r1_probe_shell.apk run/s211/r1_probe.apk
( cd "$BASE/tmp/s211_native" && zip -q -X "$BASE/run/s211/r1_probe.apk" lib/x86_64/libr1probe.so )
echo "r1_probe.apk: $(sha256sum "$BASE/run/s211/r1_probe.apk" | cut -c1-16)"
unzip -l "$BASE/run/s211/r1_probe.apk" | grep -E "classes.dex|lib/"