#!/usr/bin/env bash
# cont50_build_probe.sh — build the F-NEW-324 probe (mLayoutParams
# slot identity + computeScroll receiver binding) with the real
# aapt2/ECJ/D8 toolchain (gate_a_probe recipe: res -> R.java + compiled
# layout).
set -euo pipefail
cd /home/z/my-project
FIX=fixtures/fnew324_probe
WORK=tmp/cont52_f324_build
OUT=run/cont52/fnew324_probe.apk
rm -rf "$WORK"; mkdir -p "$WORK/gen" "$WORK/obj" "$WORK/dex" "$WORK/apk"

AAPT2=tools/toolchain/aapt2
BOOT=tools/toolchain/android-34.jar
ECJ=tools/toolchain/ecj.jar
D8JAR=tools/toolchain/r8.jar

if [ -d "$FIX/res" ]; then
  "$AAPT2" compile --dir "$FIX/res" -o "$WORK/res.zip"
fi
RESARGS=""
[ -f "$WORK/res.zip" ] && RESARGS="$WORK/res.zip"
"$AAPT2" link -o "$WORK/apk/resources.apk" -I "$BOOT" \
  --manifest "$FIX/AndroidManifest.xml" --java "$WORK/gen" \
  --auto-add-overlay $RESARGS

find "$FIX/src" "$WORK/gen" -name "*.java" > "$WORK/sources.txt"
java -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" -cp "$BOOT" @"$WORK/sources.txt"

find "$WORK/obj" -name "*.class" > "$WORK/classes.txt"
java -cp "$D8JAR" com.android.tools.r8.D8 --release \
  --lib "$BOOT" --output "$WORK/dex" @"$WORK/classes.txt"

cp "$WORK/apk/resources.apk" "$OUT"
( cd "$WORK/dex" && zip -j -q -X "/home/z/my-project/$OUT" classes.dex )
echo "built $OUT: $(sha256sum "/home/z/my-project/$OUT" | cut -c1-16)"
