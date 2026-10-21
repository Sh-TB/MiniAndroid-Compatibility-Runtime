#!/usr/bin/env bash
# cont137_build_f474.sh — build the R-NEW-133 InMemoryDexClassLoader probe
# fixture (real aapt2/ECJ/D8 toolchain; payload dex compiled separately by
# D8 and embedded as a hex string in MainActivity source).
set -euo pipefail
cd /home/z/my-project
FIX=miniandroid/tests/fixtures/fnew474_probe
WORK=tmp/cont137_f474_build
OUT=miniandroid/build/fixtures/fnew474_probe.apk
mkdir -p "$WORK/gen" "$WORK/obj" "$WORK/dex" "$WORK/apk" miniandroid/build/fixtures

AAPT2=tools/toolchain/aapt2
BOOT=tools/toolchain/android-34.jar
ECJ=tools/toolchain/ecj.jar
D8JAR=tools/toolchain/r8.jar

# ── 1) payload dex (secondary image) ──
find "$FIX/payload_src" -name "*.java" > "$WORK/psrc.txt"
java -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" -cp "$BOOT" @"$WORK/psrc.txt"
find "$WORK/obj" -name "*.class" > "$WORK/pcls.txt"
rm -rf "$WORK/pdex" && mkdir -p "$WORK/pdex"
java -cp "$D8JAR" com.android.tools.r8.D8 --release --lib "$BOOT" \
  --output "$WORK/pdex" @"$WORK/pcls.txt"
cp "$WORK/pdex/classes.dex" "$WORK/payload.dex"
PAYLOAD_HEX=$(od -An -v -tx1 "$WORK/payload.dex" | tr -d ' \n')
echo "payload.dex: $(sha256sum "$WORK/payload.dex" | cut -c1-16) bytes=$(stat -c%s "$WORK/payload.dex")"

# ── 2) main fixture APK with the hex embedded ──
sed "s/@@PAYLOAD_HEX@@/$PAYLOAD_HEX/" "$FIX/MainActivity.java" > "$WORK/gen/MainActivity.java"
"$AAPT2" link -o "$WORK/apk/resources.apk" -I "$BOOT" \
  --manifest "$FIX/AndroidManifest.xml" --java "$WORK/gen2" 2>/dev/null || \
"$AAPT2" link -o "$WORK/apk/resources.apk" -I "$BOOT" \
  --manifest "$FIX/AndroidManifest.xml"
find "$WORK/gen" -name "*.java" > "$WORK/msrc.txt"
java -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj2" -cp "$BOOT" @"$WORK/msrc.txt"
find "$WORK/obj2" -name "*.class" > "$WORK/mcls.txt"
java -cp "$D8JAR" com.android.tools.r8.D8 --release --lib "$BOOT" \
  --output "$WORK/dex" @"$WORK/mcls.txt"
cp "$WORK/apk/resources.apk" "$OUT"
( cd "$WORK/dex" && zip -j -q -X "/home/z/my-project/$OUT" classes.dex )
echo "built $OUT: $(sha256sum "/home/z/my-project/$OUT" | cut -c1-16)"
