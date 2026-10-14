#!/usr/bin/env bash
# cont65_build_probe.sh — build fixtures/capaudit_probe into run/cont65/capaudit.apk
# (real aapt2/ECJ/D8 toolchain; same harness as cont62_build_probe.sh)
set -euo pipefail
cd /home/z/my-project
FIX=fixtures/capaudit_probe
WORK=tmp/capaudit_build
OUT=run/cont65
mkdir -p "$WORK/obj" "$WORK/dex" "$WORK/apk" "$OUT"
AAPT2=tools/toolchain/aapt2
BOOT=tools/toolchain/android-34.jar
ECJ=tools/toolchain/ecj.jar
D8JAR=tools/toolchain/r8.jar
"$AAPT2" compile --dir "$FIX/res" -o "$WORK/res.zip"
"$AAPT2" link -o "$WORK/apk/resources.apk" -I "$BOOT" \
  --manifest "$FIX/AndroidManifest.xml" --auto-add-overlay \
  --java "$WORK/gen" "$WORK/res.zip" \
  -A "$FIX/assets"
java -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" -cp "$BOOT" \
  "$WORK/gen/com/probe/capaudit/R.java" \
  "$FIX/src/com/probe/capaudit/MainActivity.java"
find "$WORK/obj" -name "*.class" > "$WORK/classes.txt"
java -cp "$D8JAR" com.android.tools.r8.D8 --release \
  --lib "$BOOT" --output "$WORK/dex" @"$WORK/classes.txt"
cp "$WORK/apk/resources.apk" "$OUT/capaudit.apk"
cd "$WORK/dex" && zip -j -X "/home/z/my-project/$OUT/capaudit.apk" classes.dex > /dev/null
echo "probe apk: $(sha256sum /home/z/my-project/$OUT/capaudit.apk | cut -c1-16)"
