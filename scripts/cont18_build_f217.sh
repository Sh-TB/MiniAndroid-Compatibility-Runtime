#!/usr/bin/env bash
# CONT-18: build fixtures/f217_mutex_probe into run/w7/f217.apk
set -euo pipefail
cd /home/z/my-project
FIX=fixtures/f217_mutex_probe
WORK=tmp/f217_build
OUT=run/w7
mkdir -p "$OUT" "$WORK/obj" "$WORK/dex" "$WORK/apk"
AAPT2=tools/toolchain/aapt2
BOOT=tools/toolchain/android-34.jar
ECJ=tools/toolchain/ecj.jar
D8JAR=tools/toolchain/r8.jar
"$AAPT2" link -o "$WORK/apk/resources.apk" -I "$BOOT" \
  --manifest "$FIX/AndroidManifest.xml" --auto-add-overlay
javac_source="$FIX/src/com/probe/f217/MainActivity.java"
java -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" -cp "$BOOT" "$javac_source"
find "$WORK/obj" -name "*.class" > "$WORK/classes.txt"
java -cp "$D8JAR" com.android.tools.r8.D8 --release \
  --lib "$BOOT" --output "$WORK/dex" @"$WORK/classes.txt"
cp "$WORK/apk/resources.apk" "$OUT/f217.apk"
cd "$WORK/dex" && zip -j -X "/home/z/my-project/$OUT/f217.apk" classes.dex > /dev/null
echo "f217 apk: $(sha256sum "/home/z/my-project/$OUT/f217.apk" | cut -c1-16)"
