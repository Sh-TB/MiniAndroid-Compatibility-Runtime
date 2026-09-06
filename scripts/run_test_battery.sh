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

# G09 resume support: each PASSing stage is checkpointed to a state dir so a
# killed/interrupted run can resume without re-executing stages that already
# PASSED at the SAME HEAD (recorded inside the state dir). --resume enables it.
RESUME=0
[ "${1:-}" = "--resume" ] && RESUME=1
[ "${1:-}" = "--skip-build" ] && RESUME=1   # legacy flag keeps old meaning
STATE="${G09_BATTERY_STATE:-/tmp/g09_battery_state}"
HEADSHORT="$(git -C "$REPO" rev-parse --short HEAD)"
if [ "$RESUME" -eq 1 ]; then
    if [ -f "$STATE/HEAD" ] && [ "$(cat "$STATE/HEAD")" != "$HEADSHORT" ]; then
        echo "state dir is for HEAD $(cat "$STATE/HEAD"), current $HEADSHORT — resetting"
        rm -rf "$STATE"
    fi
    mkdir -p "$STATE"; echo "$HEADSHORT" > "$STATE/HEAD"
fi

FAIL=0
STAGE=0
declare -a RESULTS

gate() {  # gate <name> <rc>
    STAGE=$((STAGE+1))
    if [ "$2" -eq 0 ]; then
        RESULTS+=("PASS  $1")
        printf '  [%d] PASS  %s\n' "$STAGE" "$1"
        [ "$RESUME" -eq 1 ] && echo "$1" > "$STATE/$(printf '%02d' $STAGE).pass"
    else
        FAIL=1
        RESULTS+=("FAIL  $1 (rc=$2)")
        printf '  [%d] FAIL  %s (rc=%s)\n' "$STAGE" "$1" "$2"
    fi
}

cached() {  # cached <name> -> rc 0 if stage already PASSED at this HEAD
    [ "$RESUME" -eq 1 ] || return 1
    local f
    for f in "$STATE"/*.pass; do
        [ -f "$f" ] || return 1
        if [ "$(cat "$f")" = "$1" ]; then return 0; fi
    done
    return 1
}

skip() {  # skip <name> — stage already PASSED at this HEAD (resume mode)
    STAGE=$((STAGE+1))
    RESULTS+=("CACHED-PASS  $1 (same-HEAD resume)")
    printf '  [%d] CACHED  %s\n' "$STAGE" "$1"
}

echo "── run_test_battery @ $HEADSHORT (resume=$RESUME) ──"

if [ "$RESUME" -eq 0 ] || [ "${1:-}" != "--skip-build" ]; then
    if cached "build (make -j)"; then skip "build (make -j)"; else
    make -j"$(nproc)" > /tmp/battery_build.log 2>&1
    gate "build (make -j)" $?; fi
    if cached "build (make resource_trace)"; then skip "build (make resource_trace)"; else
    # FIND-G06AUDIT-001 fix: the density-oracle stage needs resource_trace;
    # build it with the same make invocation (separate target) so a clean
    # checkout never fails stage 27 for an environment gap.
    make resource_trace >> /tmp/battery_build.log 2>&1
    gate "build (make resource_trace)" $?; fi
fi

# semantic battery binaries (relinked against current objects)
if cached "semantic pass3 bridge (expect 57)"; then
    skip "link semantic_long_cmp_conv_test"; skip "semantic long/cmp/conv (expect 14)"
    skip "link semantic_switch_parse_neg_test"; skip "semantic switch parse-neg (expect 25)"
    skip "link semantic_pass3_bridge_test"; skip "semantic pass3 bridge (expect 57)"
else
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
fi

# MUTF-8 battery
if cached "mutf8 string-pool battery (expect 14)"; then
    skip "link mutf8_test"; skip "mutf8 string-pool battery (expect 14)"
else
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
fi

# P1 resource-configuration regression (generic default/v16/v21 law)
if cached "resource-config selection law (expect 48)"; then
    skip "link resource_config_selection_test"; skip "resource-config selection law (expect 48)"
else
g++ -std=c++17 -w -g -O1 -Isrc -Ithird_party/nlohmann_json/include -o build/resource_config_selection_test \
    tests/resource_config_selection_test.cpp build/apk/*.o build/dex/*.o build/runtime/*.o \
    build/diagnostics/*.o build/resources/*.o build/renderer/*.o \
    build/fonts/*.o build/framework/*.o build/api/*.o build/storage/*.o \
    -lz -ljpeg -lwebp -lwebpdemux -lfreetype -lharfbuzz -lfribidi -lpng -lpthread \
    > /tmp/battery_rescfg.log 2>&1
gate "link resource_config_selection_test" $?
./build/resource_config_selection_test > /tmp/battery_rescfg.out 2>&1
gate "resource-config selection law (expect 48)" $?
tail -1 /tmp/battery_rescfg.out
fi

# GOLDEN-03 §3/§4/§6/§7/§8/§9: canonical id/resolution/TypedValue law
if cached "resource core law (expect 42)"; then
    skip "link resource_core_law_test"; skip "resource core law (expect 42)"
else
g++ -std=c++17 -w -g -O1 -Isrc -Ithird_party/nlohmann_json/include -o build/resource_core_law_test \
    tests/resource_core_law_test.cpp build/apk/*.o build/dex/*.o build/runtime/*.o \
    build/diagnostics/*.o build/resources/*.o build/renderer/*.o \
    build/fonts/*.o build/framework/*.o build/api/*.o build/storage/*.o \
    -lz -ljpeg -lwebp -lwebpdemux -lfreetype -lharfbuzz -lfribidi -lpng -lpthread \
    > /tmp/battery_reslaw.log 2>&1
gate "link resource_core_law_test" $?
./build/resource_core_law_test > /tmp/battery_reslaw.out 2>&1
gate "resource core law (expect 42)" $?
tail -1 /tmp/battery_reslaw.out
fi

# GOLDEN-03 §14: hostile resource-table safety (named deterministic failures)
if cached "resource hostile safety (expect 18)"; then
    skip "link resource_hostile_test"; skip "resource hostile safety (expect 18)"
else
g++ -std=c++17 -w -g -O1 -Isrc -Ithird_party/nlohmann_json/include -o build/resource_hostile_test \
    tests/resource_hostile_test.cpp build/apk/*.o build/dex/*.o build/runtime/*.o \
    build/diagnostics/*.o build/resources/*.o build/renderer/*.o \
    build/fonts/*.o build/framework/*.o build/api/*.o build/storage/*.o \
    -lz -ljpeg -lwebp -lwebpdemux -lfreetype -lharfbuzz -lfribidi -lpng -lpthread \
    > /tmp/battery_hostile.log 2>&1
gate "link resource_hostile_test" $?
timeout 120 ./build/resource_hostile_test > /tmp/battery_hostile.out 2>&1
gate "resource hostile safety (expect 18)" $?
tail -1 /tmp/battery_hostile.out
fi

# G04/G05 §8/§9: MeasureSpec + LinearLayout weight law battery
if cached "LinearLayout/MeasureSpec law (expect 24)"; then
    skip "link linear_layout_law_test"; skip "LinearLayout/MeasureSpec law (expect 24)"
else
g++ -std=c++17 -w -g -O1 -Isrc -o build/linear_layout_law_test \
    tests/linear_layout_law_test.cpp build/apk/*.o build/dex/*.o build/runtime/*.o \
    build/diagnostics/*.o build/resources/*.o build/renderer/*.o \
    build/fonts/*.o build/framework/*.o build/api/*.o build/storage/*.o \
    -lz -ljpeg -lwebp -lwebpdemux -lfreetype -lharfbuzz -lfribidi -lpng -lpthread \
    > /tmp/battery_lllaw.log 2>&1
gate "link linear_layout_law_test" $?
./build/linear_layout_law_test > /tmp/battery_lllaw.out 2>&1
gate "LinearLayout/MeasureSpec law (expect 24)" $?
tail -1 /tmp/battery_lllaw.out
fi

# G10: measurement/layout law battery (orientation default, superclass-chain
# classification, gravity axis-field equality, hostile geometry safety)
if cached "link g10_layout_law_test"; then
    skip "link g10_layout_law_test"; skip "G10 measurement/layout law (expect 23)"
else
g++ -std=c++17 -w -g -O1 -Isrc -o build/g10_layout_law_test \
    tests/g10_layout_law_test.cpp build/apk/*.o build/dex/*.o build/runtime/*.o \
    build/diagnostics/*.o build/resources/*.o build/renderer/*.o \
    build/fonts/*.o build/framework/*.o build/api/*.o build/storage/*.o \
    -lz -ljpeg -lwebp -lwebpdemux -lfreetype -lharfbuzz -lfribidi -lpng -lpthread \
    > /tmp/battery_g10law.log 2>&1
gate "link g10_layout_law_test" $?
./build/g10_layout_law_test > /tmp/battery_g10law.out 2>&1
gate "G10 measurement/layout law (expect 23)" $?
tail -1 /tmp/battery_g10law.out
fi

# G04/G05 §16: hostile drawable/image/layout safety battery
if cached "G04 hostile safety (expect 24)"; then
    skip "link g04_hostile_test"; skip "G04 hostile safety (expect 24)"
else
g++ -std=c++17 -w -g -O1 -Isrc -Itests -o build/g04_hostile_test \
    tests/g04_hostile_test.cpp build/apk/*.o build/dex/*.o build/runtime/*.o \
    build/diagnostics/*.o build/resources/*.o build/renderer/*.o \
    build/fonts/*.o build/framework/*.o build/api/*.o build/storage/*.o \
    -lz -ljpeg -lwebp -lwebpdemux -lfreetype -lharfbuzz -lfribidi -lpng -lpthread \
    > /tmp/battery_g04h.log 2>&1
gate "link g04_hostile_test" $?
timeout 60 ./build/g04_hostile_test > /tmp/battery_g04h.out 2>&1
gate "G04 hostile safety (expect 24)" $?
tail -1 /tmp/battery_g04h.out
fi

# G06 §4/§5: canonical input pipeline law battery (touch dispatcher +
# state-list pick law + disabled/focus/cancel/move laws, 45 checks)
if cached "G06 input pipeline law (expect 45)"; then
    skip "link input_pipeline_law_test"; skip "G06 input pipeline law (expect 45)"
else
g++ -std=c++17 -w -g -O1 -Isrc -Ithird_party/nlohmann_json/include -o build/input_pipeline_law_test \
    tests/input_pipeline_law_test.cpp build/apk/*.o build/dex/*.o build/runtime/*.o \
    build/diagnostics/*.o build/resources/*.o build/renderer/*.o \
    build/fonts/*.o build/framework/*.o build/api/*.o build/storage/*.o \
    -lz -ljpeg -lwebp -lwebpdemux -lfreetype -lharfbuzz -lfribidi -lpng -lpthread \
    > /tmp/battery_g06law.log 2>&1
gate "link input_pipeline_law_test" $?
timeout 120 ./build/input_pipeline_law_test > /tmp/battery_g06law.out 2>&1
gate "G06 input pipeline law (expect 45)" $?
tail -1 /tmp/battery_g06law.out
fi

# G07 §7/§8/§10: lifecycle state machine + MessageQueue ordering law battery
if cached "G07 lifecycle law (expect 25)"; then
    skip "link lifecycle_law_test"; skip "G07 lifecycle law (expect 25)"
else
g++ -std=c++17 -w -g -O1 -Isrc -Ithird_party/nlohmann_json/include -o build/lifecycle_law_test \
    tests/lifecycle_law_test.cpp build/apk/*.o build/dex/*.o build/runtime/*.o \
    build/diagnostics/*.o build/resources/*.o build/renderer/*.o \
    build/fonts/*.o build/framework/*.o build/api/*.o build/storage/*.o \
    -lz -ljpeg -lwebp -lwebpdemux -lfreetype -lharfbuzz -lfribidi -lpng -lpthread \
    > /tmp/battery_g07law.log 2>&1
gate "link lifecycle_law_test" $?
timeout 120 ./build/lifecycle_law_test > /tmp/battery_g07law.out 2>&1
gate "G07 lifecycle law (expect 25)" $?
tail -1 /tmp/battery_g07law.out
fi

# G06-G08 §18: hostile input/lifecycle/queue-safety battery
if cached "G06-G08 hostile safety (expect 16)"; then
    skip "link g06g08_hostile_test"; skip "G06-G08 hostile safety (expect 16)"
else
g++ -std=c++17 -w -g -O1 -Isrc -Ithird_party/nlohmann_json/include -o build/g06g08_hostile_test \
    tests/g06g08_hostile_test.cpp build/apk/*.o build/dex/*.o build/runtime/*.o \
    build/diagnostics/*.o build/resources/*.o build/renderer/*.o \
    build/fonts/*.o build/framework/*.o build/api/*.o build/storage/*.o \
    -lz -ljpeg -lwebp -lwebpdemux -lfreetype -lharfbuzz -lfribidi -lpng -lpthread \
    > /tmp/battery_h18.log 2>&1
gate "link g06g08_hostile_test" $?
timeout 120 ./build/g06g08_hostile_test > /tmp/battery_h18.out 2>&1
gate "G06-G08 hostile safety (expect 16)" $?
tail -1 /tmp/battery_h18.out
fi

# P2 encoded-value AOSP law (hostile/edge; FIND-REUSE-DEX)
if cached "encoded_value AOSP law (expect 18)"; then
    skip "link encoded_value_law_test"; skip "encoded_value AOSP law (expect 18)"
else
g++ -std=c++17 -w -g -O1 -Isrc -o build/encoded_value_law_test \
    tests/encoded_value_law_test.cpp > /tmp/battery_ev.log 2>&1
gate "link encoded_value_law_test" $?
./build/encoded_value_law_test > /tmp/battery_ev.out 2>&1
gate "encoded_value AOSP law (expect 18)" $?
tail -1 /tmp/battery_ev.out
fi

# goldens
if cached "helloworld_golden (§28)"; then skip "helloworld_golden (§28)"; else
bash tests/fixtures/helloworld_golden/validate_helloworld_golden.sh build/miniandroid \
    > /tmp/battery_hw.out 2>&1
gate "helloworld_golden (§28)" $?
grep -h "ALL PASS" /tmp/battery_hw.out | head -1
fi

if cached "tictactoe_golden (§29 interaction + determinism)"; then
    skip "tictactoe_golden (§29 interaction + determinism)"
else
bash tests/fixtures/tictactoe_golden/validate_tictactoe_golden.sh build/miniandroid \
    > /tmp/battery_ttt.out 2>&1
gate "tictactoe_golden (§29 interaction + determinism)" $?
grep -h "ALL PASS" /tmp/battery_ttt.out | head -1
fi

# G48: EXT-01 external APK typography golden (9 static checks, Rule 10)
EXT01_APK=/home/z/corpus/external_hello/HelloWorldSelfAware-1.1.0-android.apk
EXT01_REF=/home/z/corpus/external_hello/helloworldselfaware-android-phone-screenshot.png
EXT01_OUT=/tmp/battery_ext01
rm -rf "$EXT01_OUT"; mkdir -p "$EXT01_OUT"
if cached "EXT-01 typography golden (9 static checks)"; then
    skip "EXT-01 run (external APK)"; skip "EXT-01 typography golden (9 static checks)"
elif [ -f "$EXT01_APK" ] && [ -f "$EXT01_REF" ]; then
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

if cached "EXT-02 interaction golden (12 static checks)"; then
    skip "EXT-02 long-press run (external APK interaction)"; skip "EXT-02 interaction golden (12 static checks)"
elif [ -f "$EXT01_APK" ]; then
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

# G04 §4: density-matrix differential oracle (aapt2-built fixture;
# selection law + density scaling + DENSITY_NONE + alias chain + FIT_CENTER)
if cached "density-matrix oracle (G04 §4)"; then skip "density-matrix oracle (G04 §4)"; else
bash "$REPO/scripts/validate_density_matrix.sh" /tmp/battery_density \
    > /tmp/battery_density.log 2>&1
gate "density-matrix oracle (G04 §4)" $?
grep -h "DENSITY MATRIX" /tmp/battery_density.log | head -1
fi

# G06 §6: interaction golden — real-toolchain fixture (aapt2+ECJ+D8), real
# DEX listeners. Tap law (pressed visible + queued PerformClick + counter
# mutation) + disabled law (consumes, zero visual response) + 3-run SHA.
G06_FIX_SRC="$MA/tests/fixtures/g06_interaction"
rm -rf /tmp/battery_g06; mkdir -p /tmp/battery_g06
if cached "G06 tap 3-run determinism (frame SHAs identical)"; then
    skip "G06 fixture build (aapt2+ECJ+D8)"; skip "G06 interaction golden (21 law checks)"
    skip "G06 tap 3-run determinism (frame SHAs identical)"
elif [ -d "$G06_FIX_SRC" ]; then
    bash "$REPO/MiniAndroid-Compatibility-Runtime/scripts/build_fixture_apk.sh" \
        "$G06_FIX_SRC" /tmp/battery_g06/g06_interaction.apk \
        > /tmp/battery_g06/build.log 2>&1
    gate "G06 fixture build (aapt2+ECJ+D8)" $?
    for i in 1 2 3; do
        mkdir -p "/tmp/battery_g06/tap$i"
        ./build/miniandroid run /tmp/battery_g06/g06_interaction.apk \
            -o "/tmp/battery_g06/tap$i" --tap 540,178 \
            > "/tmp/battery_g06/tap$i/run.log" 2>&1
    done
    mkdir -p /tmp/battery_g06/dis
    ./build/miniandroid run /tmp/battery_g06/g06_interaction.apk \
        -o /tmp/battery_g06/dis --tap 540,430 \
        > /tmp/battery_g06/dis/run.log 2>&1
    python3 "$REPO/scripts/compare_g06_interaction.py" \
        /tmp/battery_g06/tap1 /tmp/battery_g06/dis \
        --json /tmp/battery_g06/golden.json > /tmp/battery_g06/compare.log 2>&1
    gate "G06 interaction golden (21 law checks)" $?
    S1=$(python3 -c "import json;m=json.load(open('/tmp/battery_g06/tap1/frames/manifest.json'));print(','.join(f['sha256'] for f in m['frames']))")
    S2=$(python3 -c "import json;m=json.load(open('/tmp/battery_g06/tap2/frames/manifest.json'));print(','.join(f['sha256'] for f in m['frames']))")
    S3=$(python3 -c "import json;m=json.load(open('/tmp/battery_g06/tap3/frames/manifest.json'));print(','.join(f['sha256'] for f in m['frames']))")
    [ "$S1" = "$S2" ] && [ "$S2" = "$S3" ] && [ -n "$S1" ]
    gate "G06 tap 3-run determinism (frame SHAs identical)" $?
else
    gate "G06 interaction golden (21 law checks)" 1
fi

# G07 §9/§10: lifecycle golden — real-toolchain fixture, real DEX lifecycle
# callbacks, finish() cascade at the frame boundary, tick chain scheduling.
G07_FIX_SRC="$MA/tests/fixtures/g07_lifecycle"
rm -rf /tmp/battery_g07; mkdir -p /tmp/battery_g07
if cached "G07 finish-cascade 3-run determinism (frame SHAs identical)"; then
    skip "G07 fixture build (aapt2+ECJ+D8)"; skip "G07 lifecycle golden (16 machine checks)"
    skip "G07 finish-cascade 3-run determinism (frame SHAs identical)"
elif [ -d "$G07_FIX_SRC" ]; then
    bash "$REPO/MiniAndroid-Compatibility-Runtime/scripts/build_fixture_apk.sh" \
        "$G07_FIX_SRC" /tmp/battery_g07/g07_lifecycle.apk \
        > /tmp/battery_g07/build.log 2>&1
    gate "G07 fixture build (aapt2+ECJ+D8)" $?
    for i in 1 2 3; do
        mkdir -p "/tmp/battery_g07/fin$i"
        ./build/miniandroid run /tmp/battery_g07/g07_lifecycle.apk \
            -o "/tmp/battery_g07/fin$i" --tap 540,400 \
            > "/tmp/battery_g07/fin$i/run.log" 2>&1
    done
    mkdir -p /tmp/battery_g07/frames
    ./build/miniandroid run /tmp/battery_g07/g07_lifecycle.apk \
        -o /tmp/battery_g07/frames --frames 4 --frame-delay 250 \
        > /tmp/battery_g07/frames/run.log 2>&1
    python3 "$REPO/scripts/compare_g07_lifecycle.py" \
        /tmp/battery_g07/fin1 /tmp/battery_g07/frames \
        --json /tmp/battery_g07/golden.json > /tmp/battery_g07/compare.log 2>&1
    gate "G07 lifecycle golden (16 machine checks)" $?
    L1=$(python3 -c "import json;print(json.dumps([f['sha256'] for f in json.load(open('/tmp/battery_g07/fin1/frames/manifest.json'))['frames']]))")
    L2=$(python3 -c "import json;print(json.dumps([f['sha256'] for f in json.load(open('/tmp/battery_g07/fin2/frames/manifest.json'))['frames']]))")
    L3=$(python3 -c "import json;print(json.dumps([f['sha256'] for f in json.load(open('/tmp/battery_g07/fin3/frames/manifest.json'))['frames']]))")
    [ "$L1" = "$L2" ] && [ "$L2" = "$L3" ] && [ -n "$L1" ]
    gate "G07 finish-cascade 3-run determinism (frame SHAs identical)" $?
else
    gate "G07 lifecycle golden (16 machine checks)" 1
fi

# G08 §11-14: navigation golden — two real DEX activities, explicit Intent,
# extras roundtrip, for-result + back, pixel-real window switch.
G08_FIX_SRC="$MA/tests/fixtures/g08_navigation"
rm -rf /tmp/battery_g08; mkdir -p /tmp/battery_g08
if cached "G08 navigation 3-run determinism (frame SHAs identical)"; then
    skip "G08 fixture build (aapt2+ECJ+D8)"; skip "G08 navigation golden (17 law checks)"
    skip "G08 navigation 3-run determinism (frame SHAs identical)"
elif [ -d "$G08_FIX_SRC" ]; then
    bash "$REPO/MiniAndroid-Compatibility-Runtime/scripts/build_fixture_apk.sh" \
        "$G08_FIX_SRC" /tmp/battery_g08/g08_navigation.apk \
        > /tmp/battery_g08/build.log 2>&1
    gate "G08 fixture build (aapt2+ECJ+D8)" $?
    for i in 1 2 3; do
        mkdir -p "/tmp/battery_g08/nav$i"
        ./build/miniandroid run /tmp/battery_g08/g08_navigation.apk \
            -o "/tmp/battery_g08/nav$i" --tap 540,378 --tap 540,356 \
            > "/tmp/battery_g08/nav$i/run.log" 2>&1
    done
    mkdir -p /tmp/battery_g08/extras
    ./build/miniandroid run /tmp/battery_g08/g08_navigation.apk \
        -o /tmp/battery_g08/extras --tap 540,178 \
        > /tmp/battery_g08/extras/run.log 2>&1
    python3 "$REPO/scripts/compare_g08_navigation.py" \
        /tmp/battery_g08/nav1 /tmp/battery_g08/extras \
        --json /tmp/battery_g08/golden.json > /tmp/battery_g08/compare.log 2>&1
    gate "G08 navigation golden (17 law checks)" $?
    N1=$(python3 -c "import json;print(json.dumps([f['sha256'] for f in json.load(open('/tmp/battery_g08/nav1/frames/manifest.json'))['frames']]))")
    N2=$(python3 -c "import json;print(json.dumps([f['sha256'] for f in json.load(open('/tmp/battery_g08/nav2/frames/manifest.json'))['frames']]))")
    N3=$(python3 -c "import json;print(json.dumps([f['sha256'] for f in json.load(open('/tmp/battery_g08/nav3/frames/manifest.json'))['frames']]))")
    [ "$N1" = "$N2" ] && [ "$N2" = "$N3" ] && [ -n "$N1" ]
    gate "G08 navigation 3-run determinism (frame SHAs identical)" $?
else
    gate "G08 navigation golden (17 law checks)" 1
fi

# corpus regression: real external APKs must still boot and render
if cached "corpus run dubrowgn.microtimer_8"; then
    skip "corpus fetch (hash-verified)"
    skip "corpus run omegacentauri.mobi.simplestopwatch_26"
    skip "corpus run de.duenndns.gmdice_8"
    skip "corpus run dubrowgn.microtimer_8"
else
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
fi

echo "──────────────────────────────────────────────"
for r in "${RESULTS[@]}"; do printf '%s\n' "$r"; done
if [ $FAIL -eq 0 ]; then
    echo "BATTERY GATE: ALL PASS ($STAGE stages)"
    exit 0
else
    echo "BATTERY GATE: FAILURES PRESENT ($STAGE stages)"
    exit 1
fi
