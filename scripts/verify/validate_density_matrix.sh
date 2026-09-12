#!/usr/bin/env bash
# validate_density_matrix.sh — G04 §4 differential-oracle gate.
#
# Builds the density_matrix fixture via the REAL toolchain (aapt2+ECJ+D8),
# then proves the AOSP drawable density law at runtime:
#
#   LAW 1 (selection, ResourceTypes.cpp isBetterThan L2690-2737):
#     @ 420dpi over {160, 320, 640}: xxxhdpi (640) WINS — straddle law
#     ("l >= requested → smaller" does not apply since 320 < 420; the
#     higher bucket wins). Fill color proves WHICH bucket: yellow.
#   LAW 2 (exact bucket): @ 320dpi the exact xhdpi (320) bucket wins. Blue.
#   LAW 3 (scaling, BitmapFactory decodeResourceStream + native scale):
#     intrinsic = natural × target/source
#     @420: 40×20 × 420/640 = 26×13   (bbox asserted exact)
#     @320: 40×20 × 320/320 = 40×20   (bbox asserted exact)
#   LAW 4 (DENSITY_NONE): drawable-nodpi is NEVER scaled (40×20 at both
#     densities). Magenta.
#   LAW 5 (alias chain): icon_alias → icon (1 resolve_full hop); the
#     TERMINAL step's selected config governs density. resource_trace
#     asserts the chain + hop count.
#   LAW 6 (FIT_CENTER + wrap_content): scale = min(box/src) = 1.0 → the
#     bitmap lands 1:1 at the measured size; sequential y-flow respects
#     the sibling's SCALED height + 20px margin (nodpi y: 73@420, 80@320).
#
# Zero-skip: every check executes; PASS 0 / FAIL 0 is a failure.
set -uo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
MA="$REPO/MiniAndroid-Compatibility-Runtime/miniandroid"
FIX="$MA/tests/fixtures/density_matrix"
BIN="$MA/build/miniandroid"
TRACE="$MA/build/resource_trace"
OUT="${1:-/tmp/density_matrix_evidence}"

FAIL=0; CHECK=0
ok()   { CHECK=$((CHECK+1)); printf '  PASS: %s\n' "$*"; }
bad()  { CHECK=$((CHECK+1)); FAIL=1; printf '  FAIL: %s\n' "$*"; }

rm -rf "$OUT"; mkdir -p "$OUT"

echo "── [1] fixture build (aapt2 + ECJ + D8) ──────────"
bash "$REPO/scripts/build/build_fixture_apk.sh" "$FIX" "$OUT/density_matrix.apk" \
    > "$OUT/build.log" 2>&1 \
  && ok "fixture build + aapt2 link" || { bad "fixture build"; exit 1; }
APK_SHA=$(sha256sum "$OUT/density_matrix.apk" | cut -d' ' -f1)
ok "APK SHA256 = $APK_SHA"

echo "── [2] resource_trace: alias chain + selected config ──"
"$TRACE" "$OUT/density_matrix.apk" dm:drawable/icon_alias \
    > "$OUT/trace_alias.txt" 2>&1
grep -q "chain hops: 1" "$OUT/trace_alias.txt" \
  && ok "alias chain: 1 reference hop" || bad "alias chain hop count"
grep -q 'drawable-xxxhdpi-v4/icon.png' "$OUT/trace_alias.txt" \
  && ok "terminal value = xxxhdpi variant (straddle law @420)" \
  || bad "terminal value not xxxhdpi"
grep -q "selected=640 target=420 scale=0.6562 intrinsic=40x20 scaled=26x13" \
    "$OUT/trace_alias.txt" \
  && ok "density law: 640→420 scale 0.65625, intrinsic 26x13" \
  || bad "density scaling line"
"$TRACE" "$OUT/density_matrix.apk" dm:drawable/icon_nodpi \
    > "$OUT/trace_nodpi.txt" 2>&1
grep -q "selected=0 target=420" "$OUT/trace_nodpi.txt" || \
grep -q "selected=65535 target=420" "$OUT/trace_nodpi.txt" \
  && ok "nodpi selected density = DENSITY_NONE" || bad "nodpi density"

echo "── [3] run @420dpi (default device) ──────────────"
timeout 120 "$BIN" run "$OUT/density_matrix.apk" -o "$OUT/run420" \
    > "$OUT/run420.log" 2>&1 \
  && ok "runtime run @420 rc=0" || bad "runtime run @420"

echo "── [4] run @320dpi (device override) ─────────────"
MINIANDROID_DENSITY=320 timeout 120 "$BIN" run "$OUT/density_matrix.apk" \
    -o "$OUT/run320" > "$OUT/run320.log" 2>&1 \
  && ok "runtime run @320 rc=0" || bad "runtime run @320"

echo "── [5] pixel law assertions ──────────────────────"
python3 - "$OUT/run420/screenshot.png" "$OUT/run320/screenshot.png" << 'PYEOF' > "$OUT/pixel_checks.txt" 2>&1
import sys
from PIL import Image

def bboxes(path):
    im = Image.open(path).convert('RGB')
    px = im.load()
    pts = [(x, y) for y in range(0, 400) for x in range(0, 500)
           if px[x, y] != (255, 255, 255)]
    top = [q for q in pts if q[1] < 70]
    bot = [q for q in pts if q[1] >= 70]
    def bb(p):
        xs = [q[0] for q in p]; ys = [q[1] for q in p]
        return (min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1,
                px[xs[0] + 2, ys[0] + 2])
    return bb(top), bb(bot)

a420, n420 = bboxes(sys.argv[1])
a320, n320 = bboxes(sys.argv[2])
fails = 0
def ck(ok, what):
    global fails
    print(("PASS" if ok else "FAIL") + ": " + what)
    if not ok: fails = 1
# @420: straddle law picks xxxhdpi (yellow), scaled 26x13 at (40,40)
ck(a420[0] == 40 and a420[1] == 40 and a420[2] == 26 and a420[3] == 13,
   f"@420 alias bbox 40,40 26x13 (got {a420[:4]})")
ck(a420[4] == (220, 200, 30), f"@420 alias fill = xxxhdpi yellow (got {a420[4]})")
ck(n420[0] == 40 and n420[1] == 73 and n420[2] == 40 and n420[3] == 20,
   f"@420 nodpi bbox 40,73 40x20 (got {n420[:4]})")
ck(n420[4] == (200, 30, 200), f"@420 nodpi fill = magenta (got {n420[4]})")
# @320: exact bucket law picks xhdpi (blue), unscaled 40x20; flow shifts
ck(a320[0] == 40 and a320[1] == 40 and a320[2] == 40 and a320[3] == 20,
   f"@320 alias bbox 40,40 40x20 (got {a320[:4]})")
ck(a320[4] == (30, 60, 200), f"@320 alias fill = xhdpi blue (got {a320[4]})")
ck(n320[1] == 80, f"@320 nodpi y = 80 (sibling 20px + margin 20) (got {n320[1]})")
sys.exit(fails)
PYEOF
if [ $? -eq 0 ]; then ok "pixel law checks (8)"; else bad "pixel law checks"; fi
grep -h "PASS\|FAIL" "$OUT/pixel_checks.txt"

echo "── [6] 3-run determinism @420 ────────────────────"
S1=$(sha256sum "$OUT/run420/screenshot.png" | cut -c1-16)
for i in 2 3; do
    rm -rf "$OUT/det$i"
    timeout 120 "$BIN" run "$OUT/density_matrix.apk" -o "$OUT/det$i" \
        > "$OUT/det$i.log" 2>&1
    S=$(sha256sum "$OUT/det$i/screenshot.png" | cut -c1-16)
    [ "$S" = "$S1" ] && ok "run $i byte-identical ($S)" || bad "run $i differs"
done

echo "──────────────────────────────────────────────"
echo "DENSITY-MATRIX GATE: $((CHECK-FAIL))/$CHECK PASS"
[ $FAIL -eq 0 ] && echo "DENSITY MATRIX: ALL PASS" && exit 0
echo "DENSITY MATRIX: FAILURES PRESENT"; exit 1
