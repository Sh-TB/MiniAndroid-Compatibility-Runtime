#!/usr/bin/env bash
# cont69_build_llk.sh — build fixtures/linkedlist_probe with the real toolchain
# (aapt2 link + ECJ 1.8 + D8), following the s60_build_tsp.sh recipe
# (no res/ needed: plain Activity, no theme attributes).
set -euo pipefail
ROOT=/home/z/my-project
FIX=$ROOT/fixtures/linkedlist_probe
WORK=$ROOT/tmp/cont69_llk_build
AAPT2=$ROOT/tools/toolchain/aapt2
ECJ=$ROOT/tools/toolchain/ecj.jar
D8JAR=$ROOT/tools/toolchain/r8.jar
BOOT=$ROOT/tools/toolchain/android-34.jar
JAVA=${JAVA:-java}

rm -rf "$WORK"; mkdir -p "$WORK/obj" "$WORK/apk"

"$AAPT2" link -o "$WORK/apk/base.apk" -I "$BOOT" \
  --manifest "$FIX/AndroidManifest.xml"

"$JAVA" -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" \
  -cp "$BOOT" "$FIX"/src/com/probe/llk/*.java \
  2>&1 | grep -v "^$" | head -5 || true

find "$WORK/obj" -name "*.class" > "$WORK/classes.txt"
# NOTE: `java -jar r8.jar` hits the R8 main-class (silent no-output); the D8
# entrypoint must be named explicitly (cont9 recipe).
"$JAVA" -cp "$D8JAR" com.android.tools.r8.D8 --release \
  --lib "$BOOT" --output "$WORK/apk" @"$WORK/classes.txt"

cp "$WORK/apk/base.apk" "$ROOT/llk_probe.apk"
(cd "$WORK/apk" && zip -q "$ROOT/llk_probe.apk" classes.dex)
echo "llk_probe.apk sha256: $(sha256sum "$ROOT/llk_probe.apk" | cut -c1-16)"
