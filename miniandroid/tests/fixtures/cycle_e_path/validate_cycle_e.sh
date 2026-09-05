#!/usr/bin/env bash
# validate_cycle_e.sh — CYCLE-E Canvas Path strengthening proof fixture.
#
# Proves, from runtime-produced frames only:
#   1. fixture build (ECJ → D8 with OUTER$INNER class files) succeeds
#   2. the runtime executes the APK end-to-end (exit 0)
#   3. onDraw ran through REAL DEX (custom inner-class view dispatched)
#   4. every pixel discriminator matches the Android-correct expectation:
#        cubic fill, rMoveTo/rLineTo stroke, Path.offset geometry shift,
#        drawOval curve (not a rect), drawArc pie wedge, WINDING vs
#        EVEN_ODD fill rules, stroke-not-fill honesty
#   5. deterministic replay: a second run is byte-identical (SHA-256)
#
# Zero-skip law (§39): every check is counted and reported; the gate FAILS
# if any check fails or if no checks were executed.
#
# Usage: bash miniandroid/tests/fixtures/cycle_e_path/validate_cycle_e.sh \
#            [path-to-miniandroid-binary]
set -uo pipefail

BIN="${1:-build/miniandroid}"
REPO="$(cd "$(dirname "$0")/../../../.." && pwd)"
FIXTURE="$REPO/miniandroid/tests/fixtures/cycle_e_path"
WORK="$(mktemp -d)"
FAIL=0
CHECKS=0

say()  { printf '%s\n' "$*"; }
pass() { CHECKS=$((CHECKS+1)); printf '  PASS: %s\n' "$*"; }
fail() { CHECKS=$((CHECKS+1)); FAIL=1; printf '  FAIL: %s\n' "$*"; }

[ -x "$BIN" ] || BIN="$REPO/miniandroid/$BIN"
[ -x "$BIN" ] || { say "FAIL: binary not found: ${1:-build/miniandroid}"; exit 1; }
# §zero-skip hygiene: absolutize BEFORE the cd below — a relative -x check
# passes at the caller's CWD but then 127s once the script cd's elsewhere.
BIN="$(cd "$(dirname "$BIN")" && pwd)/$(basename "$BIN")"

cd "$REPO/miniandroid"

say "── [1] fixture build (inner-class-safe tool) ──────────────────────"
APK="$WORK/cycle_e_path.apk"
if bash "$REPO/scripts/build_fixture_apk.sh" "$FIXTURE" "$APK" > "$WORK/build.log" 2>&1; then
    pass "build_fixture_apk: ECJ + D8 + package OK"
    grep -q "class files: " "$WORK/build.log" \
        && pass "class list collected (NUL-safe)" \
        || fail "class count line missing"
    APK_SHA=$(grep '^SHA256:' "$WORK/build.log" | cut -d' ' -f2)
    [ -n "$APK_SHA" ] && pass "APK SHA256 = $APK_SHA" || fail "APK hash missing"
else
    fail "build_fixture_apk failed (see $WORK/build.log)"; cat "$WORK/build.log"
    exit 1
fi

say "── [2] runtime run #1 ─────────────────────────────────────────────"
OUT1="$WORK/run1"
"$BIN" run "$APK" -o "$OUT1" --width 480 --height 800 > "$OUT1.log" 2>&1
rc=$?
[ $rc -eq 0 ] && pass "run exit 0" || fail "run exit $rc"
[ -f "$OUT1/screenshot.png" ] && pass "screenshot.png produced" \
                              || fail "screenshot.png missing"
grep -q "C013-ONDRAW.*dispatched=YES" "$OUT1.log" \
    && pass "onDraw dispatched through real DEX (custom view)" \
    || fail "onDraw dispatch not observed in log"

say "── [3] pixel discriminators (frame #1) ────────────────────────────"
python3 - "$OUT1/screenshot.png" <<'PY'
import sys
from PIL import Image

img = Image.open(sys.argv[1]).convert("RGB")
W, H = img.size

results = []
def check(name, x, y, want):
    r, g, b = img.getpixel((x, y))
    results.append((name, (x, y), want, (r, g, b)))

def is_white(c):  return all(v > 240 for v in c)
def is_color(c, hex_rgb, tol=40):
    t = tuple(int(hex_rgb[i:i+2], 16) for i in (0, 2, 4))
    return all(abs(a - b) <= tol for a, b in zip(c, t))

BLUE   = "1E40AF"   # R1 cubic fill
GREEN  = "228B22"   # R2 stroke
RED    = "C62828"   # R2 offset copy + R3 oval
YELLOW = "F9A825"   # R3 arc wedge
MAGENTA= "AD1457"   # R4 winding
CYAN   = "00838F"   # R4 even-odd

# R1 — cubic Bézier bulge (real curve vs lineTo degenerate)
check("R1 cubic bulge inside",        100,  85, ("color", BLUE))
check("R1 above chord outside",       100,  20, ("white", None))
check("R1 below curve outside",       100, 112, ("white", None))

# R2 — rMoveTo/rLineTo stroked polyline (fill honesty)
check("R2 top edge stroke",           280,  40, ("color", GREEN))
check("R2 right edge stroke",         310,  65, ("color", GREEN))
check("R2 left edge stroke",          250,  65, ("color", GREEN))
check("R2 interior NOT filled",       280,  65, ("white", None))
# R2 — Path.offset geometry shift (offset square edges: x=350/410, y=160/210)
check("R2 offset copy top edge",      380, 160, ("color", RED))
check("R2 offset copy left edge",     350, 185, ("color", RED))
check("R2 offset copy NOT at origin", 280, 160, ("white", None))

# R3 — drawOval real curve
check("R3 oval center",               120, 540, ("color", RED))
check("R3 bbox corner white (oval≠rect)", 50, 472, ("white", None))
check("R3 oval bottom edge",          120, 612, ("color", RED))
# R3 — drawArc pie wedge (useCenter=true)
check("R3 wedge interior (45°)",      365, 585, ("color", YELLOW))
check("R3 wedge center",              320, 540, ("color", YELLOW))
check("R3 opposite quadrant white",   275, 495, ("white", None))

# R4 — fill rules on identical overlapping geometry
check("R4 WINDING overlap filled",    107, 727, ("color", MAGENTA))
check("R4 WINDING non-overlap",        60, 690, ("color", MAGENTA))
check("R4 EVEN_ODD overlap is hole",  317, 727, ("white", None))
check("R4 EVEN_ODD non-overlap",      270, 690, ("color", CYAN))

for name, (x, y), want, got in results:
    kind, ref = want
    ok = is_white(got) if kind == "white" else is_color(got, ref)
    got_s = "WHITE" if is_white(got) else "#%02X%02X%02X" % got
    print(f"{'PASS' if ok else 'FAIL'}: {name} ({x},{y}) want={kind}"
          f"{ref or ''} got={got_s}")
    if not ok:
        sys.exit(1)
PY
[ $? -eq 0 ] && pass "all pixel discriminators correct" || fail "pixel discriminators failed"

say "── [4] deterministic replay (run #2) ─────────────────────────────"
OUT2="$WORK/run2"
"$BIN" run "$APK" -o "$OUT2" --width 480 --height 800 > "$OUT2.log" 2>&1
# Zero-skip law: identical EMPTY hashes must never count as a replay pass.
if [ -f "$OUT1/screenshot.png" ] && [ -f "$OUT2/screenshot.png" ]; then
    H1=$(sha256sum "$OUT1/screenshot.png" | cut -d' ' -f1)
    H2=$(sha256sum "$OUT2/screenshot.png" | cut -d' ' -f1)
else
    H1=""; H2=""
    fail "replay frames missing (run1/run2 screenshots)"
fi
say "  frame#1 SHA256 = $H1"
say "  frame#2 SHA256 = $H2"
if [ -n "$H1" ] && [ "$H1" == "$H2" ]; then
    pass "byte-identical replay (Canvas replay deterministic)"
elif [ -n "$H1" ]; then
    fail "replay differs — nondeterministic Canvas path"
fi

say "── [5] zero-skip gate ────────────────────────────────────────────"
[ "$CHECKS" -gt 0 ] && pass "$CHECKS checks executed (none skipped)" \
                    || fail "no checks executed — zero-skip violation"

say ""
if [ "$FAIL" -eq 0 ]; then
    say "CYCLE-E VALIDATION: ALL PASS ($CHECKS checks)"
    say "WORK=$WORK"
    exit 0
else
    say "CYCLE-E VALIDATION: FAIL ($CHECKS checks, failures above)"
    say "WORK=$WORK"
    exit 1
fi
