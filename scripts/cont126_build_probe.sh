#!/usr/bin/env bash
# cont126_build_probe.sh — CONT-126 Train 3: build the F-NEW-469
# interface-chain probe APK (real aapt2/ECJ/D8 toolchain).
set -euo pipefail
cd /home/z/my-project

AAPT2=tools/toolchain/aapt2
BOOT=tools/toolchain/android-34.jar
ECJ=tools/toolchain/ecj.jar
D8JAR=tools/toolchain/r8.jar

FIX=fixtures/cont124_iface_chain
OUT=run/c126/c124_iface_probe.apk
WORK=tmp/cont126_build

rm -rf "$WORK"; mkdir -p "$WORK/obj" "$WORK/dex1" "$(dirname "$OUT")"
"$AAPT2" compile --dir "$FIX/res" -o "$WORK/res.zip" 2>/dev/null || "$AAPT2" compile --dir "$FIX/res" -o "$WORK/res.zip"
"$AAPT2" link -o "$WORK/base.apk" -I "$BOOT" --manifest "$FIX/AndroidManifest.xml" "$WORK/res.zip"
find "$FIX/src" -name "*.java" > "$WORK/sources.txt"
java -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" -cp "$BOOT" @"$WORK/sources.txt"
find "$WORK/obj" -name "*.class" > "$WORK/classes1.txt"
java -cp "$D8JAR" com.android.tools.r8.D8 --release \
  --lib "$BOOT" --output "$WORK/dex1" @"$WORK/classes1.txt" 2>"$WORK/d8_1.log" || {
    cat "$WORK/d8_1.log"; exit 1; }
cp "$WORK/base.apk" "$OUT"
( cd "$WORK/dex1" && zip -j -q -X "/home/z/my-project/$OUT" classes.dex )
echo "built $OUT: $(sha256sum "/home/z/my-project/$OUT" | cut -c1-16)"
