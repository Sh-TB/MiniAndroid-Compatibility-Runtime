#!/usr/bin/env bash
# cont86_build_probes.sh — build the CONT-86 fixtures (com.probe.swipe1 +
# com.probe.clock1) with the real aapt2/ECJ/D8 toolchain.
set -euo pipefail
cd /home/z/my-project

AAPT2=tools/toolchain/aapt2
BOOT=tools/toolchain/android-34.jar
ECJ=tools/toolchain/ecj.jar
D8JAR=tools/toolchain/r8.jar

build_one() {
  local FIX=$1 MAN=$2 OUT=$3 WORK=$4
  rm -rf "$WORK"; mkdir -p "$WORK/obj" "$WORK/dex" "$WORK/gen" "$(dirname "$OUT")"
  "$AAPT2" link -o "$WORK/base.apk" -I "$BOOT" --manifest "$MAN" --java "$WORK/gen"
  find "$FIX/src" "$WORK/gen" -name "*.java" > "$WORK/sources.txt"
  java -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" -cp "$BOOT" @"$WORK/sources.txt"
  find "$WORK/obj" -name "*.class" > "$WORK/classes.txt"
  java -cp "$D8JAR" com.android.tools.r8.D8 --release \
    --lib "$BOOT" --output "$WORK/dex" @"$WORK/classes.txt"
  cp "$WORK/base.apk" "$OUT"
  ( cd "$WORK/dex" && zip -j -q -X "/home/z/my-project/$OUT" classes.dex )
  echo "built $OUT: $(sha256sum "/home/z/my-project/$OUT" | cut -c1-16)"
}

build_one fixtures/cont86_swipe_probe \
          fixtures/cont86_swipe_probe/AndroidManifest.xml \
          run/cont86/swipe1.apk tmp/cont86_swipe_build
build_one fixtures/cont86_clock_probe \
          fixtures/cont86_clock_probe/AndroidManifest.xml \
          run/cont86/clock1.apk tmp/cont86_clock_build
