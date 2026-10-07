#!/usr/bin/env bash
# cont10_build_probe.sh — build fixtures/fnew259_probe into run/w7/f259.apk
set -euo pipefail
cd /home/z/my-project
FIX=fixtures/fnew259_probe
WORK=tmp/f259_build
rm -rf "$WORK"; mkdir -p "$WORK/obj" "$WORK/dex" "$WORK/apk"
AAPT2=tools/toolchain/aapt2
BOOT=tools/toolchain/android-34.jar
ECJ=tools/toolchain/ecj.jar
D8JAR=tools/toolchain/r8.jar
"$AAPT2" link -o "$WORK/apk/resources.apk" -I "$BOOT" \
  --manifest "$FIX/AndroidManifest.xml" --auto-add-overlay
javac_source="$FIX/src/com/probe/f259/MainActivity.java"
java -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" -cp "$BOOT" "$javac_source"
find "$WORK/obj" -name "*.class" > "$WORK/classes.txt"
java -cp "$D8JAR" com.android.tools.r8.D8 --release \
  --lib "$BOOT" --output "$WORK/dex" @"$WORK/classes.txt"
# repack: resources.apk + classes.dex (STORED for classes like aapt2 metadata lesson)
cp "$WORK/apk/resources.apk" run/w7/f259.apk
cd "$WORK/dex" && zip -j -X /home/z/my-project/run/w7/f259.apk classes.dex > /dev/null
echo "probe apk: $(sha256sum /home/z/my-project/run/w7/f259.apk | cut -c1-16)"
