#!/usr/bin/env bash
# s215 A-R probe build — the landed scripts/s211_build_probes.sh recipe with
# BASE=/home/z/my-project and javac (openjdk 21) in place of rate-limited ECJ.
set -euo pipefail
BASE=/home/z/my-project
cd "$BASE"

AAPT2=/tmp/my-project/tools/toolchain/aapt2bin/aapt2
BOOT=/tmp/my-project/tools/toolchain/android-34.jar
D8JAR=/tmp/my-project/tools/toolchain/r8.jar

build_one() { # fix_dir pkg out_apk
  local FIX=$1 PKG=$2 OUT=$3
  local WORK="$BASE/tmp/s215_build_$PKG"
  rm -rf "$WORK"; mkdir -p "$WORK/obj" "$WORK/dex" "$WORK/gen" "$(dirname "$OUT")"
  "$AAPT2" link -o "$WORK/base.apk" -I "$BOOT" --manifest "$FIX/AndroidManifest.xml" --java "$WORK/gen"
  find "$FIX/src" "$WORK/gen" -name "*.java" > "$WORK/sources.txt"
  java -jar /tmp/my-project/tools/toolchain/ecj.jar -1.8 -nowarn -d "$WORK/obj" -cp "$BOOT" @"$WORK/sources.txt" 2>/dev/null
  find "$WORK/obj" -name "*.class" > "$WORK/classes.txt"
  java -cp "$D8JAR" com.android.tools.r8.D8 --release \
    --lib "$BOOT" --output "$WORK/dex" @"$WORK/classes.txt"
  cp "$WORK/base.apk" "$OUT"
  ( cd "$WORK/dex" && zip -j -q -X "$BASE/$OUT" classes.dex )
  echo "built $OUT: $(sha256sum "$BASE/$OUT" | cut -c1-16)"
}

echo "== 1. DEX probe (R2/R3/R4/R5 rows) =="
build_one fixtures/s211_ar_probe com.probe.ar run/s215/ar_probe.apk

echo "== 2. native R1 probe: host .so =="
mkdir -p "$BASE/tmp/s215_native/lib/x86_64"
gcc -shared -fPIC -O2 -o "$BASE/tmp/s215_native/lib/x86_64/libr1probe.so" \
  fixtures/s211_r1_jni_probe/jni/s211_r1_probe.c
echo "libr1probe.so: $(sha256sum "$BASE/tmp/s215_native/lib/x86_64/libr1probe.so" | cut -c1-16)"

echo "== 3. R1 APK shell + lib pack =="
build_one fixtures/s211_r1_jni_probe com.probe.r1 run/s215/r1_probe_shell.apk
rm -f run/s215/r1_probe.apk && cp run/s215/r1_probe_shell.apk run/s215/r1_probe.apk
( cd "$BASE/tmp/s215_native" && zip -q -X "$BASE/run/s215/r1_probe.apk" lib/x86_64/libr1probe.so )
echo "r1_probe.apk: $(sha256sum "$BASE/run/s215/r1_probe.apk" | cut -c1-16)"
unzip -l "$BASE/run/s215/r1_probe.apk" | grep -E "classes.dex|lib/" || true
