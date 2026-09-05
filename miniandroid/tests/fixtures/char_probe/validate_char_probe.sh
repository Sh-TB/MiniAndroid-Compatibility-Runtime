#!/usr/bin/env bash
# validate_char_probe.sh — pins primitive-type semantics at invoke boundaries.
#
# Discriminates (per construct, one TextView line each):
#   P1 f=X        char field concat (String.valueOf(char) via StringBuilder)
#   P2 branch=TX  ternary on char == 'X' (true branch)
#   P3 f2=O       char flip assignment through synthetic accessor
#   P4 branch=TO  ternary false branch after flip
#   P5 b0=O       aput-char/aget-char through char[]
#   P6 eq=true    char[] element == flipped field (cross-type compare)
#   P7 w=false    wins() pattern over non-winning board (boolean return)
#   P8 w2=true    wins() pattern over a real row
#
# History: before the signature-aware fixes the probe rendered
# "P1 f=88", "P6 eq=1", "P7 w=0" and a char param compared as 0 made EMPTY
# CELLS match a win check — the same law as EXP-093's if-eqz zero fix.
#
# Usage: bash miniandroid/tests/fixtures/char_probe/validate_char_probe.sh \
#            [path-to-miniandroid-binary]
set -uo pipefail

BIN="${1:-build/miniandroid}"
REPO="$(cd "$(dirname "$0")/../../../.." && pwd)"
FIXTURE="$REPO/miniandroid/tests/fixtures/char_probe"
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
APK="$WORK/charprobe.apk"
if bash "$REPO/scripts/build_fixture_apk.sh" "$FIXTURE" "$APK" > "$WORK/build.log" 2>&1; then
    pass "build_fixture_apk: ECJ + D8 + package OK"
else
    fail "build_fixture_apk failed"; cat "$WORK/build.log"; exit 1
fi

say "── [2] run + render all 8 probe lines ────────────────────────────"
OUT="$WORK/run"
"$BIN" run "$APK" -o "$OUT" -v > "$OUT.log" 2>&1
[ $? -eq 0 ] && pass "run exit 0" || fail "run exit nonzero"

say "── [3] probe discriminators ──────────────────────────────────────"
python3 - "$OUT.log" <<'PY'
import re, sys

log = open(sys.argv[1], encoding="utf-8", errors="replace").read()
got = re.findall(r'\[EXP091-SETTEXT\].*text="([^"]+)"', log)
want = ["P1 f=X", "P2 branch=TX", "P3 f2=O", "P4 branch=TO",
        "P5 b0=O", "P6 eq=true", "P7 w=false", "P8 w2=true"]
ok = True
for w in want:
    hit = w in got
    print(("PASS: " if hit else "FAIL: ") + f'"{w}" rendered')
    if not hit: ok = False
sys.exit(0 if ok else 1)
PY
[ $? -eq 0 ] && pass "all primitive-type discriminators correct" \
              || fail "primitive-type discriminators wrong"

say "── [4] zero-skip gate ────────────────────────────────────────────"
[ "$CHECKS" -gt 0 ] && pass "$CHECKS checks executed (none skipped)" \
                    || fail "no checks executed — zero-skip violation"

say ""
if [ "$FAIL" -eq 0 ]; then
    say "CHAR-PROBE VALIDATION: ALL PASS ($CHECKS checks)"
    exit 0
else
    say "CHAR-PROBE VALIDATION: FAIL ($CHECKS checks, failures above)"
    exit 1
fi
