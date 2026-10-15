#!/usr/bin/env bash
# s60_build_tsp.sh — build fixtures/theme_semantics_probe with the real toolchain
# (aapt2 link + ECJ 1.8 + D8), following the cont9_rebuild_gate_a_probe.sh recipe.
set -euo pipefail
ROOT=/home/z/my-project
FIX=$ROOT/fixtures/theme_semantics_probe
WORK=$ROOT/tmp/s60_tsp_build
AAPT2=$ROOT/tools/toolchain/aapt2
ECJ=$ROOT/tools/toolchain/ecj.jar
D8JAR=$ROOT/tools/toolchain/r8.jar
BOOT=$ROOT/tools/toolchain/android-34.jar
JAVA=${JAVA:-java}

rm -rf "$WORK"; mkdir -p "$WORK/gen" "$WORK/obj" "$WORK/apk"

"$AAPT2" compile --dir "$FIX/res" -o "$WORK/res.zip"
"$AAPT2" link -o "$WORK/apk/resources.apk" -I "$BOOT" \
  --manifest "$FIX/AndroidManifest.xml" --java "$WORK/gen" \
  --auto-add-overlay "$WORK/res.zip"

"$JAVA" -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" \
  -cp "$BOOT" "$WORK/gen/com/probe/tsp/R.java" "$FIX"/src/com/probe/tsp/*.java \
  2>&1 | grep -v "^$" | head -5 || true

"$JAVA" -jar "$D8JAR" --release --lib "$BOOT" --min-api 21 \
  --output "$WORK/apk" $(find "$WORK/obj" -name "*.class")

cd "$WORK/apk" && zip -q ../tsp.apk classes.dex
cd "$WORK/apk" && zip -qj ../tsp.apk resources.apk && cd "$WORK" || true
# resources.apk must merge INTO the root: use aapt2's output as the base and add dex
cp "$WORK/apk/resources.apk" "$ROOT/tsp_probe.apk"
(cd "$WORK/apk" && zip -q "$ROOT/tsp_probe.apk" classes.dex)
echo "tsp_probe.apk sha256: $(sha256sum "$ROOT/tsp_probe.apk" | cut -c1-16)"
