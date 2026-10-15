#!/usr/bin/env bash
# cont70_build_font.sh — build fixtures/font_probe with the real toolchain
# (aapt2 link + ECJ 1.8 + D8; assets added into the linked APK).
set -euo pipefail
ROOT=/home/z/my-project
FIX=$ROOT/fixtures/font_probe
WORK=$ROOT/tmp/cont70_font_build
AAPT2=$ROOT/tools/toolchain/aapt2
ECJ=$ROOT/tools/toolchain/ecj.jar
D8JAR=$ROOT/tools/toolchain/r8.jar
BOOT=$ROOT/tools/toolchain/android-34.jar
JAVA=${JAVA:-java}

rm -rf "$WORK"; mkdir -p "$WORK/obj" "$WORK/apk"

"$AAPT2" link -o "$WORK/apk/base.apk" -I "$BOOT" -A "$FIX/assets" \
  --manifest "$FIX/AndroidManifest.xml"

"$JAVA" -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" \
  -cp "$BOOT" "$FIX"/src/com/probe/font/*.java \
  2>&1 | grep -v "^$" | head -5 || true

find "$WORK/obj" -name "*.class" > "$WORK/classes.txt"
"$JAVA" -cp "$D8JAR" com.android.tools.r8.D8 --release \
  --lib "$BOOT" --output "$WORK/apk" @"$WORK/classes.txt"

cp "$WORK/apk/base.apk" "$ROOT/font_probe.apk"
(cd "$WORK/apk" && zip -q "$ROOT/font_probe.apk" classes.dex)
echo "font_probe.apk sha256: $(sha256sum "$ROOT/font_probe.apk" | cut -c1-16)"
