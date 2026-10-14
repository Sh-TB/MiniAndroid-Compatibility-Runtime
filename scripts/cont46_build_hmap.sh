#!/usr/bin/env bash
# cont46_build_hmap.sh — rebuild the Skill self-test's intake APK
# (fixtures/hmap_probe) lost to the container reset. Same recipe as
# cont11_build_probe.sh (real aapt2/ECJ/D8 toolchain).
set -euo pipefail
cd /home/z/my-project
FIX=fixtures/hmap_probe
WORK=tmp/cont46_hmap_build
OUT=hmap_probe.apk
mkdir -p "$WORK/obj" "$WORK/dex" "$WORK/apk"
AAPT2=tools/toolchain/aapt2
BOOT=tools/toolchain/android-34.jar
ECJ=tools/toolchain/ecj.jar
D8JAR=tools/toolchain/r8.jar

"$AAPT2" link -o "$WORK/apk/resources.apk" -I "$BOOT" \
  --manifest "$FIX/AndroidManifest.xml" --auto-add-overlay

SRCS=$(find "$FIX/src" -name "*.java")
java -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" -cp "$BOOT" $SRCS
find "$WORK/obj" -name "*.class" > "$WORK/classes.txt"
java -cp "$D8JAR" com.android.tools.r8.D8 --release \
  --lib "$BOOT" --output "$WORK/dex" @"$WORK/classes.txt"
cp "$WORK/apk/resources.apk" "$OUT"
cd "$WORK/dex" && zip -j -X "/home/z/my-project/$OUT" classes.dex > /dev/null
echo "hmap_probe.apk: $(sha256sum "/home/z/my-project/$OUT" | cut -c1-16)"
