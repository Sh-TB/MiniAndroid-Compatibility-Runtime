#!/usr/bin/env bash
# cont122_build_probe.sh — build the CONT-122 UNPROVEN probe APK
# (real aapt2/ECJ/D8 toolchain; two DEXes so U16 exercises multi-dex
# enumeration: Companion lives in classes2.dex by construction).
set -euo pipefail
cd /home/z/my-project

AAPT2=tools/toolchain/aapt2
BOOT=tools/toolchain/android-34.jar
ECJ=tools/toolchain/ecj.jar
D8JAR=tools/toolchain/r8.jar

FIX=fixtures/cont123_zstate
MAN=$FIX/AndroidManifest.xml
OUT=run/c123/c123.apk
WORK=tmp/cont123_build

rm -rf "$WORK"; mkdir -p "$WORK/obj" "$WORK/dex1" "$WORK/dex2" "$WORK/gen" "$(dirname "$OUT")"
# aapt2 law: COMPILE then LINK (positional).
"$AAPT2" compile --dir "$FIX/res" -o "$WORK/res.zip"
"$AAPT2" link -o "$WORK/base.apk" -I "$BOOT" --manifest "$MAN" --java "$WORK/gen" \
  "$WORK/res.zip"
find "$FIX/src" "$WORK/gen" -name "*.java" > "$WORK/sources.txt"
java -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" -cp "$BOOT" @"$WORK/sources.txt"
# DEX 1: everything except Companion (the classes2 resident).
find "$WORK/obj" -name "*.class" > "$WORK/classes1.txt"
java -cp "$D8JAR" com.android.tools.r8.D8 --release \
  --lib "$BOOT" --output "$WORK/dex1" @"$WORK/classes1.txt" 2>"$WORK/d8_1.log" || {
    cat "$WORK/d8_1.log"; exit 1; }
# DEX 2: Companion alone — the multi-dex probe resident.
echo "$WORK/obj/com.probe.c123/Companion.class" > "$WORK/classes2.txt"
cp "$WORK/base.apk" "$OUT"
( cd "$WORK/dex1" && zip -j -q -X "/home/z/my-project/$OUT" classes.dex )


unzip -l "/home/z/my-project/$OUT" | grep -E "classes|sha" || true
echo "built $OUT: $(sha256sum "/home/z/my-project/$OUT" | cut -c1-16)"
