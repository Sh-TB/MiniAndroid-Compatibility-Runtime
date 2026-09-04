#!/usr/bin/env bash
# build_fixture_apk.sh — generic, inner-class-safe fixture APK builder.
#
# Why this exists: the previous one-off fixture build commands piped
# $(find ...) into word-splitting contexts. Fixture sources with INNER
# CLASSES produce class files like `MainActivity$PathView.class`; the
# `$PathView` fragment is a shell parameter expansion, so unquoted
# use silently mangled the class list (and `$1`-style names vanished).
# This script:
#   1. fails loudly when ECJ reports errors (no `|| true`),
#   2. collects class files via find -print0 + mapfile (NUL-safe),
#   3. passes the classes DIRECTORY to D8 so no filename is ever
#      re-parsed by the shell,
#   4. packages manifest + classes.dex (+ optional res/ assets) into
#      the APK,
#   5. prints the APK path and its SHA-256.
#
# Usage:
#   build_fixture_apk.sh <fixture_src_dir> <out_apk_path>
# <fixture_src_dir> must contain:
#   src/                   .java sources (any package layout)
#   AndroidManifest.xml    (plain-text or binary AXML; MiniAndroid reads both)
#   res/ (optional)        copied verbatim into the APK
#   assets/ (optional)     copied verbatim into the APK
#
# Toolchain: ECJ (MIT), D8 from r8.jar (Apache-2.0), AOSP android-34
# stubs (Apache-2.0). No Android SDK required. All paths quoted; TOOLS
# env var overrides the tool directory.
set -euo pipefail

SRC_DIR="$1"
OUT_APK="$2"
TOOLS="${TOOLS:-/home/z/my-project/tools}"

ECJ_JAR="$TOOLS/ecj/ecj.jar"
D8_JAR="$TOOLS/d8/r8.jar"
STUBS_JAR="$TOOLS/android-34.jar"

for f in "$SRC_DIR/AndroidManifest.xml" "$ECJ_JAR" "$D8_JAR" "$STUBS_JAR"; do
  if [ ! -e "$f" ]; then
    echo "build_fixture_apk: missing required input: $f" >&2
    exit 2
  fi
done

WORK="$(dirname "$OUT_APK")/.build_$(basename "$OUT_APK" .apk)"
rm -rf "$WORK"
mkdir -p "$WORK/classes" "$WORK/dex"

echo "[1/4] ECJ compile"
# -proc:none keeps the build deterministic (no annotation processors).
mapfile -d '' JAVA_FILES < <(find "$SRC_DIR/src" -name '*.java' -print0)
if [ "${#JAVA_FILES[@]}" -eq 0 ]; then
  echo "build_fixture_apk: no .java sources under $SRC_DIR/src" >&2
  exit 2
fi
if ! java -jar "$ECJ_JAR" \
    -source 8 -target 8 -proc:none \
    -bootclasspath "$STUBS_JAR" \
    -d "$WORK/classes" \
    "${JAVA_FILES[@]}"; then
  echo "build_fixture_apk: ECJ compile FAILED" >&2
  exit 3
fi

echo "[2/4] D8 dex (inner-class-safe class collection)"
mapfile -d '' CLASS_FILES < <(find "$WORK/classes" -name '*.class' -print0)
if [ "${#CLASS_FILES[@]}" -eq 0 ]; then
  echo "build_fixture_apk: ECJ produced no .class files" >&2
  exit 3
fi
echo "      class files: ${#CLASS_FILES[@]}"
# D8 accepts a directory of classes, which sidesteps shell quoting of
# `Outer$Inner.class` names entirely. Assert the dex exists afterwards.
if ! java -cp "$D8_JAR" com.android.tools.r8.D8 \
    --release \
    --lib "$STUBS_JAR" \
    --output "$WORK/dex" \
    "$WORK/classes"; then
  echo "build_fixture_apk: D8 dex FAILED" >&2
  exit 3
fi
if [ ! -s "$WORK/dex/classes.dex" ]; then
  echo "build_fixture_apk: classes.dex missing/empty" >&2
  exit 3
fi

echo "[3/4] APK package"
python3 - "$SRC_DIR" "$WORK" "$OUT_APK" <<'PY'
import hashlib, sys, zipfile
from pathlib import Path

src_dir, work, out_apk = sys.argv[1], sys.argv[2], sys.argv[3]
src_dir, out_apk = Path(src_dir), Path(out_apk)
out_apk.parent.mkdir(parents=True, exist_ok=True)

entries = [("AndroidManifest.xml", (src_dir / "AndroidManifest.xml").read_bytes()),
           ("classes.dex", (Path(work) / "dex" / "classes.dex").read_bytes())]

for sub in ("res", "assets"):
    d = src_dir / sub
    if d.is_dir():
        for p in sorted(d.rglob("*")):
            if p.is_file():
                entries.append((p.relative_to(src_dir).as_posix(), p.read_bytes()))

with zipfile.ZipFile(out_apk, "w", zipfile.ZIP_DEFLATED) as z:
    for name, data in entries:
        z.writestr(name, data)

h = hashlib.sha256(out_apk.read_bytes()).hexdigest()
print("APK:", out_apk)
print("SHA256:", h)
print("entries:", len(entries))
PY

echo "[4/4] done"
