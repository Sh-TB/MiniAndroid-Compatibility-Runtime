#!/usr/bin/env bash
# s141_train44_simple_browser.sh — build games/simple-browser (S133 VC2)
# with the canonical pipeline into run/s141/simple_browser.apk.
set -euo pipefail
cd /home/z/my-project
FIX=games/simple-browser
WORK=tmp/simple_browser_build
rm -rf "$WORK"; mkdir -p "$WORK/obj" "$WORK/dex" "$WORK/apk" "$WORK/gen" run/s141
AAPT2=tools/toolchain/aapt2
BOOT=tools/toolchain/android-34.jar
ECJ=tools/toolchain/ecj.jar
D8JAR=tools/toolchain/r8.jar
"$AAPT2" compile --dir "$FIX/res" -o "$WORK/res.zip"
"$AAPT2" link -o "$WORK/apk/resources.apk" -I "$BOOT" \
  --manifest "$FIX/AndroidManifest.xml" \
  "$WORK/res.zip" --auto-add-overlay \
  --java "$WORK/gen"
find "$FIX/java" -name "*.java" > "$WORK/sources.txt"
find "$WORK/gen" -name "*.java" >> "$WORK/sources.txt"
java -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" -cp "$BOOT" @"$WORK/sources.txt"
find "$WORK/obj" -name "*.class" > "$WORK/classes.txt"
java -cp "$D8JAR" com.android.tools.r8.D8 --release \
  --lib "$BOOT" --output "$WORK/dex" @"$WORK/classes.txt"
cp "$WORK/apk/resources.apk" run/s141/simple_browser.apk
cd "$WORK/dex" && zip -j -X /home/z/my-project/run/s141/simple_browser.apk classes.dex > /dev/null
echo "simple_browser apk: $(sha256sum /home/z/my-project/run/s141/simple_browser.apk | cut -c1-16)"
