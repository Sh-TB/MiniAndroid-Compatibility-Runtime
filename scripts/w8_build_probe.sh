#!/usr/bin/env bash
# w8_build_probe.sh — build fixtures/fnew520_probe into run/w8/f520.apk
# (the cont10_build_probe.sh pattern: aapt2 link + ECJ + D8, STORED dex)
set -euo pipefail
cd /home/z/my-project
FIX=fixtures/fnew520_probe
WORK=tmp/f520_build
rm -rf "$WORK"; mkdir -p "$WORK/obj" "$WORK/dex" "$WORK/apk"
AAPT2=tools/toolchain/aapt2
BOOT=tools/toolchain/android-34.jar
ECJ=tools/toolchain/ecj.jar
D8JAR=tools/toolchain/r8.jar
"$AAPT2" link -o "$WORK/apk/resources.apk" -I "$BOOT" \
  --manifest "$FIX/AndroidManifest.xml" --auto-add-overlay
java -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" -cp "$BOOT" \
  "$FIX/src/com/probe/f520/MainActivity.java"
find "$WORK/obj" -name "*.class" > "$WORK/classes.txt"
java -cp "$D8JAR" com.android.tools.r8.D8 --release \
  --lib "$BOOT" --output "$WORK/dex" @"$WORK/classes.txt"
cp "$WORK/apk/resources.apk" run/w8/f520.apk
cd "$WORK/dex" && zip -j -X /home/z/my-project/run/w8/f520.apk classes.dex > /dev/null
echo "probe apk: $(sha256sum /home/z/my-project/run/w8/f520.apk | cut -c1-16)"
