#!/usr/bin/env bash
# run_test_battery.sh — REUSE-FIRST CAMPAIGN §12 automation gate.
#
# ONE command that rebuilds and runs the ENTIRE regression gate:
#   1. make build (clean source→binary binding; BUILD_ID = git HEAD)
#   2. semantic battery: long/cmp/conv + pass3 bridge (incl. WineDroid
#      discriminators) + switch parse-neg
#   3. MUTF-8 string-pool battery (FIND-REUSE-001)
#   4. helloworld_golden §28 validation (18 checks)
#   5. tictactoe_golden §29 validation (interaction + determinism)
#
# Zero-skip law: every stage must EXECUTE; PASS 0 / FAIL 0 is a failure.
# Usage: bash scripts/run_test_battery.sh [--skip-build]
set -uo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
MA="$REPO/MiniAndroid-Compatibility-Runtime/miniandroid"
cd "$MA"

FAIL=0
STAGE=0
declare -a RESULTS

gate() {  # gate <name> <rc>
    STAGE=$((STAGE+1))
    if [ "$2" -eq 0 ]; then
        RESULTS+=("PASS  $1")
        printf '  [%d] PASS  %s\n' "$STAGE" "$1"
    else
        FAIL=1
        RESULTS+=("FAIL  $1 (rc=$2)")
        printf '  [%d] FAIL  %s (rc=%s)\n' "$STAGE" "$1" "$2"
    fi
}

echo "── run_test_battery @ $(git -C "$REPO" rev-parse --short HEAD) ──"

if [ "${1:-}" != "--skip-build" ]; then
    make -j"$(nproc)" > /tmp/battery_build.log 2>&1
    gate "build (make -j)" $?
fi

# semantic battery binaries (relinked against current objects)
for t in semantic_long_cmp_conv_test semantic_switch_parse_neg_test semantic_pass3_bridge_test; do
    g++ -std=c++17 -w -g -O2 -Isrc -Ithird_party/nlohmann_json/include -o "build/$t" \
        "tests/$t.cpp" build/apk/*.o build/dex/*.o build/runtime/*.o \
        build/diagnostics/*.o build/resources/*.o build/renderer/*.o \
        build/fonts/*.o build/framework/*.o build/api/*.o build/storage/*.o \
        -lz -ljpeg -lwebp -lwebpdemux -lfreetype -lharfbuzz -lfribidi -lpng -lpthread \
        > "/tmp/battery_$t.log" 2>&1
    gate "link $t" $?
done

./build/semantic_long_cmp_conv_test > /tmp/battery_lcc.out 2>&1
gate "semantic long/cmp/conv (expect 14)" $?
./build/semantic_switch_parse_neg_test > /tmp/battery_swpn.out 2>&1
gate "semantic switch parse-neg (expect 25)" $?
./build/semantic_pass3_bridge_test > /tmp/battery_p3b.out 2>&1
gate "semantic pass3 bridge (expect 57)" $?
tail -1 /tmp/battery_lcc.out /tmp/battery_swpn.out /tmp/battery_p3b.out 2>/dev/null | grep RESULT

# MUTF-8 battery
g++ -std=c++17 -w -g -O1 -Isrc -Ithird_party/nlohmann_json/include -o build/mutf8_test \
    tests/mutf8_string_pool_test.cpp build/apk/*.o build/dex/*.o build/runtime/*.o \
    build/diagnostics/*.o build/resources/*.o build/renderer/*.o \
    build/fonts/*.o build/framework/*.o build/api/*.o build/storage/*.o \
    -lz -ljpeg -lwebp -lwebpdemux -lfreetype -lharfbuzz -lfribidi -lpng -lpthread \
    > /tmp/battery_mutf8.log 2>&1
gate "link mutf8_test" $?
./build/mutf8_test > /tmp/battery_mutf8.out 2>&1
gate "mutf8 string-pool battery (expect 7)" $?
tail -1 /tmp/battery_mutf8.out

# goldens
bash tests/fixtures/helloworld_golden/validate_helloworld_golden.sh build/miniandroid \
    > /tmp/battery_hw.out 2>&1
gate "helloworld_golden (§28)" $?
grep -h "ALL PASS" /tmp/battery_hw.out | head -1

bash tests/fixtures/tictactoe_golden/validate_tictactoe_golden.sh build/miniandroid \
    > /tmp/battery_ttt.out 2>&1
gate "tictactoe_golden (§29 interaction + determinism)" $?
grep -h "ALL PASS" /tmp/battery_ttt.out | head -1

echo "──────────────────────────────────────────────"
for r in "${RESULTS[@]}"; do printf '%s\n' "$r"; done
if [ $FAIL -eq 0 ]; then
    echo "BATTERY GATE: ALL PASS ($STAGE stages)"
    exit 0
else
    echo "BATTERY GATE: FAILURES PRESENT ($STAGE stages)"
    exit 1
fi
