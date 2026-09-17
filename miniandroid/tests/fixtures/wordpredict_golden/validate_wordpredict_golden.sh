#!/usr/bin/env bash
# validate_wordpredict_golden.sh — S51 finalization "پیش‌بینی کلمات" gate.
#
# Proves, from runtime-produced frames only:
#   1. fixture build (ECJ + D8; String[] question table + per-button
#      inner-class listeners through real DEX)
#   2. launch + 9-click sequence (6 answering taps + 3 frozen overtap) exit 0
#   3. SEMANTIC state machine (design solver table):
#        frame0  "Q1/5 SCORE 0"
#        frame1  "Q2/5 SCORE 1"
#        frame2  "Q3/5 SCORE 2"
#        frame3  "WRONG - try again. Q3/5 SCORE 2"  (engineered wrong path)
#        frame4  "Q4/5 SCORE 3"
#        frame5  "Q5/5 SCORE 4"
#        frame6  "SCORE 5/5 DONE"
#        question band re-labels per question (frame4 "Two plus two equals ___")
#   4. frozen tail: frames 7/8/9 zero pixel delta, byte-identical
#   5. deterministic replay: run B frame-for-frame byte-identical (SHA-256)
#
# Zero-skip law (§39): checks are counted; empty counts FAIL the gate.
#
# Usage: bash miniandroid/tests/fixtures/wordpredict_golden/validate_wordpredict_golden.sh \
#            [path-to-miniandroid-binary]
set -uo pipefail

BIN="${1:-build/miniandroid}"
REPO="$(cd "$(dirname "$0")/../../../.." && pwd)"
FIXTURE="$REPO/miniandroid/tests/fixtures/wordpredict_golden"
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
APK="$WORK/wordpredict_golden.apk"
if bash "$REPO/scripts/build/build_fixture_apk.sh" "$FIXTURE" "$APK" > "$WORK/build.log" 2>&1; then
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

def texts(i):
    return {t["view_id"]: t["text"] for t in frames[i]["visible_texts"] if t["text"]}

def status(i):
    tx = texts(i)
    cand = [v for v in tx.values()
            if v.startswith("Q") and "SCORE" in v or v.startswith("SCORE")
            or v.startswith("WRONG")]
    return cand[0] if cand else None

chk("9/9 clicks dispatched", m.get("clicks_dispatched") == 9)
chk("10 frames recorded", len(frames) == 10)
chk("frame0 'Q1/5 SCORE 0'", status(0) == "Q1/5 SCORE 0")
chk("frame1 'Q2/5 SCORE 1'", status(1) == "Q2/5 SCORE 1")
chk("frame2 'Q3/5 SCORE 2'", status(2) == "Q3/5 SCORE 2")
chk("frame3 WRONG path (score unchanged 2)",
    status(3) == "WRONG - try again. Q3/5 SCORE 2")
chk("frame4 'Q4/5 SCORE 3'", status(4) == "Q4/5 SCORE 3")
chk("frame5 'Q5/5 SCORE 4'", status(5) == "Q5/5 SCORE 4")
chk("frame6 'SCORE 5/5 DONE'", status(6) == "SCORE 5/5 DONE")
chk("question band re-labels (frame4 'Two plus two equals ___')",
    any(v == "Two plus two equals ___" for v in texts(4).values()))
chk("candidates re-label (frame4 carries 'five')",
    "five" in texts(4).values())
sys.exit(0 if ok else 1)
PY
[ $? -eq 0 ] && pass "semantic state machine correct" || fail "semantic state machine wrong"

say "── [4] frozen tail ───────────────────────────────────────────────"
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

chk("frames 7/8/9 zero pixel delta (over-taps frozen)",
    all(frames[i]["changed_pixels_vs_previous"] == 0 for i in (7, 8, 9)))
h7 = open(os.path.join(d, "frame_007.png"), "rb").read()
h9 = open(os.path.join(d, "frame_009.png"), "rb").read()
chk("frames 7/9 byte-identical", h7 == h9)
sys.exit(0 if ok else 1)
PY
[ $? -eq 0 ] && pass "frozen tail correct" || fail "frozen tail wrong"

say "── [5] deterministic replay (run B) ──────────────────────────────"
OUTB="$WORK/runB"
"$BIN" run "$APK" -o "$OUTB" --click-count 9 > "$OUTB.log" 2>&1
python3 - "$OUTA" "$OUTB" <<'PY'
import json, sys, os

def shas(root):
    m = json.load(open(os.path.join(root, "frames", "manifest.json")))
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
    say "WORDPREDICT-GOLDEN VALIDATION: ALL PASS ($CHECKS checks)"
    say "WORK=$WORK"
    exit 0
else
    say "WORDPREDICT-GOLDEN VALIDATION: FAIL ($CHECKS checks, failures above)"
    say "WORK=$WORK"
    exit 1
fi
