#!/usr/bin/env bash
# validate_minesweep_golden.sh — S51 finalization XP-style mine-finder gate.
#
# Proves, from runtime-produced frames only:
#   1. fixture build (ECJ + D8; 9x9 grid, fixed mines, iterative DFS flood
#      fill through real DEX)
#   2. launch + 66-click sequence (64 to WIN + 2 frozen overtap) exit 0
#   3. SEMANTIC state machine (design solver table):
#        frame0  "MINES 10 SAFE 0/71"
#        frame63 "MINES 10 SAFE 70/71"
#        frame64 "MINES 10 SAFE 71/71 WIN"
#        flood fill: safe count jumps >1 on zero-cell taps (fill law)
#        zero BOOM: no "*" mine render in any frame (first tap safe, XP law)
#   4. frozen tail: frames 65/66 zero pixel delta, byte-identical
#   5. deterministic replay: run B frame-for-frame byte-identical (SHA-256)
#
# Zero-skip law (§39): checks are counted; empty counts FAIL the gate.
#
# Usage: bash miniandroid/tests/fixtures/minesweep_golden/validate_minesweep_golden.sh \
#            [path-to-miniandroid-binary]
set -uo pipefail

BIN="${1:-build/miniandroid}"
REPO="$(cd "$(dirname "$0")/../../../.." && pwd)"
FIXTURE="$REPO/miniandroid/tests/fixtures/minesweep_golden"
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
APK="$WORK/minesweep_golden.apk"
if bash "$REPO/scripts/build/build_fixture_apk.sh" "$FIXTURE" "$APK" > "$WORK/build.log" 2>&1; then
    pass "build_fixture_apk: ECJ + D8 + package OK"
    APK_SHA=$(grep '^SHA256:' "$WORK/build.log" | cut -d' ' -f2)
    [ -n "$APK_SHA" ] && pass "APK SHA256 = $APK_SHA" || fail "APK hash missing"
else
    fail "build_fixture_apk failed (see $WORK/build.log)"; cat "$WORK/build.log"
    exit 1
fi

say "── [2] run A: launch + 66 clicks ─────────────────────────────────"
OUTA="$WORK/runA"
"$BIN" run "$APK" -o "$OUTA" --click-count 66 > "$OUTA.log" 2>&1
rc=$?
[ $rc -eq 0 ] && pass "run exit 0" || fail "run exit $rc"
[ -f "$OUTA/frames/manifest.json" ] && pass "frames manifest produced" \
                                    || fail "frames manifest missing"

say "── [3] semantic state machine (real DEX listeners) ───────────────"
python3 - "$OUTA/frames/manifest.json" <<'PY'
import json, re, sys

m = json.load(open(sys.argv[1]))
frames = m.get("frames", [])
ok = True
def chk(name, cond):
    global ok
    print(("PASS: " if cond else "FAIL: ") + name)
    if not cond: ok = False

def status(i):
    tx = {t["view_id"]: t["text"] for t in frames[i]["visible_texts"] if t["text"]}
    cand = [v for v in tx.values() if v.startswith("MINES") or v.startswith("BOOM")]
    return cand[0] if cand else None

def safe_count(i):
    s = status(i)
    mm = re.search(r"SAFE (\d+)/71", s or "")
    return int(mm.group(1)) if mm else -1

chk("66/66 clicks dispatched", m.get("clicks_dispatched") == 66)
chk("67 frames recorded", len(frames) == 67)
chk("frame0 'MINES 10 SAFE 0/71'", status(0) == "MINES 10 SAFE 0/71")
chk("frame63 'MINES 10 SAFE 70/71'", status(63) == "MINES 10 SAFE 70/71")
chk("frame64 'MINES 10 SAFE 71/71 WIN'", status(64) == "MINES 10 SAFE 71/71 WIN")
seq = [safe_count(i) for i in range(0, 65)]
chk("safe count monotonic non-decreasing", seq == sorted(seq))
chk("flood fill law: count jumps >1 on zero-cell reveals",
    any(seq[i + 1] - seq[i] > 1 for i in range(64)))
chk("final count exactly 71/71", seq[-1] == 71)
star = any(t["text"] == "*" for f in frames for t in f["visible_texts"])
chk("no mine revealed in the golden sequence (XP first-tap-safe law)",
    not star)
chk("no BOOM status ever", not any(status(i) and "BOOM" in status(i)
                                   for i in range(len(frames))))
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

chk("frames 65/66 zero pixel delta (over-taps frozen)",
    all(frames[i]["changed_pixels_vs_previous"] == 0 for i in (65, 66)))
h65 = open(os.path.join(d, "frame_065.png"), "rb").read()
h66 = open(os.path.join(d, "frame_066.png"), "rb").read()
chk("frames 65/66 byte-identical", h65 == h66)
chk("win repaint is a real visual event (>50 px at frame 64)",
    frames[64]["changed_pixels_vs_previous"] > 50)
sys.exit(0 if ok else 1)
PY
[ $? -eq 0 ] && pass "frozen tail correct" || fail "frozen tail wrong"

say "── [5] deterministic replay (run B) ──────────────────────────────"
OUTB="$WORK/runB"
"$BIN" run "$APK" -o "$OUTB" --click-count 66 > "$OUTB.log" 2>&1
python3 - "$OUTA" "$OUTB" <<'PY'
import json, sys, os

def shas(root):
    m = json.load(open(os.path.join(root, "frames", "manifest.json")))
    return [f["png_sha256"] for f in m.get("frames", [])]

a, b = shas(sys.argv[1]), shas(sys.argv[2])
ok = len(a) == 67 and a == b and all(a)
print(("PASS: " if ok else "FAIL: ") +
      f"all 67 frames byte-identical across runs ({a[0][:12]}…)")
sys.exit(0 if ok else 1)
PY
[ $? -eq 0 ] && pass "deterministic replay verified" || fail "replay differs"

say "── [6] zero-skip gate ────────────────────────────────────────────"
[ "$CHECKS" -gt 0 ] && pass "$CHECKS checks executed (none skipped)" \
                    || fail "no checks executed — zero-skip violation"

say ""
if [ "$FAIL" -eq 0 ]; then
    say "MINESWEEP-GOLDEN VALIDATION: ALL PASS ($CHECKS checks)"
    say "WORK=$WORK"
    exit 0
else
    say "MINESWEEP-GOLDEN VALIDATION: FAIL ($CHECKS checks, failures above)"
    say "WORK=$WORK"
    exit 1
fi
