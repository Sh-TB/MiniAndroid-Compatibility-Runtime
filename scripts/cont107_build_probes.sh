#!/usr/bin/env bash
# cont107_build_probes.sh — build CONT-107 probes (real aapt2/ECJ/D8).
set -euo pipefail
cd /home/z/my-project

AAPT2=tools/toolchain/aapt2
BOOT=tools/toolchain/android-34.jar
ECJ=tools/toolchain/ecj.jar
D8JAR=tools/toolchain/r8.jar

build_one() { # fix_dir pkg out_apk [res_dir]
  local FIX=$1 PKG=$2 OUT=$3 RES=${4:-}
  local MAN=$FIX/AndroidManifest.xml
  local WORK=tmp/cont107_build_$PKG
  rm -rf "$WORK"; mkdir -p "$WORK/obj" "$WORK/dex" "$WORK/gen" "$(dirname "$OUT")"
  if [ -n "$RES" ]; then
    "$AAPT2" compile --dir "$RES" -o "$WORK/res.zip"
    "$AAPT2" link -o "$WORK/base.apk" -I "$BOOT" --manifest "$MAN" --java "$WORK/gen" "$WORK/res.zip"
  else
    "$AAPT2" link -o "$WORK/base.apk" -I "$BOOT" --manifest "$MAN" --java "$WORK/gen"
  fi
  find "$FIX/src" "$WORK/gen" -name "*.java" > "$WORK/sources.txt"
  java -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" -cp "$BOOT" @"$WORK/sources.txt"
  find "$WORK/obj" -name "*.class" > "$WORK/classes.txt"
  java -cp "$D8JAR" com.android.tools.r8.D8 --release \
    --lib "$BOOT" --output "$WORK/dex" @"$WORK/classes.txt"
  cp "$WORK/base.apk" "$OUT"
  ( cd "$WORK/dex" && zip -j -q -X "/home/z/my-project/$OUT" classes.dex )
  echo "built $OUT: $(sha256sum "/home/z/my-project/$OUT" | cut -c1-16)"
}

build_one fixtures/cont107_toolbarmeasure com.probe.c106b2 run/c107/c106b2.apk fixtures/cont107_toolbarmeasure/res
build_one fixtures/cont107_reflectcount  com.probe.c106b  run/c107/c106b.apk
