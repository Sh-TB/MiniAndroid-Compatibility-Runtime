#!/usr/bin/env bash
# cont46_build_probes.sh — build the CONT-46 Phase-3 probe fixtures
# (fnew262 bridge<->DEX object-flow + fnew260 getModifiers zoo) with the
# real aapt2/ECJ/D8 toolchain.
set -euo pipefail
cd /home/z/my-project
AAPT2=tools/toolchain/aapt2
BOOT=tools/toolchain/android-34.jar
ECJ=tools/toolchain/ecj.jar
D8JAR=tools/toolchain/r8.jar

build_one() { # build_one <fixture> <out-apk>
  local FIX="fixtures/$1" WORK="tmp/cont46_probebuild/$1" OUT="$2"
  rm -rf "$WORK"; mkdir -p "$WORK/obj" "$WORK/dex" "$WORK/apk"
  "$AAPT2" link -o "$WORK/apk/resources.apk" -I "$BOOT" \
    --manifest "$FIX/AndroidManifest.xml" --auto-add-overlay
  local SRCS=$(find "$FIX/src" -name "*.java")
  java -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" -cp "$BOOT" $SRCS
  find "$WORK/obj" -name "*.class" > "$WORK/classes.txt"
  java -cp "$D8JAR" com.android.tools.r8.D8 --release \
    --lib "$BOOT" --output "$WORK/dex" @"$WORK/classes.txt"
  cp "$WORK/apk/resources.apk" "$OUT"
  (cd "$WORK/dex" && zip -j -X "/home/z/my-project/$OUT" classes.dex > /dev/null)
  echo "built $OUT: $(sha256sum "/home/z/my-project/$OUT" | cut -c1-16)"
}

build_one fnew262_probe run/cont46/fnew262_probe.apk
build_one fnew260_probe run/cont46/fnew260_probe.apk
