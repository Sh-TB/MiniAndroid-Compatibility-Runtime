#!/usr/bin/env bash
# cont138_build_f475.sh — build the R-NEW-018/019 Parcel probe fixture
# (real aapt2/ECJ/D8 toolchain).
set -euo pipefail
cd /home/z/my-project
FIX=miniandroid/tests/fixtures/fnew475_probe
WORK=tmp/cont138_f475_build
OUT=miniandroid/build/fixtures/fnew475_probe.apk
rm -rf "$WORK"; mkdir -p "$WORK/obj" "$WORK/dex" "$WORK/apk" miniandroid/build/fixtures
AAPT2=tools/toolchain/aapt2
BOOT=tools/toolchain/android-34.jar
ECJ=tools/toolchain/ecj.jar
D8JAR=tools/toolchain/r8.jar
"$AAPT2" link -o "$WORK/apk/resources.apk" -I "$BOOT" --manifest "$FIX/AndroidManifest.xml"
find "$FIX/src" -name "*.java" > "$WORK/src.txt"
java -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" -cp "$BOOT" @"$WORK/src.txt"
find "$WORK/obj" -name "*.class" > "$WORK/cls.txt"
java -cp "$D8JAR" com.android.tools.r8.D8 --release --lib "$BOOT" --output "$WORK/dex" @"$WORK/cls.txt"
cp "$WORK/apk/resources.apk" "$OUT"
( cd "$WORK/dex" && zip -j -q -X "/home/z/my-project/$OUT" classes.dex )
echo "built $OUT: $(sha256sum "/home/z/my-project/$OUT" | cut -c1-16)"
