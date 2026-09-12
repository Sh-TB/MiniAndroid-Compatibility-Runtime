#!/usr/bin/env bash
# validate_f078_arraycopy.sh — pins java.lang.System.arraycopy semantics.
#
# Discriminates (per construct, one TextView line each):
#   C1 plain=1,2,3,4          distinct-array copy
#   C2 shift=1,2,1,2,3,4,5    same-array RIGHT-shift by 2 (temp-copy/memmove
#                             law — kotlin copyInto, TrieNode insert); a
#                             naive forward loop yields 1,2,1,2,1,2,1
#   C3 lshift=2,3,4,5,5       same-array left-shift by 1 (ArrayList remove)
#   C4 mid=1,2,7,8,9,3,4,5    ArrayList-style mid-insert through a shift
#   C5 grow=k0,v0,k2,v2,k1,v1 the EXACT kotlinx TrieNode mutableInsertEntryAt
#                             sequence: Arrays.copyOf grow + same-array
#                             shift + store — buffer invariant, no nulls
#                             (F-077 dooz root cause)
#   C6 npe=CAUGHT             null dst → NullPointerException
#   C7 oob=CAUGHT             bounds → ArrayIndexOutOfBoundsException
#   C8 ints=9,2,3             primitive int[] copy
#
# Usage: bash miniandroid/tests/fixtures/f078_arraycopy/validate_f078_arraycopy.sh \
#            [path-to-miniandroid-binary]
set -uo pipefail

BIN="${1:-build/miniandroid}"
REPO="$(cd "$(dirname "$0")/../../../.." && pwd)"
FIXTURE="$REPO/miniandroid/tests/fixtures/f078_arraycopy"
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
APK="$WORK/f078arraycopy.apk"
if bash "$REPO/scripts/build/build_fixture_apk.sh" "$FIXTURE" "$APK" > "$WORK/build.log" 2>&1; then
    pass "build_fixture_apk: ECJ + D8 + package OK"
else
    fail "build_fixture_apk failed"; cat "$WORK/build.log"; exit 1
fi

say "── [2] run + render all 8 probe lines ────────────────────────────"
OUT="$WORK/run"
"$BIN" run "$APK" -o "$OUT" -v > "$OUT.log" 2>&1
[ $? -eq 0 ] && pass "run exit 0" || fail "run exit nonzero"

check_line() { # check_line <label> <expected> <logfile>
    local label="$1" want="$2" log="$3"
    if grep -q "$label=$want" "$log"; then
        pass "$label=$want"
    else
        local got
        got=$(grep -oE "$label=[^ ]*" "$log" | head -1)
        fail "$label expected '$want' got '${got:-<absent>}'"
    fi
}

check_line "C1 plain"  "1,2,3,4"          "$OUT.log"
check_line "C2 shift"  "1,2,1,2,3,4,5"    "$OUT.log"
check_line "C3 lshift" "2,3,4,5,5"        "$OUT.log"
check_line "C4 mid"    "1,2,7,8,9,5,8,9"  "$OUT.log"
check_line "C5 grow"   "k0,v0,k2,v2,k1,v1" "$OUT.log"
check_line "C6 npe"    "CAUGHT"           "$OUT.log"
check_line "C7 oob"    "CAUGHT"           "$OUT.log"
check_line "C8 ints"   "9,2,3"            "$OUT.log"

say "── [3] determinism ───────────────────────────────────────────────"
OUT2="$WORK/run2"
"$BIN" run "$APK" -o "$OUT2" > /dev/null 2>&1
if [ -f "$OUT/screenshot.png" ] && [ -f "$OUT2/screenshot.png" ]; then
    h1=$(sha256sum "$OUT/screenshot.png" | cut -d' ' -f1)
    h2=$(sha256sum "$OUT2/screenshot.png" | cut -d' ' -f1)
    [ "$h1" = "$h2" ] && pass "screenshots byte-identical ($h1)" \
                      || fail "screenshot SHA mismatch: $h1 vs $h2"
else
    fail "missing screenshot artifacts"
fi

printf '\n'
if [ "$FAIL" -eq 0 ]; then
    say "F-078 arraycopy probe: VALIDATION_PASS ($CHECKS checks)"
    exit 0
else
    say "F-078 arraycopy probe: VALIDATION_FAIL ($CHECKS checks)"
    exit 1
fi
