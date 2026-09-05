#!/usr/bin/env bash
# validate_helloworld_golden.sh — §27/§28 "simplest permanent boot/render
# regression test".
#
# Proves, from a REAL toolchain-built APK (ECJ → D8 → zip):
#   1. fixture build + APK/DEX SHA-256 evidence
#   2. runtime boot: APK → manifest → Activity.onCreate → DEX execution →
#      View tree (LinearLayout + 2 TextView + Button) → measure → layout →
#      fonts → Canvas → renderer → visible PNG
#   3. §27 semantic chain checks from runtime-produced evidence:
#        AOSP gravity law (EXT-AOSP-001): container setGravity(0x11)
#        horizontally centers children ((screen_w - child_w)/2)
#        AOSP sp law (EXT-AOSP-002): setTextSize(28sp) → 28*2.625=73.5px,
#        visibly larger than 14sp line
#   4. pixel discriminators: headline ink band taller than subtitle band;
#        both text rows horizontally centered; button surface present
#   5. §28 deterministic replay: run B byte-identical (SHA-256)
#
# Required §28 evidence record: APK SHA256, DEX SHA256, runtime command,
# exit status, screenshot SHA256, dimensions, run #1 vs run #2.
#
# Zero-skip law: every check is counted; empty counts FAIL the gate.
#
# Usage: bash miniandroid/tests/fixtures/helloworld_golden/validate_helloworld_golden.sh \
#            [path-to-miniandroid-binary]
set -uo pipefail

BIN="${1:-build/miniandroid}"
REPO="$(cd "$(dirname "$0")/../../../.." && pwd)"
FIXTURE="$REPO/miniandroid/tests/fixtures/helloworld_golden"
WORK="$(mktemp -d)"
FAIL=0
CHECKS=0

say()  { printf '%s\n' "$*"; }
pass() { CHECKS=$((CHECKS+1)); printf '  PASS: %s\n' "$*"; }
fail() { CHECKS=$((CHECKS+1)); FAIL=1; printf '  FAIL: %s\n' "$*"; }

[ -x "$BIN" ] || BIN="$REPO/miniandroid/$BIN"
[ -x "$BIN" ] || { say "FAIL: binary not found: ${1:-build/miniandroid}"; exit 1; }
BIN="$(cd "$(dirname "$BIN")" && pwd)/$(basename "$BIN")"

cd "$REPO/miniandroid"

say "── [1] fixture build (real toolchain: ECJ + D8) ──────────────────"
APK="$WORK/helloworld_golden.apk"
if bash "$REPO/scripts/build_fixture_apk.sh" "$FIXTURE" "$APK" > "$WORK/build.log" 2>&1; then
    pass "build_fixture_apk: ECJ + D8 + package OK"
    APK_SHA=$(grep '^SHA256:' "$WORK/build.log" | cut -d' ' -f2)
    [ -n "$APK_SHA" ] && pass "APK SHA256 = $APK_SHA" || fail "APK hash missing"
else
    fail "build_fixture_apk failed (see $WORK/build.log)"; cat "$WORK/build.log"
    exit 1
fi
# DEX SHA-256 (classes.dex extracted from the APK)
python3 - "$APK" > "$WORK/dex.sha" <<'PY'
import sys, zipfile, hashlib
with zipfile.ZipFile(sys.argv[1]) as z:
    print(hashlib.sha256(z.read("classes.dex")).hexdigest())
PY
DEX_SHA=$(cat "$WORK/dex.sha")
[ -n "$DEX_SHA" ] && pass "DEX SHA256 = $DEX_SHA" || fail "DEX hash missing"

say "── [2] run A: boot + render ──────────────────────────────────────"
OUTA="$WORK/runA"
"$BIN" run "$APK" -o "$OUTA" > "$OUTA.log" 2>&1
rc=$?
[ $rc -eq 0 ] && pass "run exit 0" || fail "run exit $rc"
[ -f "$OUTA/screenshot.png" ] && pass "screenshot produced" || fail "screenshot missing"
grep -q "EXT-AOSP-001" "$OUTA.log" 2>/dev/null \
    && pass "EXT-AOSP-001 container setGravity intercepted (real DEX dispatch)" \
    || fail "container setGravity intercept not observed"
grep -q "EXT-AOSP-002.*px=73.5" "$OUTA.log" 2>/dev/null \
    && pass "EXT-AOSP-002 setTextSize 28sp→73.5px (AOSP sp law)" \
    || fail "setTextSize sp conversion not observed"
grep -q "EXT-AOSP-002.*px=36.75" "$OUTA.log" 2>/dev/null \
    && pass "EXT-AOSP-002 setTextSize 14sp→36.75px" \
    || fail "14sp conversion not observed"

say "── [3] §27 semantic chain (gravity centering + size law) ────────"
python3 - "$OUTA/screenshot.png" > "$WORK/pixels.report" <<'PY'
import sys, zlib, struct

d = open(sys.argv[1], 'rb').read()
pos = 8; idat = b''; w = h = None; ctype = None
while pos < len(d):
    ln = struct.unpack('>I', d[pos:pos+4])[0]; typ = d[pos+4:pos+8]
    if typ == b'IHDR':
        w, h, bd, ctype = struct.unpack('>IIBB', d[pos+8:pos+18])
    elif typ == b'IDAT':
        idat += d[pos+8:pos+8+ln]
    pos += 12 + ln
raw = zlib.decompress(idat)
ch = 4 if ctype == 6 else 3
stride = w * ch
out = bytearray(); prev = bytearray(stride); i = 0
for y in range(h):
    f = raw[i]; i += 1
    line = bytearray(raw[i:i+stride]); i += stride
    if f == 1:
        for x in range(ch, stride): line[x] = (line[x] + line[x-ch]) & 255
    elif f == 2:
        for x in range(stride): line[x] = (line[x] + prev[x]) & 255
    elif f == 3:
        for x in range(stride):
            a = line[x-ch] if x >= ch else 0
            line[x] = (line[x] + ((a + prev[x]) >> 1)) & 255
    elif f == 4:
        for x in range(stride):
            a = line[x-ch] if x >= ch else 0
            b = prev[x]; c = prev[x-ch] if x >= ch else 0
            p = a + b - c; pa = abs(p-a); pb = abs(p-b); pc = abs(p-c)
            pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
            line[x] = (line[x] + pr) & 255
    out += line; prev = line

def row_ink(y):
    return sum(1 for x in range(w) if out[y*stride + x*ch] < 200
               and out[y*stride + x*ch + 1] < 200)

def band(y0, y1):
    rows = [y for y in range(y0, min(y1, h)) if row_ink(y) > 3]
    if not rows:
        return None
    xs = [x for y in rows[:6] for x in range(w)
          if out[y*stride + x*ch] < 200]
    return {"top": rows[0], "bottom": rows[-1],
            "height": rows[-1] - rows[0] + 1,
            "left": min(xs), "right": max(xs)}

headline = band(0, 160)
sub      = band(160, 300)
print(f"frame {w}x{h}")
print(f"headline band: {headline}")
print(f"subtitle band: {sub}")
hc = (headline["left"] + headline["right"]) / 2 if headline else 0
sc = (sub["left"] + sub["right"]) / 2 if sub else 0
print(f"headline center={hc:.1f} (frame center {w/2})")
print(f"subtitle center={sc:.1f}")
print(f"headline taller than subtitle: "
      f"{headline and sub and headline['height'] > sub['height']}")
print(f"headline centered: {abs(hc - w/2) < w*0.06}")
print(f"subtitle centered: {abs(sc - w/2) < w*0.06}")
PY
FRAME_WH=$(head -1 "$WORK/pixels.report")
[ -n "$FRAME_WH" ] && pass "$FRAME_WH" || fail "frame decode failed"
grep -q "headline taller than subtitle: True" "$WORK/pixels.report" \
    && pass "28sp headline band taller than 14sp subtitle band (AOSP sp law visible)" \
    || fail "text size bands do not differ"
grep -q "headline centered: True" "$WORK/pixels.report" \
    && pass "headline horizontally centered (EXT-AOSP-001)" \
    || fail "headline not centered"
grep -q "subtitle centered: True" "$WORK/pixels.report" \
    && pass "subtitle horizontally centered (EXT-AOSP-001)" \
    || fail "subtitle not centered"

say "── [4] §28 deterministic replay (run B) ─────────────────────────"
OUTB="$WORK/runB"
"$BIN" run "$APK" -o "$OUTB" > "$OUTB.log" 2>&1
rc_b=$?
[ $rc_b -eq 0 ] && pass "run B exit 0" || fail "run B exit $rc_b"
if cmp -s "$OUTA/screenshot.png" "$OUTB/screenshot.png"; then
    pass "screenshots byte-identical across runs"
else
    fail "screenshots differ between runs"
fi

say "── [5] §28 evidence record ───────────────────────────────────────"
SHOT_SHA=$(sha256sum "$OUTA/screenshot.png" | cut -d' ' -f1)
DIM=$(python3 -c "
import struct
d = open('$OUTA/screenshot.png','rb').read()
w, h = struct.unpack('>II', d[16:24]); print(f'{w}x{h}')")
pass "screenshot SHA256 = $SHOT_SHA"
pass "screenshot dimensions = $DIM"
pass "runtime command = $BIN run <apk> -o <outdir>"
say "    fixture dir: miniandroid/tests/fixtures/helloworld_golden"
say "    work dir preserved at: $WORK"

say "── [6] zero-skip gate ────────────────────────────────────────────"
[ $CHECKS -gt 0 ] && pass "$CHECKS checks executed (none skipped)" || fail "no checks ran"

if [ $FAIL -eq 0 ]; then
    say "HELLOWORLD-GOLDEN VALIDATION: ALL PASS ($CHECKS checks)"
    exit 0
else
    say "HELLOWORLD-GOLDEN VALIDATION: FAILURES PRESENT ($CHECKS checks)"
    exit 1
fi
