#!/usr/bin/env bash
# cont11_build_probe.sh — build fixtures/fnew261_probe into run/w7/f261.apk
# (real toolchain: aapt2 + ECJ + D8, same law as cont10_build_probe.sh)
set -euo pipefail
cd /home/z/my-project
FIX=fixtures/fnew261_probe
WORK=tmp/f261_build
rm -rf "$WORK"; mkdir -p "$WORK/obj" "$WORK/dex"
AAPT2=tools/toolchain/aapt2
BOOT=tools/toolchain/android-34.jar
ECJ=tools/toolchain/ecj.jar
D8JAR=tools/toolchain/r8.jar
"$AAPT2" link -o "$WORK/resources.apk" -I "$BOOT" \
  --manifest "$FIX/AndroidManifest.xml" --auto-add-overlay
java -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" -cp "$BOOT" \
  "$FIX/src/com/probe/f261/MainActivity.java"
find "$WORK/obj" -name "*.class" > "$WORK/classes.txt"
java -cp "$D8JAR" com.android.tools.r8.D8 --release \
  --lib "$BOOT" --output "$WORK/dex" @"$WORK/classes.txt"
cp "$WORK/resources.apk" run/w7/f261.apk
cd "$WORK/dex" && zip -j -X /home/z/my-project/run/w7/f261.apk classes.dex > /dev/null
echo "probe apk: $(sha256sum /home/z/my-project/run/w7/f261.apk | cut -c1-16)"
