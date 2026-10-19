#!/usr/bin/env bash
# cont112_build_probe.sh — build the CONT-112 F-NEW-454/455 law-deref probe
# (real aapt2/ECJ/D8 toolchain, same shape as cont111_build_probe.sh).
set -euo pipefail
cd /home/z/my-project

AAPT2=tools/toolchain/aapt2
BOOT=tools/toolchain/android-34.jar
ECJ=tools/toolchain/ecj.jar
D8JAR=tools/toolchain/r8.jar

FIX=fixtures/cont112_lawderef
MAN=$FIX/AndroidManifest.xml
OUT=run/c112/c449.apk
WORK=tmp/cont112_build

rm -rf "$WORK"; mkdir -p "$WORK/obj" "$WORK/dex" "$WORK/gen" "$(dirname "$OUT")"
# aapt2 law: resources COMPILE first (.flat zip), then LINK (positional).
"$AAPT2" compile --dir "$FIX/res" -o "$WORK/res.zip"
"$AAPT2" link -o "$WORK/base.apk" -I "$BOOT" --manifest "$MAN" --java "$WORK/gen" \
  "$WORK/res.zip"
find "$FIX/src" "$WORK/gen" -name "*.java" > "$WORK/sources.txt"
java -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" -cp "$BOOT" @"$WORK/sources.txt"
find "$WORK/obj" -name "*.class" > "$WORK/classes.txt"
java -cp "$D8JAR" com.android.tools.r8.D8 --release \
  --lib "$BOOT" --output "$WORK/dex" @"$WORK/classes.txt"
cp "$WORK/base.apk" "$OUT"
( cd "$WORK/dex" && zip -j -q -X "/home/z/my-project/$OUT" classes.dex )
echo "built $OUT: $(sha256sum "/home/z/my-project/$OUT" | cut -c1-16)"
