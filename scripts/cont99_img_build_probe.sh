#!/usr/bin/env bash
# cont99_img_build_probe.sh — build the CONT-99 T3 ImageView/scaleType probe
# (real aapt2 compile+link with resources, ECJ, D8; deterministic PNG assets
# generated with zlib so the pixel oracle is reproducible).
set -euo pipefail
cd /home/z/my-project

AAPT2=tools/toolchain/aapt2
BOOT=tools/toolchain/android-34.jar
ECJ=tools/toolchain/ecj.jar
D8JAR=tools/toolchain/r8.jar

FIX=fixtures/cont99_img_probe
MAN=$FIX/AndroidManifest.xml
OUT=run/cont99/c99im.apk
WORK=tmp/cont99_img_build

# ── deterministic solid-color PNGs (zlib, no PIL) ──
python3 - << 'PYEOF'
import zlib, struct, os
def png(path, w, h, rgba):
    raw = b''.join(b'\x00' + bytes(rgba) * w for _ in range(h))
    def chunk(t, d):
        c = t + d
        return struct.pack('>I', len(d)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)
    ihdr = struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)
    data = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr)
            + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))
    with open(path, 'wb') as f:
        f.write(data)
base = 'fixtures/cont99_img_probe/res/drawable-nodpi'
os.makedirs(base, exist_ok=True)
png(f'{base}/red_land.png', 200, 100, (0xCC, 0x22, 0x22, 0xFF))
png(f'{base}/blue_port.png', 100, 200, (0x22, 0x22, 0xCC, 0xFF))
png(f'{base}/green_sq.png', 100, 100, (0x22, 0xCC, 0x22, 0xFF))
print('assets: red_land 200x100, blue_port 100x200, green_sq 100x100')
PYEOF

rm -rf "$WORK"; mkdir -p "$WORK/obj" "$WORK/dex" "$WORK/gen" "$(dirname "$OUT")"
"$AAPT2" compile --dir "$FIX/res" -o "$WORK/res.zip"
"$AAPT2" link -o "$WORK/base.apk" -I "$BOOT" --manifest "$MAN" \
  --java "$WORK/gen" "$WORK/res.zip" --auto-add-overlay
find "$FIX/src" "$WORK/gen" -name "*.java" > "$WORK/sources.txt"
java -jar "$ECJ" -1.8 -nowarn -d "$WORK/obj" -cp "$BOOT" @"$WORK/sources.txt"
find "$WORK/obj" -name "*.class" > "$WORK/classes.txt"
java -cp "$D8JAR" com.android.tools.r8.D8 --release \
  --lib "$BOOT" --output "$WORK/dex" @"$WORK/classes.txt"
cp "$WORK/base.apk" "$OUT"
( cd "$WORK/dex" && zip -j -q -X "/home/z/my-project/$OUT" classes.dex )
echo "built $OUT: $(sha256sum "/home/z/my-project/$OUT" | cut -c1-16)"
