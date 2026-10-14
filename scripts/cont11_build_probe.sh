#!/usr/bin/env bash
# cont11_build_probe.sh — build fixtures/fnew264_probe into run/cont11/f264.apk
set -euo pipefail
cd /home/z/my-project
FIX=fixtures/fnew264_probe
WORK=tmp/f264_build
OUT=run/cont11
mkdir -p "$WORK/obj" "$WORK/dex" "$WORK/apk" "$OUT"
AAPT2=tools/toolchain/aapt2
BOOT=tools/toolchain/android-34.jar
ECJ=tools/toolchain/ecj.jar
D8JAR=tools/toolchain/r8.jar
"$AAPT2" link -o "$WORK/apk/resources.apk" -I "$BOOT" \
  --manifest "$FIX/AndroidManifest.xml" --auto-add-overlay
java -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" -cp "$BOOT" \
  "$FIX/src/com/probe/f264/MainActivity.java"
find "$WORK/obj" -name "*.class" > "$WORK/classes.txt"
java -cp "$D8JAR" com.android.tools.r8.D8 --release \
  --lib "$BOOT" --output "$WORK/dex" @"$WORK/classes.txt"
cp "$WORK/apk/resources.apk" "$OUT/f264.apk"
cd "$WORK/dex" && zip -j -X "/home/z/my-project/$OUT/f264.apk" classes.dex > /dev/null
echo "probe apk: $(sha256sum /home/z/my-project/$OUT/f264.apk | cut -c1-16)"
