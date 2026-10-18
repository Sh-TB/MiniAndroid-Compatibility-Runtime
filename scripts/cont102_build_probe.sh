#!/usr/bin/env bash
# cont102_build_probe.sh — build ALL CONT-102 batch probes (real aapt2/ECJ/D8).
set -euo pipefail
cd /home/z/my-project

AAPT2=tools/toolchain/aapt2
BOOT=tools/toolchain/android-34.jar
ECJ=tools/toolchain/ecj.jar
D8JAR=tools/toolchain/r8.jar

build_one() { # fix_dir pkg out_apk
  local FIX=$1 PKG=$2 OUT=$3
  local MAN=$FIX/AndroidManifest.xml
  local WORK=tmp/cont102_build_$PKG
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

build_one fixtures/cont102_a_probe com.probe.c102a run/cont102/c102a.apk
build_one fixtures/cont102_b_probe com.probe.c102b run/cont102/c102b.apk
build_one fixtures/cont102_c_probe com.probe.c102c run/cont102/c102c.apk
build_one fixtures/cont102_d_probe com.probe.c102d run/cont102/c102d.apk
