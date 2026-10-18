#!/usr/bin/env bash
# cont101_build_probes.sh — build the CONT-101 batch probes (CONT-99 T5 text,
# T6 z-order, T7 canvas save/clip) with the real toolchain (aapt2 link,
# ECJ, D8). No resources needed: all three fixtures are programmatic.
set -euo pipefail
cd /home/z/my-project

AAPT2=tools/toolchain/aapt2
BOOT=tools/toolchain/android-34.jar
ECJ=tools/toolchain/ecj.jar
D8JAR=tools/toolchain/r8.jar

build_one() {
  local FIX=$1 PKG=$2 OUT=$3 WORK=$4
  rm -rf "$WORK"; mkdir -p "$WORK/obj" "$WORK/dex" "$WORK/gen" "$(dirname "$OUT")"
  "$AAPT2" link -o "$WORK/base.apk" -I "$BOOT" \
    --manifest "$FIX/AndroidManifest.xml" --auto-add-overlay
  find "$FIX/src" -name "*.java" > "$WORK/sources.txt"
  java -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" -cp "$BOOT" @"$WORK/sources.txt"
  find "$WORK/obj" -name "*.class" > "$WORK/classes.txt"
  java -cp "$D8JAR" com.android.tools.r8.D8 --release \
    --lib "$BOOT" --output "$WORK/dex" @"$WORK/classes.txt"
  cp "$WORK/base.apk" "$OUT"
  ( cd "$WORK/dex" && zip -j -q -X "/home/z/my-project/$OUT" classes.dex )
  echo "built $OUT: $(sha256sum "/home/z/my-project/$OUT" | cut -c1-16)"
}

build_one fixtures/cont99_tx_probe com.probe.c99tx run/cont101/c99tx.apk tmp/cont101_tx_build
build_one fixtures/cont99_zo_probe com.probe.c99zo run/cont101/c99zo.apk tmp/cont101_zo_build
build_one fixtures/cont99_cv_probe com.probe.c99cv run/cont101/c99cv.apk tmp/cont101_cv_build
