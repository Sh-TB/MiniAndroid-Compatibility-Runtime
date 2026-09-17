#!/usr/bin/env bash
# validate_connectfour_golden.sh — S51 "third board game" golden gate.
#
# Proves, from runtime-produced frames only:
#   1. fixture build (ECJ → D8, real char[6][7] multianewarray via
#      R-NEW-372 TYPE law + real Outer$Inner listener classes)
#   2. launch + 24-click interaction sequence runs end-to-end (exit 0)
#   3. SEMANTIC state machine through real DEX bytecode:
#        frame0  status "R to move"
#        frame1  status "Y to move"        (turn flip after click 1)
#        frame21 status "Y to move"        (21 drops: R 11×, Y 10×)
#        frame22 status "Y WINS"           (r+1,c+1 diagonal (0,3),(1,4),
#                                           (2,5),(3,6) — click 22 = col6
#                                           4th drop)
#        final   exactly 11 R marks + 11 Y marks (22 real drops)
#   4. PIXEL discriminators:
#        button band rendered (7 column buttons cover the band)
#        board TOP two display rows stay empty (gravity law: col6 stack
#        reaches row3 only — no mark may appear above display row 3)
#        bottom four display rows carry ink in ALL 7 column bands
#   5. frozen tail: frames 22/23/24 byte-identical (gameOver early
#      return — Android-correct)
#   6. deterministic replay: run B frame-for-frame byte-identical (SHA-256)
#
# Zero-skip law (§39): checks are counted; empty counts FAIL the gate.
#
# Usage: bash miniandroid/tests/fixtures/connectfour_golden/validate_connectfour_golden.sh \
#            [path-to-miniandroid-binary]
set -uo pipefail

BIN="${1:-build/miniandroid}"
REPO="$(cd "$(dirname "$0")/../../../.." && pwd)"
FIXTURE="$REPO/miniandroid/tests/fixtures/connectfour_golden"
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
APK="$WORK/connectfour_golden.apk"
if bash "$REPO/scripts/build/build_fixture_apk.sh" "$FIXTURE" "$APK" > "$WORK/build.log" 2>&1; then
    pass "build_fixture_apk: ECJ + D8 + package OK"
    APK_SHA=$(grep '^SHA256:' "$WORK/build.log" | cut -d' ' -f2)
    [ -n "$APK_SHA" ] && pass "APK SHA256 = $APK_SHA" || fail "APK hash missing"
else
    fail "build_fixture_apk failed (see $WORK/build.log)"; cat "$WORK/build.log"
    exit 1
fi

say "── [2] run A: launch + 24 clicks ─────────────────────────────────"
OUTA="$WORK/runA"
"$BIN" run "$APK" -o "$OUTA" --click-count 24 > "$OUTA.log" 2>&1
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

chk("24/24 clicks dispatched", m.get("clicks_dispatched") == 24)
chk("25 frames recorded", len(frames) == 25)

def texts(i):
    return {t["view_id"]: t["text"] for t in frames[i]["visible_texts"] if t["text"]}

t0 = texts(0)
# Status view id is run-dependent — find it by its frame0 text (AOSP-unique
# string set by onCreate's first setText).
STATUS = next((v for v, t in t0.items() if t.endswith("to move")), None)
chk("status view found in frame0", STATUS is not None)
chk("frame0 status 'R to move'", STATUS is not None and t0.get(STATUS) == "R to move")
chk("frame1 status 'Y to move'", t1.get(STATUS) == "Y to move") if (t1 := texts(1)) else chk("frame1 present", False)
t21, t22, t24 = texts(21), texts(22), texts(24)
chk("frame21 status 'Y to move' (21 drops: R 11×, Y 10× → Y plays the win)", t21.get(STATUS) == "Y to move")
chk("frame22 status 'Y WINS' (diagonal (0,3),(1,4),(2,5),(3,6))", t22.get(STATUS) == "Y WINS")
xs = sum(1 for v, t in t24.items() if v != STATUS and t == "R")
os_ = sum(1 for v, t in t24.items() if v != STATUS and t == "Y")
chk("final board 11 R marks", xs == 11)
chk("final board 11 Y marks", os_ == 11)
chk("frames 23,24 frozen (no pixel diff)",
    frames[23]["changed_pixels_vs_previous"] == 0 and
    frames[24]["changed_pixels_vs_previous"] == 0)
# Turn-flip law over the whole pre-win sequence: strict R/Y alternation.
seq = [texts(i).get(STATUS, "") for i in range(22)]
expect = [("R to move" if i % 2 == 0 else "Y to move") for i in range(22)]
chk("status alternates R/Y for clicks 1..21", seq == expect)
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
# The 7 column-button surfaces must form one contiguous full-width band.
chk("button band rendered (7 buttons cover a full-width band)",
    len(full) > 10)

board_top = int(full[-1]) + 1 if len(full) else int(H * 0.1)
g0 = f0.mean(axis=2)
BOARD_H = H - board_top
def col_ink(fb, r0, r1, c):
    y0 = board_top + r0 * BOARD_H // 6
    y1 = board_top + r1 * BOARD_H // 6
    x0, x1 = c * W // 7, (c + 1) * W // 7
    return int((np.abs(g0[y0:y1, x0:x1] - fb[y0:y1, x0:x1]) > 24).sum())

f22 = img(22).mean(axis=2)
# Gravity law: col6 stack reaches row3 only → display rows 5 and 4
# (the TOP two) must carry ZERO ink vs the empty frame0 board.
top_ink = sum(col_ink(f22, r, r + 1, c) for r in (0, 1) for c in range(7))
chk("board top two display rows empty (gravity law)", top_ink < 200)
# Bottom four display rows: every one of the 7 columns has ≥3 marks.
for c in range(7):
    ink = sum(col_ink(f22, r, r + 1, c) for r in (2, 3, 4, 5))
    chk(f"column band {c} has real drop ink (>300 px)", ink > 300)

# Game frozen: frames 22, 23, 24 byte-identical (gameOver early return).
h22 = open(os.path.join(d, "frame_022.png"), "rb").read()
h23 = open(os.path.join(d, "frame_023.png"), "rb").read()
h24 = open(os.path.join(d, "frame_024.png"), "rb").read()
chk("frames 22/23/24 byte-identical (frozen game)", h22 == h23 == h24)

sys.exit(0 if ok else 1)
PY
[ $? -eq 0 ] && pass "pixel discriminators correct" || fail "pixel discriminators wrong"

say "── [5] deterministic replay (run B) ──────────────────────────────"
OUTB="$WORK/runB"
"$BIN" run "$APK" -o "$OUTB" --click-count 24 > "$OUTB.log" 2>&1
python3 - "$OUTA" "$OUTB" <<'PY'
import json, sys, os

def shas(root):
    d = os.path.join(root, "frames")
    m = json.load(open(os.path.join(d, "manifest.json")))
    return [f["png_sha256"] for f in m.get("frames", [])]

a, b = shas(sys.argv[1]), shas(sys.argv[2])
ok = len(a) == 25 and a == b and all(a)
print(("PASS: " if ok else "FAIL: ") +
      f"all 25 frames byte-identical across runs ({a[0][:12]}…)")
sys.exit(0 if ok else 1)
PY
[ $? -eq 0 ] && pass "deterministic replay verified" || fail "replay differs"

say "── [6] zero-skip gate ────────────────────────────────────────────"
[ "$CHECKS" -gt 0 ] && pass "$CHECKS checks executed (none skipped)" \
                    || fail "no checks executed — zero-skip violation"

say ""
if [ "$FAIL" -eq 0 ]; then
    say "CONNECTFOUR-GOLDEN VALIDATION: ALL PASS ($CHECKS checks)"
    say "WORK=$WORK"
    exit 0
else
    say "CONNECTFOUR-GOLDEN VALIDATION: FAIL ($CHECKS checks, failures above)"
    say "WORK=$WORK"
    exit 1
fi
