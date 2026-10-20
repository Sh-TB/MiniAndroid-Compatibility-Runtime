#!/usr/bin/env bash
# c114_build_f462.sh — build the F-NEW-462 ctor-calls-ctor receiver-binding
# probe (CONT-114): minimal libGDX-shaped fixture.
#
# Shape under test (from the tower3d F-NEW-462 decode):
#   AndroidGraphics-like: class Gfx (extends Object, has fields cfg/app)
#     Gfx.<init>: new ViewLike(ctx) [DEX class extending a FRAMEWORK class]
#                -> Gfx.cfg = cfg; Gfx.app = app   (field stores AFTER nested ctor)
#   ViewLike (app DEX class extends android.opengl.GLSurfaceView):
#     ViewLike.<init>: super(ctx) [framework shadow ctor] + framework-ish calls
#   Config: plain app class with a marker int.
#
# MainActivity builds Gfx, then prints C462 markers reading back cfg/app.
set -euo pipefail
cd /home/z/my-project

AAPT2=tools/toolchain/aapt2
BOOT=tools/toolchain/android-34.jar
ECJ=tools/toolchain/ecj.jar
D8JAR=tools/toolchain/r8.jar

FIX=fixtures/c114_f462_probe
MAN=$FIX/AndroidManifest.xml
OUT=run/c114/f462.apk
WORK=tmp/c114_build

rm -rf "$WORK"; mkdir -p "$WORK/obj" "$WORK/dex" "$WORK/gen" "$(dirname "$OUT")"
"$AAPT2" link -o "$WORK/base.apk" -I "$BOOT" --manifest "$MAN" --java "$WORK/gen"
find "$FIX/src" "$WORK/gen" -name "*.java" > "$WORK/sources.txt"
java -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" -cp "$BOOT" @"$WORK/sources.txt"
find "$WORK/obj" -name "*.class" > "$WORK/classes.txt"
java -cp "$D8JAR" com.android.tools.r8.D8 --release \
  --lib "$BOOT" --output "$WORK/dex" @"$WORK/classes.txt"
cp "$WORK/base.apk" "$OUT"
( cd "$WORK/dex" && zip -j -q -X "/home/z/my-project/$OUT" classes.dex )
echo "built $OUT: $(sha256sum "/home/z/my-project/$OUT" | cut -c1-16)"
