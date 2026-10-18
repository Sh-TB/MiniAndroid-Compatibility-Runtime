#!/usr/bin/env bash
# cont99_img_run.sh — run the CONT-99 T3 probe and pixel-sample the final
# raster (screenshot.ppm, P6 binary) at deterministic points.
# Usage: cont99_img_run.sh <tag>   (tag = pre | post)
set -uo pipefail
cd /home/z/my-project
BIN=${BIN:-miniandroid/build/miniandroid}
APK=run/cont99/c99im.apk
TAG=$1
OUT=run/cont99/img_${TAG}
mkdir -p "$OUT"

o="$OUT/run"; rm -rf "$o"; mkdir -p "$o"
timeout 120 "$BIN" run "$APK" --width 1080 --height 1920 --frames 5 \
  --max-seconds 30 -o "$o" > "$o/run.log" 2>&1
echo "== state rows =="
rg -o "\[C99-IM(VER|IMPHASE|IM|IMSWITCH|IMDONE|IMERR)\].*" "$o/run.log" | sed 's/^/  /'

PPM="$o/screenshot.ppm"
[ -f "$PPM" ] || PPM=$(ls "$o"/frames/*.ppm 2>/dev/null | tail -1)
echo "== pixel rows (source: $PPM) =="
python3 - "$PPM" << 'PYEOF'
import sys
def sample(path, pts):
    with open(path, 'rb') as f:
        data = f.read()
    # P6 parser with comment tolerance
    assert data[:2] == b'P6', 'not P6'
    i, fields = 2, []
    while len(fields) < 3:
        while i < len(data) and data[i:i+1].isspace(): i += 1
        if data[i:i+1] == b'#':
            while data[i:i+1] not in (b'\n', b''): i += 1
            continue
        j = i
        while j < len(data) and not data[j:j+1].isspace(): j += 1
        fields.append(int(data[i:j])); i = j
    i += 1  # single whitespace after maxval
    w, h = fields[0], fields[1]
    def px(x, y):
        o = i + (y * w + x) * 3
        return (data[o], data[o+1], data[o+2])
    BG  = (0xEE, 0xEE, 0xEE)
    RED = (0xCC, 0x22, 0x22)
    BLU = (0x22, 0x22, 0xCC)
    GRN = (0x22, 0xCC, 0x22)
    def name(c):
        for n, e in (("BG", BG), ("RED", RED), ("BLU", BLU), ("GRN", GRN)):
            if all(abs(a-b) <= 8 for a, b in zip(c, e)):
                return n
        return f"?{c}"
    ROWS = [
        ("iv1.fitCenter->FIT_XY fills",  (100,100), "RED"),
        ("iv1.corner (letterbox gone)",  (10,10),   "RED"),
        ("iv2.center",                   (100,300), "RED"),
        ("iv2.crop-reaches-x5",          (5,205),   "RED"),
        ("iv3.center",                   (100,500), "BLU"),
        ("iv3.letterbox",                (10,410),  "BG"),
        ("iv4.fitXY-center",             (50,650),  "GRN"),
        ("iv4.fitXY-corner",             (1,601),   "GRN"),
        ("iv5.centerInside-center",      (100,800), "GRN"),
        ("iv5.no-upscale-margin",        (10,710),  "BG"),
        ("iv6.center-natural",           (50,950),  "GRN"),
        ("iv6.natural-eq-box-corner",    (1,901),   "GRN"),
        ("iv7.wrap-intrinsic-center",    (50,1050), "GRN"),
        ("iv7.nothing-beyond-intrinsic", (150,1050),"BG"),
        ("iv8.missing-image",            (50,1150), "BG"),
    ]
    ok = 0
    for tag, (x, y), want in ROWS:
        c = px(x, y); got = name(c)
        verdict = "OK" if got == want else "DIVERGE"
        if got == want: ok += 1
        print(f"  [C99-PX] {tag} ({x},{y}) got={got} want={want} v={verdict}")
    print(f"  PIXELS: {ok}/{len(ROWS)}")
sample(sys.argv[1], None)
PYEOF
echo "RUN DONE ($TAG)"
