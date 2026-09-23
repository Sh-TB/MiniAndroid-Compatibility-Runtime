#!/usr/bin/env bash
# validate_crossword_golden.sh — S51 finalization "board game" golden gate.
#
# Proves, from runtime-produced frames only:
#   1. fixture build (ECJ + D8, real 5x5 interlocked crossword through DEX)
#   2. launch + 11-click sequence (9 fills + 2 frozen overtap) exit 0
#   3. SEMANTIC state machine (design solver table):
#        frame0  "WORDS 0/3 FILLED 0/9"
#        frame1  "WORDS 0/3 FILLED 1/9"
#        frame4  "WORDS 1/3 FILLED 4/9"   (PROP completes first)
#        frame9  "SOLVED!"                 (BEAM completes last)
#        final grid carries B,E,A,M,A,P,R,O,P — the real interlock
#   4. frozen tail: frames 10/11 zero pixel delta (over-taps are no-ops)
#   5. deterministic replay: run B frame-for-frame byte-identical (SHA-256)
#
# Zero-skip law (§39): checks are counted; empty counts FAIL the gate.
#
# Usage: bash miniandroid/tests/fixtures/crossword_golden/validate_crossword_golden.sh \
#            [path-to-miniandroid-binary]
set -uo pipefail

BIN="${1:-build/miniandroid}"
REPO="$(cd "$(dirname "$0")/../../../.." && pwd)"
FIXTURE="$REPO/miniandroid/tests/fixtures/crossword_golden"
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
APK="$WORK/crossword_golden.apk"
if bash "$REPO/scripts/build/build_fixture_apk.sh" "$FIXTURE" "$APK" > "$WORK/build.log" 2>&1; then
    pass "build_fixture_apk: ECJ + D8 + package OK"
    APK_SHA=$(grep '^SHA256:' "$WORK/build.log" | cut -d' ' -f2)
    [ -n "$APK_SHA" ] && pass "APK SHA256 = $APK_SHA" || fail "APK hash missing"
else
    fail "build_fixture_apk failed (see $WORK/build.log)"; cat "$WORK/build.log"
    exit 1
fi

say "── [2] run A: launch + 11 clicks ─────────────────────────────────"
OUTA="$WORK/runA"
"$BIN" run "$APK" -o "$OUTA" --click-count 11 > "$OUTA.log" 2>&1
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
    cand = [v for v in tx.values() if v.startswith("WORDS") or v == "SOLVED!"]
    return cand[0] if cand else None

chk("11/11 clicks dispatched", m.get("clicks_dispatched") == 11)
chk("12 frames recorded", len(frames) == 12)
chk("frame0 'WORDS 0/3 FILLED 0/9'", status(0) == "WORDS 0/3 FILLED 0/9")
chk("frame1 'WORDS 0/3 FILLED 1/9'", status(1) == "WORDS 0/3 FILLED 1/9")
chk("frame4 'WORDS 1/3 FILLED 4/9' (PROP completes first)",
    status(4) == "WORDS 1/3 FILLED 4/9")
chk("frame9 'SOLVED!'", status(9) == "SOLVED!")
t9 = texts(9)
letters = sorted(v for v in t9.values() if len(v) == 1 and v.isalpha())
chk("final grid letters exactly A,A,B,E,M,O,P,P,R",
    letters == sorted("BEAMAPROP"))
chk("clue band rendered", any("ACROSS" in v for v in t9.values()))
sys.exit(0 if ok else 1)
PY
[ $? -eq 0 ] && pass "semantic state machine correct" || fail "semantic state machine wrong"

say "── [4] frozen tail + pixel delta ─────────────────────────────────"
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

chk("frames 10/11 zero pixel delta (over-taps frozen)",
    frames[10]["changed_pixels_vs_previous"] == 0 and
    frames[11]["changed_pixels_vs_previous"] == 0)
h10 = open(os.path.join(d, "frame_010.png"), "rb").read()
h11 = open(os.path.join(d, "frame_011.png"), "rb").read()
chk("frames 10/11 byte-identical", h10 == h11)
d0 = frames[1]["changed_pixels_vs_previous"]
chk("first fill changed real pixels (>500)", d0 > 500)
sys.exit(0 if ok else 1)
PY
[ $? -eq 0 ] && pass "frozen tail + pixel discriminators correct" \
                || fail "frozen tail + pixel discriminators wrong"

say "── [5] deterministic replay (run B) ──────────────────────────────"
OUTB="$WORK/runB"
"$BIN" run "$APK" -o "$OUTB" --click-count 11 > "$OUTB.log" 2>&1
python3 - "$OUTA" "$OUTB" <<'PY'
import json, sys, os

def shas(root):
    m = json.load(open(os.path.join(root, "frames", "manifest.json")))
    return [f["png_sha256"] for f in m.get("frames", [])]

a, b = shas(sys.argv[1]), shas(sys.argv[2])
ok = len(a) == 12 and a == b and all(a)
print(("PASS: " if ok else "FAIL: ") +
      f"all 12 frames byte-identical across runs ({a[0][:12]}…)")
sys.exit(0 if ok else 1)
PY
[ $? -eq 0 ] && pass "deterministic replay verified" || fail "replay differs"

say "── [6] zero-skip gate ────────────────────────────────────────────"
[ "$CHECKS" -gt 0 ] && pass "$CHECKS checks executed (none skipped)" \
                    || fail "no checks executed — zero-skip violation"

say ""
if [ "$FAIL" -eq 0 ]; then
    say "CROSSWORD-GOLDEN VALIDATION: ALL PASS ($CHECKS checks)"
    say "WORK=$WORK"
    exit 0
else
    say "CROSSWORD-GOLDEN VALIDATION: FAIL ($CHECKS checks, failures above)"
    say "WORK=$WORK"
    exit 1
fi
