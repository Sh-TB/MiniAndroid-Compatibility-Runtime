#!/usr/bin/env bash
# s98_build_snakeneon.sh — build Snake Neon (com.miniandroid.snakeneon) with
# the canonical aapt2/ECJ/D8 toolchain (S80 recipe; GAMES-4 NEW content).
set -euo pipefail
ROOT=/home/z/my-project
SRC=$ROOT/games/snake-neon
B=$ROOT/upload/s98_games/build_snakeneon
TOOLS=${TOOLS:-$ROOT/tools}

rm -rf "$B"; mkdir -p "$B"/{classes,dex}
cd "$B"

"$TOOLS/aapt2/aapt2" compile --dir "$SRC/res" -o res.zip
"$TOOLS/aapt2/aapt2" link -o base.apk -I "$TOOLS/android-34.jar" \
  --manifest "$SRC/AndroidManifest.xml" \
  --java rjava --min-sdk-version 19 --target-sdk-version 26 \
  --version-code 1 --version-name 1.0 res.zip

find "$SRC/java" rjava -name "*.java" > sources.txt
wc -l sources.txt
java -jar "$TOOLS/ecj/ecj.jar" -source 1.8 -target 1.8 -encoding UTF-8 \
  -cp "$TOOLS/android-34.jar" -d classes @sources.txt -nowarn -g

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
  --release --lib "$TOOLS/android-34.jar" --output dex classes.jar
ls -la dex/

cp base.apk snakeneon_v1.0_vc1.apk
(cd dex && zip -q ../snakeneon_v1.0_vc1.apk classes.dex)
sha256sum snakeneon_v1.0_vc1.apk
unzip -l snakeneon_v1.0_vc1.apk | tail -5
echo "BUILD COMPLETE: $B/snakeneon_v1.0_vc1.apk"
