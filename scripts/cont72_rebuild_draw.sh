#!/usr/bin/env bash
# cont72_rebuild_draw.sh — rebuild the frame-spread draw probe only.
set -euo pipefail
cd /home/z/my-project
AAPT2=tools/toolchain/aapt2
BOOT=tools/toolchain/android-34.jar
ECJ=tools/toolchain/ecj.jar
D8JAR=tools/toolchain/r8.jar
W=tmp/cont72_build_draw2
OUT=run/cont72/c72draw.apk
rm -rf "$W"; mkdir -p "$W/gen" "$W/obj" "$W/dex"
"$AAPT2" link -o "$W/base.apk" -I "$BOOT" \
  --manifest fixtures/cont72_draw_probe/AndroidManifest.xml --java "$W/gen"
find fixtures/cont72_draw_probe/src "$W/gen" -name "*.java" > "$W/sources.txt"
java -jar "$ECJ" -1.8 -nowarn -d "$W/obj" -cp "$BOOT" @"$W/sources.txt"
find "$W/obj" -name "*.class" > "$W/classes.txt"
java -cp "$D8JAR" com.android.tools.r8.D8 --release --lib "$BOOT" \
  --output "$W/dex" @"$W/classes.txt"
cp "$W/base.apk" "$OUT"
( cd "$W/dex" && zip -j -q -X "/home/z/my-project/$OUT" classes.dex )
echo "built $OUT: $(sha256sum "/home/z/my-project/$OUT" | cut -c1-16)"
