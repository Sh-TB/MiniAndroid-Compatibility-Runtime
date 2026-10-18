#!/usr/bin/env bash
# cont99_btn_build_probe.sh — build the CONT-99 T4 button hitbox/state probe
# (real aapt2/ECJ/D8 toolchain; same chain as cont98_build_probe.sh).
set -euo pipefail
cd /home/z/my-project

AAPT2=tools/toolchain/aapt2
BOOT=tools/toolchain/android-34.jar
ECJ=tools/toolchain/ecj.jar
D8JAR=tools/toolchain/r8.jar

FIX=fixtures/cont99_btn_probe
MAN=$FIX/AndroidManifest.xml
OUT=run/cont99/c99btn.apk
WORK=tmp/cont99_btn_build

rm -rf "$WORK"; mkdir -p "$WORK/obj" "$WORK/dex" "$WORK/gen" "$(dirname "$OUT")"
"$AAPT2" link -o "$WORK/base.apk" -I "$BOOT" --manifest "$MAN" --java "$WORK/gen"
find "$FIX/src" "$WORK/gen" -name "*.java" > "$WORK/sources.txt"
java -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" -cp "$BOOT" @"$WORK/sources.txt"
find "$WORK/obj" -name "*.class" > "$WORK/classes.txt"
java -cp "$D8JAR" com.android.tools.r8.D8 --release \
  --lib "$BOOT" --output "$WORK/dex" @"$WORK/classes.txt"
cp "$WORK/base.apk" "$OUT"
( cd "$WORK/dex" && zip -j -q -X "/home/z/my-project/$OUT" classes.dex )
echo "built $OUT: $(sha256sum "/home/z/my-project/$OUT" | cut -c1-16)"
