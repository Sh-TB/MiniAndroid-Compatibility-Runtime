#!/bin/bash
# cont12_build_probe.sh — build fixtures/f266_probe into run/w8/f266.apk
set -euo pipefail
BASE=/home/z/my-project
FIX=$BASE/fixtures/f266_probe
WORK=$BASE/tmp/f266_build
OUT=$BASE/run/w8
mkdir -p "$OUT" "$WORK/obj" "$WORK/dex" "$WORK/apk"
AAPT2=$BASE/tools/toolchain/aapt2
BOOT=$BASE/tools/toolchain/android-34.jar
ECJ=$BASE/tools/toolchain/ecj.jar
D8JAR=$BASE/tools/toolchain/r8.jar
"$AAPT2" link -o "$WORK/apk/resources.apk" -I "$BOOT" \
  --manifest "$FIX/AndroidManifest.xml" --auto-add-overlay
java -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" -cp "$BOOT" "$FIX/src/com/probe/f266/MainActivity.java"
find "$WORK/obj" -name "*.class" > "$WORK/classes.txt"
java -cp "$D8JAR" com.android.tools.r8.D8 --release \
  --lib "$BOOT" --output "$WORK/dex" @"$WORK/classes.txt"
cp "$WORK/apk/resources.apk" "$OUT/f266.apk"
cd "$WORK/dex" && zip -j -X "$OUT/f266.apk" classes.dex > /dev/null
echo "f266 probe apk: $(sha256sum "$OUT/f266.apk" | cut -c1-16)"
