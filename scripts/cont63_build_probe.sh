#!/usr/bin/env bash
# cont63_build_probe.sh — build fixtures/fnew351_probe into run/cont63/f351.apk
# (real aapt2/ECJ/D8 toolchain, the fnew345 recipe).
set -euo pipefail
cd /home/z/my-project
FIX=fixtures/fnew351_probe
WORK=tmp/f351_build
OUT=run/cont63
mkdir -p "$WORK/obj" "$WORK/dex" "$OUT"
AAPT2=tools/toolchain/aapt2
BOOT=tools/toolchain/android-34.jar
ECJ=tools/toolchain/ecj.jar
D8JAR=tools/toolchain/r8.jar
"$AAPT2" link -o "$WORK/resources.apk" -I "$BOOT" \
  --manifest "$FIX/AndroidManifest.xml" --auto-add-overlay
java -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" -cp "$BOOT" \
  "$FIX/src/com/probe/f351/MainActivity.java"
find "$WORK/obj" -name "*.class" > "$WORK/classes.txt"
java -cp "$D8JAR" com.android.tools.r8.D8 --release \
  --lib "$BOOT" --output "$WORK/dex" @"$WORK/classes.txt"
cp "$WORK/resources.apk" "$OUT/f351.apk"
cd "$WORK/dex" && zip -j -X "/home/z/my-project/$OUT/f351.apk" classes.dex > /dev/null
echo "probe apk: $(sha256sum /home/z/my-project/$OUT/f351.apk | cut -c1-16)"
