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
#   3. packages the class tree into a deterministic classes.jar for D8
#      (D8 8.3.37 rejects bare directories; `$`-fragments never reach
#      the shell or the D8 CLI parser),
#   4. packages manifest + classes.dex (+ optional res/ assets) into
#      the APK,
#   5. prints the APK path and its SHA-256.
#
# REUSE-FIRST upgrade (aapt2 path): when <fixture_src_dir>/res exists,
# the REAL Android resource toolchain aapt2 (Google Maven,
# com.android.tools.build:aapt2:8.13.2-14304508, Apache-2.0) compiles
# res/ into real binary resources.arsc + binary AXML and generates
# R.java; the final APK is aapt2-LINKED (binary manifest +
# resources.arsc + res/**). Fixtures without res/ keep the legacy
# plain-manifest zip path. aapt2 zip entries carry a fixed 1980 epoch,
# and the repackage below pins its own entries to the same epoch, so
# fixture APKs are byte-deterministic across builds.
#
# Usage:
#   build_fixture_apk.sh <fixture_src_dir> <out_apk_path>
# <fixture_src_dir> must contain:
#   src/                   .java sources (any package layout)
#   AndroidManifest.xml    (plain-text; the aapt2 path compiles it to binary)
#   res/ (optional)        compiled+linked by aapt2 when present
#   assets/ (optional)     copied verbatim into the APK
#
# Toolchain: ECJ (MIT), D8 from r8.jar (Apache-2.0), AOSP android-34
# stubs (Apache-2.0), aapt2 (Apache-2.0, Google Maven). No Android SDK
# required. All paths quoted; TOOLS env var overrides the tool directory.
set -euo pipefail

SRC_DIR="$1"
OUT_APK="$2"
TOOLS="${TOOLS:-/home/z/my-project/tools}"

ECJ_JAR="$TOOLS/ecj/ecj.jar"
D8_JAR="$TOOLS/d8/r8.jar"
STUBS_JAR="$TOOLS/android-34.jar"
AAPT2="$TOOLS/aapt2/aapt2"

for f in "$SRC_DIR/AndroidManifest.xml" "$ECJ_JAR" "$D8_JAR" "$STUBS_JAR"; do
  if [ ! -e "$f" ]; then
    echo "build_fixture_apk: missing required input: $f" >&2
    exit 2
  fi
done

WORK="$(dirname "$OUT_APK")/.build_$(basename "$OUT_APK" .apk)"
rm -rf "$WORK"
mkdir -p "$WORK/classes" "$WORK/dex"

# ── [1] resources (aapt2 path, only when res/ exists) ─────────────────
BASE_APK=""
RJAVA_ARGS=()
if [ -d "$SRC_DIR/res" ]; then
  if [ ! -x "$AAPT2" ]; then
    echo "build_fixture_apk: res/ present but aapt2 missing at $AAPT2" >&2
    exit 2
  fi
  echo "[1/4] aapt2 compile res/"
  "$AAPT2" compile --dir "$SRC_DIR/res" -o "$WORK/res.zip"
  echo "[1/4] aapt2 link (binary manifest + resources.arsc + R.java)"
  mkdir -p "$WORK/rjava"
  # --min-sdk-version 24 pins config selection so aapt2 emits exactly one
  # res/layout variant (no -vNN version splits) for simple fixtures.
  "$AAPT2" link \
      -o "$WORK/base.apk" \
      -I "$STUBS_JAR" \
      --manifest "$SRC_DIR/AndroidManifest.xml" \
      --min-sdk-version 24 \
      --java "$WORK/rjava" \
      "$WORK/res.zip"
  BASE_APK="$WORK/base.apk"
  # R.java joins the compile set so R.layout/R.id/R.string constants in
  # app code match the aapt2-assigned resource IDs exactly.
  RJAVA_ARGS=(-sourcepath "$WORK/rjava")
else
  echo "[1/4] resources: none (plain zip path)"
fi

echo "[2/4] ECJ compile"
# -proc:none keeps the build deterministic (no annotation processors).
mapfile -d '' JAVA_FILES < <(find "$SRC_DIR/src" -name '*.java' -print0)
if [ "${#JAVA_FILES[@]}" -eq 0 ]; then
  echo "build_fixture_apk: no .java sources under $SRC_DIR/src" >&2
  exit 2
fi
if ! java -jar "$ECJ_JAR" \
    -source 8 -target 8 -proc:none \
    -bootclasspath "$STUBS_JAR" \
    "${RJAVA_ARGS[@]}" \
    -d "$WORK/classes" \
    "${JAVA_FILES[@]}"; then
  echo "build_fixture_apk: ECJ compile FAILED" >&2
  exit 3
fi

echo "[3/4] D8 dex (inner-class-safe class collection)"
mapfile -d '' CLASS_FILES < <(find "$WORK/classes" -name '*.class' -print0)
if [ "${#CLASS_FILES[@]}" -eq 0 ]; then
  echo "build_fixture_apk: ECJ produced no .class files" >&2
  exit 3
fi
echo "      class files: ${#CLASS_FILES[@]}"
# D8 8.3.37 rejects bare directories as program input, and individual
# `Outer$Inner.class` paths are shell-hostile. Package the class tree into
# a deterministic .jar first — entry names live INSIDE the archive, so no
# `$`-fragment can ever reach the shell or the D8 CLI parser.
CLASSES_JAR="$WORK/classes.jar"
python3 - "$WORK/classes" "$CLASSES_JAR" <<'PY'
import sys, zipfile
from pathlib import Path
classes_dir, jar_path = Path(sys.argv[1]), sys.argv[2]
files = sorted(p for p in classes_dir.rglob("*.class") if p.is_file())
with zipfile.ZipFile(jar_path, "w", zipfile.ZIP_DEFLATED) as z:
    for p in files:
        z.writestr(p.relative_to(classes_dir).as_posix(), p.read_bytes())
print(f"      jar entries: {len(files)}")
PY
# Assert the dex exists afterwards.
if ! java -cp "$D8_JAR" com.android.tools.r8.D8 \
    --release \
    --lib "$STUBS_JAR" \
    --output "$WORK/dex" \
    "$CLASSES_JAR"; then
  echo "build_fixture_apk: D8 dex FAILED" >&2
  exit 3
fi
if [ ! -s "$WORK/dex/classes.dex" ]; then
  echo "build_fixture_apk: classes.dex missing/empty" >&2
  exit 3
fi

echo "[4/4] APK package"
python3 - "$SRC_DIR" "$WORK" "$OUT_APK" "$BASE_APK" <<'PY'
import hashlib, sys, zipfile
from pathlib import Path

src_dir, work, out_apk, base_apk = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
src_dir, out_apk = Path(src_dir), Path(out_apk)
out_apk.parent.mkdir(parents=True, exist_ok=True)

# Deterministic zip: fixed 1980 epoch (matches aapt2's own convention).
def put(z, name, data):
    zi = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    zi.compress_type = zipfile.ZIP_DEFLATED
    z.writestr(zi, data)

entries = []
if base_apk:
    # REAL aapt2-linked APK: binary manifest + resources.arsc + binary
    # res/**. Only classes.dex is added on top.
    with zipfile.ZipFile(base_apk) as b:
        for n in b.namelist():
            entries.append((n, b.read(n)))
    entries.append(("classes.dex", (Path(work) / "dex" / "classes.dex").read_bytes()))
else:
    entries.append(("AndroidManifest.xml",
                    (src_dir / "AndroidManifest.xml").read_bytes()))
    entries.append(("classes.dex", (Path(work) / "dex" / "classes.dex").read_bytes()))
    for sub in ("res", "assets"):
        d = src_dir / sub
        if d.is_dir():
            for p in sorted(d.rglob("*")):
                if p.is_file():
                    entries.append((p.relative_to(src_dir).as_posix(), p.read_bytes()))

with zipfile.ZipFile(out_apk, "w", zipfile.ZIP_DEFLATED) as z:
    for name, data in entries:
        put(z, name, data)

h = hashlib.sha256(out_apk.read_bytes()).hexdigest()
print("APK:", out_apk)
print("SHA256:", h)
print("entries:", len(entries))
if base_apk:
    print("aapt2: linked (binary manifest + resources.arsc)")
PY

echo "[4/4] done"
