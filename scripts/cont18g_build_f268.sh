#!/usr/bin/env bash
# cont18g_build_f268.sh — build fixtures/f268_exception_probe into run/cont18g/f268.apk
set -euo pipefail
cd /home/z/my-project
FIX=fixtures/f268_exception_probe
WORK=tmp/f268_build
OUT=run/cont18g
mkdir -p "$OUT" "$WORK/obj" "$WORK/dex" "$WORK/apk"
AAPT2=tools/toolchain/aapt2
BOOT=tools/toolchain/android-34.jar
ECJ=tools/toolchain/ecj.jar
D8JAR=tools/toolchain/r8.jar
"$AAPT2" link -o "$WORK/apk/resources.apk" -I "$BOOT" \
  --manifest "$FIX/AndroidManifest.xml" --auto-add-overlay
java -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" -cp "$BOOT" "$FIX/src/com/probe/f268/MainActivity.java"
find "$WORK/obj" -name "*.class" > "$WORK/classes.txt"
java -cp "$D8JAR" com.android.tools.r8.D8 --release \
  --lib "$BOOT" --output "$WORK/dex" @"$WORK/classes.txt"
cp "$WORK/apk/resources.apk" "$OUT/f268.apk"
cd "$WORK/dex" && zip -j -X "/home/z/my-project/$OUT/f268.apk" classes.dex > /dev/null
echo "f268 apk: $(sha256sum "/home/z/my-project/$OUT/f268.apk" | cut -c1-16)"
