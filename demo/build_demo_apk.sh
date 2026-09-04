#!/usr/bin/env bash
# build_demo_apk.sh — build the MiniAndroid execution-proof demo APK.
#
# Toolchain (all official open-source releases, no Android SDK required):
#   1. ECJ  (Eclipse Compiler for Java, MIT)  -> .class from .java
#   2. D8   (Google R8/D8 dexer, AOSP)        -> classes.dex from .class
#   3. Python zipfile                     -> APK (manifest + classes.dex)
#
# The manifest is PLAIN TEXT XML: MiniAndroid's manifest_reader parses both
# binary AXML and plain XML, and this app uses no compiled resources.
set -euo pipefail

# Tool locations can be overridden via the TOOLS env var; the defaults match
# the layout used by the project tooling. TOOLS must contain:
#   ecj/ecj.jar        (Eclipse Compiler for Java, EPL-2.0)
#   d8/r8.jar          (Google D8 dexer, Apache-2.0)
#   android-34.jar     (AOSP platform stubs, Apache-2.0)
DEMO_DIR="$(cd "$(dirname "$0")" && pwd)"
OUT_DIR="$DEMO_DIR/build"
TOOLS="${TOOLS:-/home/z/my-project/tools}"

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR/classes" "$OUT_DIR/dex"

echo "[1/3] ECJ compile"
java -jar "$TOOLS/ecj/ecj.jar" \
  -source 8 -target 8 \
  -bootclasspath "$TOOLS/android-34.jar" \
  -d "$OUT_DIR/classes" \
  "$DEMO_DIR/src/com/miniandroid/demo/MainActivity.java" || true

echo "[2/3] D8 dex"
java -cp "$TOOLS/d8/r8.jar" com.android.tools.r8.D8 \
  --release \
  --lib "$TOOLS/android-34.jar" \
  --output "$OUT_DIR/dex" \
  $(find "$OUT_DIR/classes" -name '*.class')

echo "[3/3] APK package"
python3 - "$OUT_DIR" <<'PY'
import sys, zipfile, hashlib, os
out = sys.argv[1]
apk = os.path.join(out, "miniandroid-demo.apk")
with zipfile.ZipFile(apk, "w", zipfile.ZIP_DEFLATED) as z:
    z.write("/home/z/my-project/ws/demo/AndroidManifest.xml", "AndroidManifest.xml")
    z.write(os.path.join(out, "dex/classes.dex"), "classes.dex")
h = hashlib.sha256(open(apk, "rb").read()).hexdigest()
print("APK:", apk)
print("SHA256:", h)
PY
