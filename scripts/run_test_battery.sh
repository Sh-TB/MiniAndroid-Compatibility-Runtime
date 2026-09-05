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
gate "mutf8 string-pool battery (expect 14)" $?
tail -1 /tmp/battery_mutf8.out

# P1 resource-configuration regression (generic default/v16/v21 law)
g++ -std=c++17 -w -g -O1 -Isrc -Ithird_party/nlohmann_json/include -o build/resource_config_selection_test \
    tests/resource_config_selection_test.cpp build/apk/*.o build/dex/*.o build/runtime/*.o \
    build/diagnostics/*.o build/resources/*.o build/renderer/*.o \
    build/fonts/*.o build/framework/*.o build/api/*.o build/storage/*.o \
    -lz -ljpeg -lwebp -lwebpdemux -lfreetype -lharfbuzz -lfribidi -lpng -lpthread \
    > /tmp/battery_rescfg.log 2>&1
gate "link resource_config_selection_test" $?
./build/resource_config_selection_test > /tmp/battery_rescfg.out 2>&1
gate "resource-config selection law (expect 19)" $?
tail -1 /tmp/battery_rescfg.out

# P2 encoded-value AOSP law (hostile/edge; FIND-REUSE-DEX)
g++ -std=c++17 -w -g -O1 -Isrc -o build/encoded_value_law_test \
    tests/encoded_value_law_test.cpp > /tmp/battery_ev.log 2>&1
gate "link encoded_value_law_test" $?
./build/encoded_value_law_test > /tmp/battery_ev.out 2>&1
gate "encoded_value AOSP law (expect 18)" $?
tail -1 /tmp/battery_ev.out

# goldens
bash tests/fixtures/helloworld_golden/validate_helloworld_golden.sh build/miniandroid \
    > /tmp/battery_hw.out 2>&1
gate "helloworld_golden (§28)" $?
grep -h "ALL PASS" /tmp/battery_hw.out | head -1

bash tests/fixtures/tictactoe_golden/validate_tictactoe_golden.sh build/miniandroid \
    > /tmp/battery_ttt.out 2>&1
gate "tictactoe_golden (§29 interaction + determinism)" $?
grep -h "ALL PASS" /tmp/battery_ttt.out | head -1

# G48: EXT-01 external APK typography golden (9 static checks, Rule 10)
EXT01_APK=/home/z/corpus/external_hello/HelloWorldSelfAware-1.1.0-android.apk
EXT01_REF=/home/z/corpus/external_hello/helloworldselfaware-android-phone-screenshot.png
EXT01_OUT=/tmp/battery_ext01
rm -rf "$EXT01_OUT"; mkdir -p "$EXT01_OUT"
if [ -f "$EXT01_APK" ] && [ -f "$EXT01_REF" ]; then
    echo "$EXT01_APK" | grep -q . && \
    ./build/miniandroid run "$EXT01_APK" -o "$EXT01_OUT" > "$EXT01_OUT/run.log" 2>&1
    gate "EXT-01 run (external APK)" $?
    python3 "$REPO/scripts/compare_ext01_typography.py" "$EXT01_REF" \
        "$EXT01_OUT/screenshot.png" --json "$EXT01_OUT/typography_golden.json" \
        > "$EXT01_OUT/compare.log" 2>&1
    gate "EXT-01 typography golden (9 static checks)" $?
    grep -h "TYPOGRAPHY GOLDEN" "$EXT01_OUT/compare.log"
else
    gate "EXT-01 typography golden (9 static checks)" 1
    echo "  (fixture missing: $EXT01_APK — fetch per docs/evidence/EXTERNAL_FIXTURE_HELLOWORLDSELFAWARE.md)"
fi

# GOLDEN-02: EXT-01 long-press interaction golden (12 static checks, Rule 10)
if [ -f "$EXT01_APK" ]; then
    EXT02_OUT=/tmp/battery_ext02
    rm -rf "$EXT02_OUT"; mkdir -p "$EXT02_OUT"
    ./build/miniandroid run "$EXT01_APK" -o "$EXT02_OUT" --long-press 540,960 \
        > "$EXT02_OUT/run.log" 2>&1
    gate "EXT-02 long-press run (external APK interaction)" $?
    python3 "$REPO/scripts/compare_ext01_interaction.py" \
        "$EXT02_OUT/frames/frame_000.png" "$EXT02_OUT/frames/frame_001.png" \
        "$EXT02_OUT/frames/manifest.json" --json "$EXT02_OUT/interaction_golden.json" \
        > "$EXT02_OUT/compare.log" 2>&1
    gate "EXT-02 interaction golden (12 static checks)" $?
    grep -h "verdict" "$EXT02_OUT/interaction_golden.json"
else
    gate "EXT-02 interaction golden (12 static checks)" 1
    echo "  (fixture missing: $EXT01_APK)"
fi

# corpus regression: real external APKs must still boot and render
CORPUS_DIR="$MA/download"
python3 "$REPO/MiniAndroid-Compatibility-Runtime/scripts/fetch_corpus.py" \
    "Simple Stopwatch" gmdice microtimer \
    > /tmp/battery_corpus_fetch.log 2>&1
CORPUS_RC=$?
gate "corpus fetch (hash-verified)" $CORPUS_RC
for rel in "exp073_real_apps/omegacentauri.mobi.simplestopwatch_26.apk" \
           "exp073_real_apps/de.duenndns.gmdice_8.apk" \
           "exp076_corpus/dubrowgn.microtimer_8.apk"; do
    name=$(basename "$rel" .apk)
    if [ -f "$CORPUS_DIR/$rel" ]; then
        out="/tmp/battery_corpus_$name"; rm -rf "$out"; mkdir -p "$out"
        ./build/miniandroid run "$CORPUS_DIR/$rel" -o "$out" \
            > "$out/run.log" 2>&1
        rc=$?
        grep -q "Status: SUCCESS" "$out/run.log" && [ -f "$out/screenshot.png" ] && rc=0 || rc=1
        gate "corpus run $name" $rc
    else
        gate "corpus run $name" 1
    fi
done

echo "──────────────────────────────────────────────"
for r in "${RESULTS[@]}"; do printf '%s\n' "$r"; done
if [ $FAIL -eq 0 ]; then
    echo "BATTERY GATE: ALL PASS ($STAGE stages)"
    exit 0
else
    echo "BATTERY GATE: FAILURES PRESENT ($STAGE stages)"
    exit 1
fi
