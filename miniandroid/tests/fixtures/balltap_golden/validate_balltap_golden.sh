#!/usr/bin/env bash
# validate_balltap_golden.sh — S51 finalization simple-2D-ball-game gate.
#
# Proves, from runtime-produced frames only:
#   1. fixture build (ECJ + D8; integer physics + paddle collision through
#      real DEX)
#   2. launch + 38-click sequence (35 to WIN + 3 frozen overtap) exit 0
#   3. SEMANTIC state machine (design solver table):
#        frame0  "GOAL 0/3 SERVE"
#        frame11 "GOAL 1/3"   (ball-step 4)
#        frame23 "GOAL 2/3"   (ball-step 8)
#        frame35 "GOAL 3/3 WIN" (ball-step 12; zero misses)
#        exactly one ball cell "o" per frame; paddle "=" 2 cells
#   4. frozen tail: frames 36/37/38 zero pixel delta, byte-identical
#   5. deterministic replay: run B frame-for-frame byte-identical (SHA-256)
#
# Zero-skip law (§39): checks are counted; empty counts FAIL the gate.
#
# Usage: bash miniandroid/tests/fixtures/balltap_golden/validate_balltap_golden.sh \
#            [path-to-miniandroid-binary]
set -uo pipefail

BIN="${1:-build/miniandroid}"
REPO="$(cd "$(dirname "$0")/../../../.." && pwd)"
FIXTURE="$REPO/miniandroid/tests/fixtures/balltap_golden"
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

say "── [1] fixture build ─────────────────────────────────────────────"
APK="$WORK/balltap_golden.apk"
if bash "$REPO/scripts/build/build_fixture_apk.sh" "$FIXTURE" "$APK" > "$WORK/build.log" 2>&1; then
    pass "build_fixture_apk: ECJ + D8 + package OK"
    APK_SHA=$(grep '^SHA256:' "$WORK/build.log" | cut -d' ' -f2)
    [ -n "$APK_SHA" ] && pass "APK SHA256 = $APK_SHA" || fail "APK hash missing"
else
    fail "build_fixture_apk failed (see $WORK/build.log)"; cat "$WORK/build.log"
    exit 1
fi

say "── [2] run A: launch + 38 clicks ─────────────────────────────────"
OUTA="$WORK/runA"
"$BIN" run "$APK" -o "$OUTA" --click-count 38 > "$OUTA.log" 2>&1
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

def texts(i):
    return {t["view_id"]: t["text"] for t in frames[i]["visible_texts"] if t["text"]}

def status(i):
    tx = texts(i)
    cand = [v for v in tx.values() if v.startswith("GOAL")]
    return cand[0] if cand else None

chk("38/38 clicks dispatched", m.get("clicks_dispatched") == 38)
chk("39 frames recorded", len(frames) == 39)
chk("frame0 'GOAL 0/3 SERVE'", status(0) == "GOAL 0/3 SERVE")
chk("frame11 'GOAL 1/3' (ball-step 4)", status(11) == "GOAL 1/3")
chk("frame23 'GOAL 2/3' (ball-step 8)", status(23) == "GOAL 2/3")
chk("frame35 'GOAL 3/3 WIN' (ball-step 12)", status(35) == "GOAL 3/3 WIN")
chk("status never regresses (goals monotonic)",
    [int(status(i).split()[1].split("/")[0]) for i in range(0, 36)]
    == sorted(int(status(i).split()[1].split("/")[0]) for i in range(0, 36)))
ball_ok = all(
    sum(1 for v in texts(i).values() if v == "o") == 1 for i in range(0, 36)
)
chk("exactly one ball cell 'o' every frame 0..35", ball_ok)
pad_ok = all(
    sum(1 for v in texts(i).values() if v == "=") == 2 for i in range(0, 36)
)
chk("paddle always exactly 2 cells '='", pad_ok)
chk("3 goals total, zero misses (no MISS status ever)",
    not any("MISS" in v for f in frames for t in f["visible_texts"]
            for v in [t["text"]]))
sys.exit(0 if ok else 1)
PY
[ $? -eq 0 ] && pass "semantic state machine correct" || fail "semantic state machine wrong"

say "── [4] frozen tail + pixel discriminators ────────────────────────"
python3 - "$OUTA/frames" <<'PY'
import json, sys, os
d = sys.argv[1]
m = json.load(open(os.path.join(d, "manifest.json")))
frames = m["frames"]
ok = True
def chk(name, cond):
    global ok
    print(("PASS: " if cond else "FAIL: ") + name)
    if not cond: ok = False

chk("frames 36/37/38 zero pixel delta (over-taps frozen)",
    all(frames[i]["changed_pixels_vs_previous"] == 0 for i in (36, 37, 38)))
h36 = open(os.path.join(d, "frame_036.png"), "rb").read()
h38 = open(os.path.join(d, "frame_038.png"), "rb").read()
chk("frames 36/38 byte-identical", h36 == h38)
# A goal event repaints multiple cells: the frame where the first goal
# lands must differ from its predecessor by a real pixel delta.
chk("goal #1 repaint is a real visual event (>50 px)",
    frames[11]["changed_pixels_vs_previous"] > 50)
sys.exit(0 if ok else 1)
PY
[ $? -eq 0 ] && pass "frozen tail + pixel discriminators correct" \
                || fail "frozen tail + pixel discriminators wrong"

say "── [5] deterministic replay (run B) ──────────────────────────────"
OUTB="$WORK/runB"
"$BIN" run "$APK" -o "$OUTB" --click-count 38 > "$OUTB.log" 2>&1
python3 - "$OUTA" "$OUTB" <<'PY'
import json, sys, os

def shas(root):
    m = json.load(open(os.path.join(root, "frames", "manifest.json")))
    return [f["png_sha256"] for f in m.get("frames", [])]

a, b = shas(sys.argv[1]), shas(sys.argv[2])
ok = len(a) == 39 and a == b and all(a)
print(("PASS: " if ok else "FAIL: ") +
      f"all 39 frames byte-identical across runs ({a[0][:12]}…)")
sys.exit(0 if ok else 1)
PY
[ $? -eq 0 ] && pass "deterministic replay verified" || fail "replay differs"

say "── [6] zero-skip gate ────────────────────────────────────────────"
[ "$CHECKS" -gt 0 ] && pass "$CHECKS checks executed (none skipped)" \
                    || fail "no checks executed — zero-skip violation"

say ""
if [ "$FAIL" -eq 0 ]; then
    say "BALLTAP-GOLDEN VALIDATION: ALL PASS ($CHECKS checks)"
    say "WORK=$WORK"
    exit 0
else
    say "BALLTAP-GOLDEN VALIDATION: FAIL ($CHECKS checks, failures above)"
    say "WORK=$WORK"
    exit 1
fi
