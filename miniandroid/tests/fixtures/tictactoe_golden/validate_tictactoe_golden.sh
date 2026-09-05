#!/usr/bin/env bash
# validate_tictactoe_golden.sh — §9/§10/§11 "ONE COMPLETE APK" proof.
#
# Proves, from runtime-produced frames only:
#   1. fixture build (ECJ → D8, real Outer$Inner listener classes)
#   2. launch + 9-click interaction sequence runs end-to-end (exit 0)
#   3. SEMANTIC state machine through real DEX bytecode:
#        frame0  status "X to move"
#        frame1  status "O to move"        (turn flip after click 1)
#        frame7  status "X WINS"           (anti-diagonal 2,4,6 complete)
#        final   exactly 4 X marks + 3 O marks (clicks 8,9 frozen by
#                gameOver — Android-correct early return)
#   4. PIXEL discriminators:
#        board rendered (button surfaces cover the frame)
#        every mark lands in ITS OWN cell region (localized ink diff)
#        cells 0 and 1 stay empty (no spurious ink)
#   5. deterministic replay: run B frame-for-frame byte-identical (SHA-256)
#
# Zero-skip law (§39): checks are counted; empty counts FAIL the gate.
#
# Usage: bash miniandroid/tests/fixtures/tictactoe_golden/validate_tictactoe_golden.sh \
#            [path-to-miniandroid-binary]
set -uo pipefail

BIN="${1:-build/miniandroid}"
REPO="$(cd "$(dirname "$0")/../../../.." && pwd)"
FIXTURE="$REPO/miniandroid/tests/fixtures/tictactoe_golden"
WORK="$(mktemp -d)"
FAIL=0
CHECKS=0

say()  { printf '%s\n' "$*"; }
pass() { CHECKS=$((CHECKS+1)); printf '  PASS: %s\n' "$*"; }
fail() { CHECKS=$((CHECKS+1)); FAIL=1; printf '  FAIL: %s\n' "$*"; }

[ -x "$BIN" ] || BIN="$REPO/miniandroid/$BIN"
[ -x "$BIN" ] || { say "FAIL: binary not found: ${1:-build/miniandroid}"; exit 1; }
# Absolutize before cd (same law as validate_cycle_e.sh).
BIN="$(cd "$(dirname "$BIN")" && pwd)/$(basename "$BIN")"

cd "$REPO/miniandroid"

say "── [1] fixture build ─────────────────────────────────────────────"
APK="$WORK/tictactoe_golden.apk"
if bash "$REPO/scripts/build_fixture_apk.sh" "$FIXTURE" "$APK" > "$WORK/build.log" 2>&1; then
    pass "build_fixture_apk: ECJ + D8 + package OK"
    APK_SHA=$(grep '^SHA256:' "$WORK/build.log" | cut -d' ' -f2)
    [ -n "$APK_SHA" ] && pass "APK SHA256 = $APK_SHA" || fail "APK hash missing"
else
    fail "build_fixture_apk failed (see $WORK/build.log)"; cat "$WORK/build.log"
    exit 1
fi

say "── [2] run A: launch + 9 clicks ──────────────────────────────────"
OUTA="$WORK/runA"
"$BIN" run "$APK" -o "$OUTA" --click-count 9 > "$OUTA.log" 2>&1
rc=$?
[ $rc -eq 0 ] && pass "run exit 0" || fail "run exit $rc"
[ -f "$OUTA/frames/manifest.json" ] && pass "frames manifest produced" \
                                    || fail "frames manifest missing"

say "── [3] semantic state machine (real DEX listeners) ───────────────"
python3 - "$OUTA/frames/manifest.json" <<'PY'
import json, sys

m = json.load(open(sys.argv[1]))
frames = m.get("frames", [])
ok = True
def chk(name, cond):
    global ok
    print(("PASS: " if cond else "FAIL: ") + name)
    if not cond: ok = False

chk("9/9 clicks dispatched", m.get("clicks_dispatched") == 9)
chk("10 frames recorded", len(frames) == 10)

def texts(i):
    return {t["view_id"]: t["text"] for t in frames[i]["visible_texts"] if t["text"]}

t0, t1, t7, t9 = texts(0), texts(1), texts(7), texts(9)
# Status view id is run-dependent — find it by its frame0 text (AOSP-unique
# string set by onCreate's first setText).
STATUS = next((v for v, t in t0.items() if t.endswith("to move")), None)
chk("status view found in frame0", STATUS is not None)
chk("frame0 status 'X to move'", STATUS is not None and t0.get(STATUS) == "X to move")
chk("frame1 status 'O to move'", t1.get(STATUS) == "O to move")
# Cell view ids differ per run — count marks semantically instead.
c1 = [t for v, t in t1.items() if v != STATUS]
chk("frame1 exactly one X placed, no O yet",
    c1.count("X") == 1 and c1.count("O") == 0)
chk("frame7 status 'X WINS'", t7.get(STATUS) == "X WINS")
xs = sum(1 for v, t in t9.items() if v != STATUS and t == "X")
os_ = sum(1 for v, t in t9.items() if v != STATUS and t == "O")
chk("final board 4 X marks", xs == 4)
chk("final board 3 O marks", os_ == 3)
chk("frames 8,9 frozen (no diff)",
    frames[8]["changed_pixels_vs_previous"] == 0 and
    frames[9]["changed_pixels_vs_previous"] == 0)
sys.exit(0 if ok else 1)
PY
[ $? -eq 0 ] && pass "semantic state machine correct" || fail "semantic state machine wrong"

say "── [4] pixel discriminators ──────────────────────────────────────"
python3 - "$OUTA/frames" <<'PY'
import sys, os
import numpy as np
from PIL import Image

d = sys.argv[1]
def img(i):
    return np.asarray(Image.open(os.path.join(d, f"frame_{i:03d}.png")).convert("RGB"))

f0 = img(0)
H, W, _ = f0.shape
ok = True
def chk(name, cond):
    global ok
    print(("PASS: " if cond else "FAIL: ") + name)
    if not cond: ok = False

blue = ((np.abs(f0[:,:,0].astype(int) - 0x6F) < 10) &
        (np.abs(f0[:,:,1].astype(int) - 0xA8) < 10) &
        (np.abs(f0[:,:,2].astype(int) - 0xDC) < 10))
rows_blue = blue.sum(axis=1)
full = np.where(rows_blue > W * 0.9)[0]
# The 9 button surfaces must cover ≥80% of the frame's HEIGHT in rows.
chk("board surfaces rendered (buttons fill the frame)",
    len(full) > H * 0.8)

board_top = int(full[0]) if len(full) else int(H * 0.08)
g0 = f0.mean(axis=2)
def region_diffs(fb):
    out = []
    for r in range(3):
        row = []
        for c in range(3):
            y0 = board_top + r * (H - board_top) // 3
            y1 = board_top + (r + 1) * (H - board_top) // 3
            x0, x1 = c * W // 3, (c + 1) * W // 3
            row.append(int((np.abs(g0[y0:y1, x0:x1] - fb[y0:y1, x0:x1]) > 24).sum()))
        out.append(row)
    return out

f7 = img(7).mean(axis=2)
d7 = region_diffs(f7)
# After 7 clicks: X at cells 2,4,6,8; O at 3,5,7; cells 0,1 untouched.
want = [[0, 0, 233], [287, 233, 287], [233, 287, 233]]
nonzero = [[d7[r][c] > 40 for c in range(3)] for r in range(3)]
want_nz = [[w > 0 for w in row] for row in want]
chk("marks exactly in cells 2..8, cells 0/1 empty",
    nonzero == want_nz)
chk("every mark region has real glyph ink (>100 px each)",
    all(d7[r][c] > 100 for r in range(3) for c in range(3) if want[r][c]))

# Game frozen: frames 7, 8, 9 byte-identical (gameOver early return).
h7 = open(os.path.join(d, "frame_007.png"), "rb").read()
h8 = open(os.path.join(d, "frame_008.png"), "rb").read()
h9 = open(os.path.join(d, "frame_009.png"), "rb").read()
chk("frames 7/8/9 byte-identical (frozen game)", h7 == h8 == h9)

sys.exit(0 if ok else 1)
PY
[ $? -eq 0 ] && pass "pixel discriminators correct" || fail "pixel discriminators wrong"

say "── [5] deterministic replay (run B) ──────────────────────────────"
OUTB="$WORK/runB"
"$BIN" run "$APK" -o "$OUTB" --click-count 9 > "$OUTB.log" 2>&1
python3 - "$OUTA" "$OUTB" <<'PY'
import json, sys, hashlib, os

def shas(root):
    d = os.path.join(root, "frames")
    m = json.load(open(os.path.join(d, "manifest.json")))
    return [f["png_sha256"] for f in m.get("frames", [])]

a, b = shas(sys.argv[1]), shas(sys.argv[2])
ok = len(a) == 10 and a == b and all(a)
print(("PASS: " if ok else "FAIL: ") +
      f"all 10 frames byte-identical across runs ({a[0][:12]}…)")
sys.exit(0 if ok else 1)
PY
[ $? -eq 0 ] && pass "deterministic replay verified" || fail "replay differs"

say "── [6] zero-skip gate ────────────────────────────────────────────"
[ "$CHECKS" -gt 0 ] && pass "$CHECKS checks executed (none skipped)" \
                    || fail "no checks executed — zero-skip violation"

say ""
if [ "$FAIL" -eq 0 ]; then
    say "TICTACTOE-GOLDEN VALIDATION: ALL PASS ($CHECKS checks)"
    say "WORK=$WORK"
    exit 0
else
    say "TICTACTOE-GOLDEN VALIDATION: FAIL ($CHECKS checks, failures above)"
    say "WORK=$WORK"
    exit 1
fi
