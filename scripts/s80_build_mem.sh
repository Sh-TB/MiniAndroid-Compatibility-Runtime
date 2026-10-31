#!/usr/bin/env bash
# s80_build_mem.sh — Memory Match (com.miniandroid.gmem), canonical
# aapt2/ECJ/D8 toolchain, same pipeline as s80_build_2048.sh.
set -euo pipefail
ROOT=/home/z/my-project
SRC=$ROOT/upload/s80_games/gmem
B=$ROOT/upload/s80_games/build_mem
TOOLS=${TOOLS:-$ROOT/tools}
PLAT_JAR=$TOOLS/android-34/android-34.jar
rm -rf "$B"; mkdir -p "$B"/{classes,dex}
cd "$B"
"$TOOLS/aapt2/aapt2" compile --dir "$SRC/res" -o res.zip
"$TOOLS/aapt2/aapt2" link -o base.apk -I "$PLAT_JAR" \
  --manifest "$SRC/AndroidManifest.xml" \
  --java rjava --min-sdk-version 19 --target-sdk-version 26 \
  --version-code 1 --version-name 1.0 res.zip
find "$SRC/java" rjava -name "*.java" > sources.txt
java -jar "$TOOLS/ecj/ecj.jar" -source 1.8 -target 1.8 -encoding UTF-8 \
  -cp "$PLAT_JAR" -d classes @sources.txt -nowarn -g
python3 - classes classes.jar <<'PY'
import sys, zipfile
from pathlib import Path
classes_dir, jar_path = Path(sys.argv[1]), Path(sys.argv[2])
files = sorted(p for p in classes_dir.rglob("*.class") if p.is_file())
with zipfile.ZipFile(jar_path, "w", zipfile.ZIP_DEFLATED) as z:
    for p in files:
        z.writestr(p.relative_to(classes_dir).as_posix(), p.read_bytes())
print(f"      jar entries: {len(files)}")
PY
java -cp "$TOOLS/d8/r8.jar" com.android.tools.r8.D8 \
  --release --lib "$PLAT_JAR" --output dex classes.jar
cp base.apk gmem_v1.0_vc1.apk
(cd dex && zip -q ../gmem_v1.0_vc1.apk classes.dex)
echo "APK: $B/gmem_v1.0_vc1.apk"
sha256sum "$B/gmem_v1.0_vc1.apk" | cut -c1-16
