#!/usr/bin/env bash
# cont55_build_probe.sh — build the F-NEW-327 probe (the AOSP
# AttributeResolution def-style stages: xmlStyle/defStyleAttr/defStyleRes)
# with the real aapt2/ECJ/D8 toolchain (res: attrs + styles + theme).
set -euo pipefail
cd /home/z/my-project
FIX=fixtures/fnew327_probe
WORK=tmp/cont55_f327_build
OUT=run/cont55/fnew327_probe.apk
rm -rf "$WORK"; mkdir -p "$WORK/gen" "$WORK/obj" "$WORK/dex" "$WORK/apk"

AAPT2=tools/toolchain/aapt2
BOOT=tools/toolchain/android-34.jar
ECJ=tools/toolchain/ecj.jar
D8JAR=tools/toolchain/r8.jar

"$AAPT2" compile --dir "$FIX/res" -o "$WORK/res.zip"
"$AAPT2" link -o "$WORK/apk/resources.apk" -I "$BOOT" \
  --manifest "$FIX/AndroidManifest.xml" --java "$WORK/gen" \
  --auto-add-overlay "$WORK/res.zip"

find "$FIX/src" "$WORK/gen" -name "*.java" > "$WORK/sources.txt"
java -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" -cp "$BOOT" @"$WORK/sources.txt"

find "$WORK/obj" -name "*.class" > "$WORK/classes.txt"
java -cp "$D8JAR" com.android.tools.r8.D8 --release \
  --lib "$BOOT" --output "$WORK/dex" @"$WORK/classes.txt"

cp "$WORK/apk/resources.apk" "$OUT"
( cd "$WORK/dex" && zip -j -q -X "/home/z/my-project/$OUT" classes.dex )
echo "built $OUT: $(sha256sum "/home/z/my-project/$OUT" | cut -c1-16)"
