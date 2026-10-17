#!/usr/bin/env bash
# cont83_build_gfx_probe.sh — build the CONT-83 graphics-boundary probe
# (com.probe.gfx1) with the real aapt2/ECJ/D8 toolchain.
set -euo pipefail
cd /home/z/my-project

AAPT2=tools/toolchain/aapt2
BOOT=tools/toolchain/android-34.jar
ECJ=tools/toolchain/ecj.jar
D8JAR=tools/toolchain/r8.jar

FIX=fixtures/cont83_gfx_probe
MAN=$FIX/AndroidManifest.xml
OUT=run/cont83/gfx1.apk
WORK=tmp/cont83_build

rm -rf "$WORK"; mkdir -p "$WORK/obj" "$WORK/dex" "$(dirname "$OUT")"
mkdir -p "$WORK/gen"
"$AAPT2" link -o "$WORK/base.apk" -I "$BOOT" --manifest "$MAN" --java "$WORK/gen"
find "$FIX/src" "$WORK/gen" -name "*.java" > "$WORK/sources.txt"
java -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" -cp "$BOOT" @"$WORK/sources.txt"
find "$WORK/obj" -name "*.class" > "$WORK/classes.txt"
java -cp "$D8JAR" com.android.tools.r8.D8 --release \
  --lib "$BOOT" --output "$WORK/dex" @"$WORK/classes.txt"
cp "$WORK/base.apk" "$OUT"
( cd "$WORK/dex" && zip -j -q -X "/home/z/my-project/$OUT" classes.dex )
echo "built $OUT: $(sha256sum "/home/z/my-project/$OUT" | cut -c1-16)"
