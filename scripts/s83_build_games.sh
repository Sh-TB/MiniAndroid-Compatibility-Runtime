#!/usr/bin/env bash
# s83_build_games.sh — rebuild the S80 game APKs (tetris + 2048) into
# upload/s83_games/ so the S83 campaign has every in-house game present.
# Canonical aapt2/ECJ/D8 toolchain (S72-W4 OPMT S65 recipe).
set -euo pipefail
ROOT=/home/z/my-project
TOOLS=${TOOLS:-/tmp/my-project/tools}
OUTB=$ROOT/upload/s83_games
mkdir -p "$OUTB"

build_game () {
  local name=$1 src=$2 out=$3
  local B=$OUTB/build_$name
  echo "=== building $name from $src -> $out"
  rm -rf "$B"; mkdir -p "$B"/{classes,dex}
  cd "$B"
  "$TOOLS/aapt2/aapt2" compile --dir "$src/res" -o res.zip
  "$TOOLS/aapt2/aapt2" link -o base.apk -I "$TOOLS/android-34.jar" \
    --manifest "$src/AndroidManifest.xml" \
    --java rjava --min-sdk-version 19 --target-sdk-version 26 \
    --version-code 1 --version-name 1.0 res.zip
  find "$src/java" rjava -name "*.java" > sources.txt
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
  cp base.apk "$out"
  (cd dex && zip -q ../"$out" classes.dex)
  sha256sum "$out"
}

build_game tetris "$ROOT/upload/s80_games/tetris" "tetris_v1.0_vc1.apk"
build_game g2048  "$ROOT/upload/s80_games/g2048"  "g2048_v1.0_vc1.apk"
echo "S83 GAME BUILDS COMPLETE"
