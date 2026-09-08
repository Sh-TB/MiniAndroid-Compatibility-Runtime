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
# Resolves BOTH layouts: the in-repo copy (scripts/ inside
# MiniAndroid-Compatibility-Runtime) and the legacy sandbox copy
# (/home/z/my-project/scripts/ next to the repo directory).
if [ -d "$REPO/miniandroid" ]; then
    MA="$REPO/miniandroid"
    IN_REPO=1
else
    MA="$REPO/MiniAndroid-Compatibility-Runtime/miniandroid"
    IN_REPO=0
fi
# SHARED (comparators, fixture builders, corpus fetch) always live in the
# OUTER scripts/ directory — the sandbox tools location that predates the
# in-repo harness copy. TOOLREPO = repo root when run from the sandbox
# layout, or the parent when run from the in-repo layout.
if [ "$IN_REPO" -eq 1 ]; then TOOLREPO="$REPO/.."; else TOOLREPO="$REPO"; fi
TOOLS="$TOOLREPO/scripts"
# Fixture builders + fetch_corpus live in the REPO's scripts/ in both layouts.
REPOSCRIPTS="$REPO/scripts"
if [ "$IN_REPO" -eq 0 ]; then REPOSCRIPTS="$REPO/MiniAndroid-Compatibility-Runtime/scripts"; fi
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
        if [ "$RESUME" -eq 1 ]; then echo "$1" > "$STATE/$(printf '%02d' $STAGE).pass"; fi
    else
        FAIL=1
        RESULTS+=("FAIL  $1 (rc=$2)")
        printf '  [%d] FAIL  %s (rc=%s)\n' "$STAGE" "$1" "$2"
    fi
    # TOOL-FINDING FIX (MASTER-3 session 11, §24 class): gate() is invoked
    # as a plain command while stages toggle `set -e`. With RESUME=0 the
    # old tail `[ "$RESUME" -eq 1 ] && echo ...` evaluated FALSE and became
    # the function's return value — so the FIRST gate() under an active
    # `set -e` (stage 63, F-016 default) aborted the ENTIRE battery before
    # stage 64 (F-016 strict-mode). Every fresh run silently executed only
    # 63 of 64 stages. gate() must NEVER propagate a nonzero status.
    return 0
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
if cached "semantic pass3 bridge (expect 66)"; then
    skip "link semantic_long_cmp_conv_test"; skip "semantic long/cmp/conv (expect 14)"
    skip "link semantic_switch_parse_neg_test"; skip "semantic switch parse-neg (expect 25)"
    skip "link semantic_pass3_bridge_test"; skip "semantic pass3 bridge (expect 66)"
else
for t in semantic_long_cmp_conv_test semantic_switch_parse_neg_test semantic_pass3_bridge_test; do
    g++ -std=c++17 -w -g -O2 -Isrc -Ithird_party/nlohmann_json/include -o "build/$t" \
        "tests/$t.cpp" build/apk/*.o build/dex/*.o build/runtime/*.o \
        build/diagnostics/*.o build/resources/*.o build/renderer/*.o \
        build/fonts/*.o build/framework/*.o build/api/*.o build/storage/*.o \
        -lz -ljpeg -lwebp -lwebpdemux -lfreetype -lharfbuzz -lfribidi -lpng -lpthread -lsqlite3 \
        > "/tmp/battery_$t.log" 2>&1
    gate "link $t" $?
done

./build/semantic_long_cmp_conv_test > /tmp/battery_lcc.out 2>&1
gate "semantic long/cmp/conv (expect 14)" $?
./build/semantic_switch_parse_neg_test > /tmp/battery_swpn.out 2>&1
gate "semantic switch parse-neg (expect 25)" $?
./build/semantic_pass3_bridge_test > /tmp/battery_p3b.out 2>&1
gate "semantic pass3 bridge (expect 66)" $?
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
    -lz -ljpeg -lwebp -lwebpdemux -lfreetype -lharfbuzz -lfribidi -lpng -lpthread -lsqlite3 \
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
    -lz -ljpeg -lwebp -lwebpdemux -lfreetype -lharfbuzz -lfribidi -lpng -lpthread -lsqlite3 \
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
    -lz -ljpeg -lwebp -lwebpdemux -lfreetype -lharfbuzz -lfribidi -lpng -lpthread -lsqlite3 \
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
    -lz -ljpeg -lwebp -lwebpdemux -lfreetype -lharfbuzz -lfribidi -lpng -lpthread -lsqlite3 \
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
    -lz -ljpeg -lwebp -lwebpdemux -lfreetype -lharfbuzz -lfribidi -lpng -lpthread -lsqlite3 \
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
    -lz -ljpeg -lwebp -lwebpdemux -lfreetype -lharfbuzz -lfribidi -lpng -lpthread -lsqlite3 \
    > /tmp/battery_g10law.log 2>&1
gate "link g10_layout_law_test" $?
./build/g10_layout_law_test > /tmp/battery_g10law.out 2>&1
gate "G10 measurement/layout law (expect 23)" $?
tail -1 /tmp/battery_g10law.out
fi

# G11: real-DEX constructor + custom-hierarchy law battery (descriptor gate,
# LayoutInflater Factory law, from/inflate hostile dispatch, addView
# single-mount + cycle hostile laws)
if cached "link g11_ctor_law_test"; then
    skip "link g11_ctor_law_test"; skip "G11 ctor/Factory/addView law (expect 37)"
else
g++ -std=c++17 -w -g -O1 -Isrc -o build/g11_ctor_law_test \
    tests/g11_ctor_law_test.cpp build/apk/*.o build/dex/*.o build/runtime/*.o \
    build/diagnostics/*.o build/resources/*.o build/renderer/*.o \
    build/fonts/*.o build/framework/*.o build/api/*.o build/storage/*.o \
    -lz -ljpeg -lwebp -lwebpdemux -lfreetype -lharfbuzz -lfribidi -lpng -lpthread -lsqlite3 \
    > /tmp/battery_g11law.log 2>&1
gate "link g11_ctor_law_test" $?
./build/g11_ctor_law_test > /tmp/battery_g11law.out 2>&1
gate "G11 ctor/Factory/addView law (expect 37)" $?
tail -1 /tmp/battery_g11law.out
fi

# G04/G05 §16: hostile drawable/image/layout safety battery
if cached "G04 hostile safety (expect 24)"; then
    skip "link g04_hostile_test"; skip "G04 hostile safety (expect 24)"
else
g++ -std=c++17 -w -g -O1 -Isrc -Itests -o build/g04_hostile_test \
    tests/g04_hostile_test.cpp build/apk/*.o build/dex/*.o build/runtime/*.o \
    build/diagnostics/*.o build/resources/*.o build/renderer/*.o \
    build/fonts/*.o build/framework/*.o build/api/*.o build/storage/*.o \
    -lz -ljpeg -lwebp -lwebpdemux -lfreetype -lharfbuzz -lfribidi -lpng -lpthread -lsqlite3 \
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
    -lz -ljpeg -lwebp -lwebpdemux -lfreetype -lharfbuzz -lfribidi -lpng -lpthread -lsqlite3 \
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
    -lz -ljpeg -lwebp -lwebpdemux -lfreetype -lharfbuzz -lfribidi -lpng -lpthread -lsqlite3 \
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
    -lz -ljpeg -lwebp -lwebpdemux -lfreetype -lharfbuzz -lfribidi -lpng -lpthread -lsqlite3 \
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

# MASTER-2 §6: shadow registry architectural invariant (one canonical
# ownership model — a second/reduced registry must be detectable, never
# silently accepted).
if cached "link shadow_registry_invariant_test"; then
    skip "link shadow_registry_invariant_test"
    skip "§6 shadow registry invariant (expect 24)"
else
g++ -std=c++17 -w -g -O1 -Isrc -o build/shadow_registry_invariant_test \
    tests/shadow_registry_invariant_test.cpp build/apk/*.o build/dex/*.o \
    build/runtime/*.o build/diagnostics/*.o build/resources/*.o \
    build/renderer/*.o build/fonts/*.o build/framework/*.o build/api/*.o \
    build/storage/*.o -lz -ljpeg -lwebp -lwebpdemux -lfreetype -lharfbuzz \
    -lfribidi -lpng -lpthread -lsqlite3 > /tmp/battery_sri.log 2>&1
gate "link shadow_registry_invariant_test" $?
./build/shadow_registry_invariant_test > /tmp/battery_sri.out 2>&1
gate "§6 shadow registry invariant (expect 24)" $?
tail -1 /tmp/battery_sri.out
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
    python3 "$TOOLS/compare_ext01_typography.py" "$EXT01_REF" \
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
    python3 "$TOOLS/compare_ext01_interaction.py" \
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
bash "$TOOLS/validate_density_matrix.sh" /tmp/battery_density \
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
    bash "$REPOSCRIPTS/build_fixture_apk.sh" \
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
    python3 "$TOOLS/compare_g06_interaction.py" \
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
    bash "$REPOSCRIPTS/build_fixture_apk.sh" \
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
    python3 "$TOOLS/compare_g07_lifecycle.py" \
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
    bash "$REPOSCRIPTS/build_fixture_apk.sh" \
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
    python3 "$TOOLS/compare_g08_navigation.py" \
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

# M3 §6/§13: style-bag layout law — aapt2-built fixture whose buttons take
# geometry ONLY from the style= bag + parent chain (the headingcalculator
# keypad shape). Guards: (a) ARSC ResTable_map 12-byte stride + bag_parent
# chain (unit test on the real fixture ARSC); (b) inflate-layer compiled-
# reference style resolution; (c) AOSP precedence (direct layout_weight
# beats the style bag); (d) FIX-M3-004 match-parent remeasure (row = full
# remaining height after the header).
M3_FIX_SRC="$MA/tests/fixtures/m3_style_weight"
rm -rf /tmp/battery_m3sw; mkdir -p /tmp/battery_m3sw
if cached "M3 style geometry golden (6 law checks)"; then
    skip "M3 fixture build (aapt2+ECJ+D8)"
    skip "M3 ARSC style law (17 checks)"
    skip "M3 style geometry golden (6 law checks)"
elif [ -d "$M3_FIX_SRC" ]; then
    bash "$REPOSCRIPTS/build_fixture_apk.sh" \
        "$M3_FIX_SRC" /tmp/battery_m3sw/m3_style_weight.apk \
        > /tmp/battery_m3sw/build.log 2>&1
    gate "M3 fixture build (aapt2+ECJ+D8)" $?
    (cd "$MA" && unzip -o -q /tmp/battery_m3sw/m3_style_weight.apk \
        resources.arsc -d /tmp/battery_m3sw) \
        && g++ -std=c++17 -w -g -O1 -Isrc -Ithird_party/nlohmann_json/include \
            -o build/m3_arsc_style_law_test tests/m3_arsc_style_law_test.cpp \
            build/apk/*.o build/dex/*.o build/runtime/*.o build/diagnostics/*.o \
            build/resources/*.o build/renderer/*.o build/fonts/*.o \
            build/framework/*.o build/api/*.o build/storage/*.o \
            -lz -ljpeg -lwebp -lwebpdemux -lfreetype -lharfbuzz -lfribidi -lsqlite3 \
            -lpng -lpthread > /tmp/battery_m3sw/link.log 2>&1
    gate "link m3_arsc_style_law_test" $?
    ./build/m3_arsc_style_law_test /tmp/battery_m3sw/resources.arsc \
        > /tmp/battery_m3sw/law.log 2>&1
    gate "M3 ARSC style law (17 checks)" $?
    U007_LAYOUT_DEBUG=2 ./build/miniandroid run /tmp/battery_m3sw/m3_style_weight.apk \
        -o /tmp/battery_m3sw/run > /tmp/battery_m3sw/run.log 2>&1
    gate "M3 fixture run" $?
    python3 "$REPOSCRIPTS/m3_style_geometry_check.py" \
        /tmp/battery_m3sw/run.log > /tmp/battery_m3sw/geometry.log 2>&1
    gate "M3 style geometry golden (6 law checks)" $?
else
    gate "M3 style geometry golden (6 law checks)" 1
fi

# corpus regression: real external APKs must still boot and render
if cached "corpus run dubrowgn.microtimer_8"; then
    skip "corpus fetch (hash-verified)"
    skip "corpus run omegacentauri.mobi.simplestopwatch_26"
    skip "corpus run de.duenndns.gmdice_8"
    skip "corpus run dubrowgn.microtimer_8"
else
CORPUS_DIR="$MA/download"
python3 "$REPOSCRIPTS/fetch_corpus.py" \
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
        # M3 FINDING-012: hermetic per-run app-data root — a corpus run
        # must never read/write a previous run's Room/SQLite state.
        ./build/miniandroid run "$CORPUS_DIR/$rel" -o "$out" \
            --data-root "$out/data_root" \
            > "$out/run.log" 2>&1
        rc=$?
        grep -q "Status: SUCCESS" "$out/run.log" && [ -f "$out/screenshot.png" ] && rc=0 || rc=1
        gate "corpus run $name" $rc
    else
        gate "corpus run $name" 1
    fi
done
fi

# M3 FINDING-012: app-data-root law golden — persistence replay + fresh-state
# determinism on a REAL APK (microtimer, Room/SQLite-backed).
#   Pair 1: run A (fresh root) → exactly 1 alarm row
#           run B (SAME root)   → exactly 2 rows; frame_000 visually gains
#                                 the persisted timer row (expired render)
#   Pair 2: runs C,D repeat the protocol on an independent fresh root
# LAW 1 (durable persistence): B's first frame renders A's committed state
#          (Android /data/data law — install state survives process death).
# LAW 2 (byte determinism): frames(A)≡frames(C) AND frames(B)≡frames(D)
#          byte-for-byte — identical initial state ⇒ identical execution.
F012_APK="$MA/download/exp076_corpus/dubrowgn.microtimer_8.apk"
[ -f "$F012_APK" ] || F012_APK=/tmp/my-project/apk_cache/microtimer.apk
f012_rows() {
    python3 - "$1" <<'PYEOF'
import sqlite3, sys
try:
    c = sqlite3.connect(sys.argv[1] + "/dubrowgn.microtimer/databases/app-data")
    print(c.execute("SELECT COUNT(*) FROM alarm").fetchone()[0])
except Exception:
    print("0")
PYEOF
}
if [ ! -f "$F012_APK" ]; then
    gate "M3 F-012 persistence+fresh-state determinism golden" 1
else
    PAIR1=/tmp/battery_f012_p1; PAIR2=/tmp/battery_f012_p2
    rm -rf "$PAIR1" "$PAIR2"; mkdir -p "$PAIR1" "$PAIR2"
    TAPS=(--tap 540,1605 --tap 540,1185 --tap 900,1815)
    rc=0   # shell rc convention: 0 = pass (gate law)
    ./build/miniandroid run "$F012_APK" -o "$PAIR1/A" --data-root "$PAIR1/root" \
        "${TAPS[@]}" > "$PAIR1/A.log" 2>&1 || rc=1
    [ "$(f012_rows "$PAIR1/root")" = "1" ] || rc=1
    ./build/miniandroid run "$F012_APK" -o "$PAIR1/B" --data-root "$PAIR1/root" \
        "${TAPS[@]}" > "$PAIR1/B.log" 2>&1 || rc=1
    [ "$(f012_rows "$PAIR1/root")" = "2" ] || rc=1
    ./build/miniandroid run "$F012_APK" -o "$PAIR2/C" --data-root "$PAIR2/root" \
        "${TAPS[@]}" > "$PAIR2/C.log" 2>&1 || rc=1
    [ "$(f012_rows "$PAIR2/root")" = "1" ] || rc=1
    ./build/miniandroid run "$F012_APK" -o "$PAIR2/D" --data-root "$PAIR2/root" \
        "${TAPS[@]}" > "$PAIR2/D.log" 2>&1 || rc=1
    [ "$(f012_rows "$PAIR2/root")" = "2" ] || rc=1
    # LAW 1: stateful frame_000 must differ from fresh frame_000 (persisted
    # row visibly present) — in BOTH independent pairs.
    cmp -s "$PAIR1/A/frames/frame_000.png" "$PAIR1/B/frames/frame_000.png" && rc=1
    cmp -s "$PAIR2/C/frames/frame_000.png" "$PAIR2/D/frames/frame_000.png" && rc=1
    # LAW 2: byte determinism frame-for-frame across the independent pairs.
    for f in $(ls "$PAIR1/A/frames" | grep '\.png$'); do
        cmp -s "$PAIR1/A/frames/$f" "$PAIR2/C/frames/$f" || rc=1
        cmp -s "$PAIR1/B/frames/$f" "$PAIR2/D/frames/$f" || rc=1
    done
    nA=$(ls "$PAIR1/A/frames" | grep -c '\.png$'); nC=$(ls "$PAIR2/C/frames" | grep -c '\.png$')
    { [ "$nA" = "$nC" ] && [ "$nA" -ge 90 ]; } || rc=1
    gate "M3 F-012 persistence+fresh-state determinism golden" $rc
fi

# GATE H (M3 FINDING-016): real-APK image pipeline visual golden.
# Subject: omegacentauri simplestopwatch — its action bar renders TWO real
# PNG resources (settings.png gear, menu.png list icon) through the full
# runtime pipeline: ARSC density selection → PNG decode → BitmapFactory
# inDensity→inTargetDensity scale → tint → ImageButton draw.
# LAW 1 (decode+tint): each ImageButton crop must contain the blue button
#          background AND a white glyph (>= 1000 white px, > 8 distinct
#          colors — a flat fill or a failed decode has neither).
# LAW 2 (structural fidelity): the rendered glyph mask must agree with the
#          SOURCE PNG's alpha mask (bbox-aligned IoU >= 0.85; measured
#          0.959 settings / 0.997 menu at freeze).
# LAW 3 (determinism): 3 independent runs produce byte-identical frames.
GATEH_APK="$MA/download/exp073_real_apps/omegacentauri.mobi.simplestopwatch_26.apk"
if [ ! -f "$GATEH_APK" ]; then
    gate "GATE H real-APK image pipeline golden" 1
else
    GH=/tmp/battery_gateh; rm -rf "$GH"; mkdir -p "$GH/ext"
    unzip -o -q "$GATEH_APK" "res/drawable-xhdpi-v4/settings.png" \
        "res/drawable-xhdpi-v4/menu.png" -d "$GH/ext" 2>/dev/null
    rc=0
    for i in 1 2 3; do
        ./build/miniandroid run "$GATEH_APK" -o "$GH/run$i" \
            --data-root "$GH/data$i" > "$GH/run$i.log" 2>&1 || rc=1
    done
    cmp -s "$GH/run1/screenshot.png" "$GH/run2/screenshot.png" || rc=1
    cmp -s "$GH/run1/screenshot.png" "$GH/run3/screenshot.png" || rc=1
    python3 - "$GH" <<'PYEOF2' || rc=1
import sys
from PIL import Image
import numpy as np
gh = sys.argv[1]
im = Image.open(gh + "/run1/screenshot.png").convert("RGB")
assert im.size == (1080, 1920)
CROPS = {"settings": (854, 1815, 959, 1920), "menu": (975, 1815, 1080, 1920)}
def bbox(m):
    ys, xs = np.where(m)
    if len(xs) == 0: return None
    return xs.min(), ys.min(), xs.max(), ys.max()
def glyph_white(crop):
    a = np.array(crop)
    return (a[:,:,0]>200)&(a[:,:,1]>200)&(a[:,:,2]>200)
def glyph_alpha(src):
    return np.array(Image.open(src).convert("RGBA"))[:,:,3] > 128
for name, (x0,y0,x1,y1) in CROPS.items():
    crop = im.crop((x0,y0,x1,y1))
    a = np.array(crop)
    ncol = len(set(map(tuple, a.reshape(-1,3))))
    white = int(glyph_white(crop).sum())
    blue = int(((a[:,:,0]==111)&(a[:,:,1]==168)&(a[:,:,2]==220)).sum())
    assert white >= 1000, f"{name}: white={white}"
    assert ncol > 8, f"{name}: colors={ncol}"
    assert blue > 3000, f"{name}: blue={blue}"
    src = f"{gh}/ext/res/drawable-xhdpi-v4/{name}.png"
    sm, rm = glyph_alpha(src), glyph_white(crop)
    sb, rb = bbox(sm), bbox(rm)
    assert sb and rb, f"{name}: empty mask"
    sc = sm[sb[1]:sb[3]+1, sb[0]:sb[2]+1]
    rc_ = rm[rb[1]:rb[3]+1, rb[0]:rb[2]+1]
    G = 48
    si = np.array(Image.fromarray((sc*255).astype(np.uint8)).resize((G,G), Image.NEAREST))>127
    ri = np.array(Image.fromarray((rc_*255).astype(np.uint8)).resize((G,G), Image.NEAREST))>127
    iou = (si&ri).sum()/(si|ri).sum()
    print(f"[GATE-H] {name}: white={white} colors={ncol} IoU={iou:.3f}")
    assert iou >= 0.85, f"{name}: IoU={iou:.3f} < 0.85"
PYEOF2
    gate "GATE H real-APK image pipeline golden" $rc
fi

# M3 FINDING-016: exception-honesty law battery (ROADMAP family G).
# Subject: f016_exception_honesty — REAL DEX bytecode throws an uncaught
# IllegalStateException through a three-deep call chain
# (onCreate → chainA → chainB → chainC(throws)); no app frame catches.
# LAW 1 (Dalvik unwind): every handler-less frame unwinds — mid-stack
#          [EXC-UNWIND] records for chainA AND chainB must exist and the
#          throw must be the app's own bytecode (message F016-UNCAUGHT).
# LAW 2 (honesty, default mode): the run must NOT report plain SUCCESS —
#          status downgrades to PARTIAL with the in-flight count in the
#          status message, crash.log carries an [EXC-UNCAUGHT-TOP]
#          APP-BOUNDARY entry, and the CLI exit code is nonzero.
# LAW 3 (ART process death, MINIANDROID_EXC_STRICT=1): status CRASH,
#          "ART process-death law" in the message, and the strict CRASH
#          latch REFUSES further DEX dispatch (onStart/onResume refused).
# LAW 4 (pre-throw state): "F016 armed" text is set BEFORE the throw —
#          the rendered frame must show it (state-before-death visible).
F016_FIXTURE="$MA/tests/fixtures/f016_exception_honesty"
F016_APK="$F016_FIXTURE/f016_exception_honesty.apk"
if cached "F-016 fixture APK build (aapt2+ECJ+D8)"; then
    skip "F-016 fixture APK build (aapt2+ECJ+D8)"
else
    if bash "$REPOSCRIPTS/build_fixture_apk.sh" "$F016_FIXTURE" "$F016_APK" \
        > /tmp/battery_f016_build.log 2>&1; then
        gate "F-016 fixture APK build (aapt2+ECJ+D8)" 0
    else
        gate "F-016 fixture APK build (aapt2+ECJ+D8)" 1
    fi
fi
if [ -f "$F016_APK" ]; then
    # Stage: default-mode honesty (LAWS 1+2+4).
    if cached "F-016 default-mode honesty (unwind+PARTIAL+crash.log)"; then
        skip "F-016 default-mode honesty (unwind+PARTIAL+crash.log)"
    else
        F016_OUT=/tmp/battery_f016_default; rm -rf "$F016_OUT"; mkdir -p "$F016_OUT"
        rc=0
        set +e
        ./build/miniandroid run "$F016_APK" -o "$F016_OUT" \
            > "$F016_OUT/run.log" 2>&1
        run_rc=$?
        set -e
        # LAW 2a: nonzero CLI rc (honest failure)…
        [ "$run_rc" -ne 0 ] || rc=1
        # LAW 2b: …with PARTIAL (not SUCCESS, not CRASH) status + count text.
        grep -q "Status: PARTIAL SUCCESS" "$F016_OUT/run.log" || rc=1
        grep -q "F-016 exception-honesty: 1 uncaught in-flight exception" \
            "$F016_OUT/run.log" || rc=1
        # LAW 1: real app bytecode (throw message in DEX traces) + mid-stack
        # unwind records in crash.log.
        CRASHLOG="$F016_OUT/crash.log"
        [ -f "$CRASHLOG" ] || CRASHLOG="$MA/run/crash.log"
        grep -rq "F016-UNCAUGHT" "$F016_OUT" || rc=1
        grep -q "unwound .*MainActivity;.chainB" "$CRASHLOG" || rc=1
        grep -q "unwound .*MainActivity;.chainA" "$CRASHLOG" || rc=1
        grep -q "\[EXC-UNCAUGHT-TOP\].*APP-BOUNDARY" "$CRASHLOG" || rc=1
        # LAW 4: pre-throw visual state observable (the rendered screenshot
        # carries the "F016 armed" state — state-before-death visible).
        [ -f "$F016_OUT/screenshot.png" ] || rc=1
        gate "F-016 default-mode honesty (unwind+PARTIAL+crash.log)" $rc
    fi
    # Stage: strict-mode ART process-death law (LAW 3).
    if cached "F-016 strict-mode process death (CRASH + dispatch refused)"; then
        skip "F-016 strict-mode process death (CRASH + dispatch refused)"
    else
        F016_OUTS=/tmp/battery_f016_strict; rm -rf "$F016_OUTS"; mkdir -p "$F016_OUTS"
        rc=0
        set +e
        MINIANDROID_EXC_STRICT=1 ./build/miniandroid run "$F016_APK" -o "$F016_OUTS" \
            > "$F016_OUTS/run.log" 2>&1
        run_rc=$?
        set -e
        [ "$run_rc" -ne 0 ] || rc=1
        grep -q "Status: CRASH" "$F016_OUTS/run.log" || rc=1
        grep -q "ART process-death law" "$F016_OUTS/run.log" || rc=1
        grep -q "APP BOUNDARY + strict: CRASH" "$F016_OUTS/run.log" || rc=1
        # The CRASH latch must refuse subsequent lifecycle DEX dispatch.
        grep -q "strict CRASH latch active — DEX dispatch .*onStart refused" \
            "$F016_OUTS/run.log" || rc=1
        grep -q "strict CRASH latch active — DEX dispatch .*onResume refused" \
            "$F016_OUTS/run.log" || rc=1
        gate "F-016 strict-mode process death (CRASH + dispatch refused)" $rc
    fi
else
    gate "F-016 default-mode honesty (unwind+PARTIAL+crash.log)" 1
    gate "F-016 strict-mode process death (CRASH + dispatch refused)" 1
fi

# ── M3 F-020: Compose snapshot-family primitive laws (micro reproducer) ──
# The fixture exercises the four runtime laws the dooz Compose chain
# demanded (AtomicReference ctor-value identity = the global-snapshot law,
# AtomicInteger arithmetic = write counters, Enum.compareTo ordinal sign =
# the isAtLeast shape, CAS value law) plus the F-021 getLayoutInflater
# window-singleton law, and renders the verdicts as five pixel bands
# (green=pass/red=fail) — §10: visual proof, not just rc.
F020_FIX_SRC="$MA/tests/fixtures/f020_snapshot"
rm -rf /tmp/battery_f020; mkdir -p /tmp/battery_f020
if cached "F-020 snapshot-law fixture build (ECJ+D8)"; then
    skip "F-020 snapshot-law fixture build (ECJ+D8)"
    skip "F-020 snapshot-law pixel golden (5 bands)"
elif [ -d "$F020_FIX_SRC" ]; then
    bash "$REPOSCRIPTS/build_fixture_apk.sh" \
        "$F020_FIX_SRC" /tmp/battery_f020/f020_snapshot.apk \
        > /tmp/battery_f020/build.log 2>&1
    gate "F-020 snapshot-law fixture build (ECJ+D8)" $?
    (cd "$MA" && timeout 120 ./build/miniandroid run /tmp/battery_f020/f020_snapshot.apk \
        -o /tmp/battery_f020/out > /tmp/battery_f020/run.log 2>&1)
    gate "F-020 snapshot-law fixture run (rc=0 SUCCESS)" $?
    rc=0
    grep -q "Status: SUCCESS" /tmp/battery_f020/run.log || rc=1
    python3 "$REPOSCRIPTS/f020_pixel_golden.py" /tmp/battery_f020/out/screenshot.ppm \
        > /tmp/battery_f020/pixel.log 2>&1 || rc=1
    gate "F-020 snapshot-law pixel golden (5 bands)" $rc
    tail -1 /tmp/battery_f020/pixel.log
else
    gate "F-020 snapshot-law fixture build (ECJ+D8)" 1
    gate "F-020 snapshot-law pixel golden (5 bands)" 1
fi

# ── M3 F-024: InputStream EOF law family (micro reproducer) ──
# The §3A closure law: read() returns 0..255, -1 at EOF (sticky), bulk
# read returns the count filled; 0xFF is DATA (255) — proven against four
# deterministic assets (empty/one-byte/0xFF/11-byte) with a 7-band visual
# verdict. Guards the historical defect class: fail-soft read()==0 spin
# and signed-byte EOF confusion.
F024_FIX_SRC="$MA/tests/fixtures/f024_eof_law"
rm -rf /tmp/battery_f024; mkdir -p /tmp/battery_f024
if cached "F-024 EOF-law fixture build (ECJ+D8)"; then
    skip "F-024 EOF-law fixture build (ECJ+D8)"
    skip "F-024 EOF-law pixel golden (7 bands)"
elif [ -d "$F024_FIX_SRC" ]; then
    bash "$REPOSCRIPTS/build_fixture_apk.sh" \
        "$F024_FIX_SRC" /tmp/battery_f024/f024_eof_law.apk \
        > /tmp/battery_f024/build.log 2>&1
    gate "F-024 EOF-law fixture build (ECJ+D8)" $?
    (cd "$MA" && timeout 120 ./build/miniandroid run /tmp/battery_f024/f024_eof_law.apk \
        -o /tmp/battery_f024/out > /tmp/battery_f024/run.log 2>&1)
    gate "F-024 EOF-law fixture run (rc=0 SUCCESS)" $?
    rc=0
    grep -q "Status: SUCCESS" /tmp/battery_f024/run.log || rc=1
    python3 "$REPOSCRIPTS/f024_pixel_golden.py" /tmp/battery_f024/out/screenshot.ppm \
        > /tmp/battery_f024/pixel.log 2>&1 || rc=1
    gate "F-024 EOF-law pixel golden (7 bands)" $rc
    tail -1 /tmp/battery_f024/pixel.log
else
    gate "F-024 EOF-law fixture build (ECJ+D8)" 1
    gate "F-024 EOF-law pixel golden (7 bands)" 1
fi

# ── M3 §4 F-025: Executor/Executors closure (micro reproducer) ──
# The queue law: Executors.newFixedThreadPool → execute(Runnable)×3 →
# FIFO drain at the settle point (count==3, sum==7, ran-after-onCreate).
# Guards the double-run defect class (F-025: static-local guard froze
# false → every task ran twice, executedCount=9) and the enqueue-vs-inline
# ownership law (ExecutorShadow owns executor-family execute()).
F026_FIX_SRC="$MA/tests/fixtures/f020_executor"
rm -rf /tmp/battery_f026; mkdir -p /tmp/battery_f026
if cached "F-025 executor fixture build (ECJ+D8)"; then
    skip "F-025 executor fixture build (ECJ+D8)"
    skip "F-025 executor pixel golden (4 bands)"
elif [ -d "$F026_FIX_SRC" ]; then
    bash "$REPOSCRIPTS/build_fixture_apk.sh" \
        "$F026_FIX_SRC" /tmp/battery_f026/f020_executor.apk \
        > /tmp/battery_f026/build.log 2>&1
    gate "F-025 executor fixture build (ECJ+D8)" $?
    (cd "$MA" && timeout 120 ./build/miniandroid run /tmp/battery_f026/f020_executor.apk \
        -o /tmp/battery_f026/out > /tmp/battery_f026/run.log 2>&1)
    gate "F-025 executor fixture run (rc=0 SUCCESS)" $?
    rc=0
    grep -q "Status: SUCCESS" /tmp/battery_f026/run.log || rc=1
    # ownership law: ZERO inline executions for executor-family receivers
    grep -q "REAL DEX run() executed inline" /tmp/battery_f026/run.log && rc=1
    python3 "$REPOSCRIPTS/f020_executor_pixel_golden.py" /tmp/battery_f026/out/screenshot.ppm \
        > /tmp/battery_f026/pixel.log 2>&1 || rc=1
    gate "F-025 executor pixel golden (4 bands)" $rc
    tail -1 /tmp/battery_f026/pixel.log
else
    gate "F-025 executor fixture build (ECJ+D8)" 1
    gate "F-025 executor pixel golden (4 bands)" 1
fi

# ── M3 §5 F-026+F-027: Room/SQLite persistence law family (micro reproducer) ──
# INSERT-order/UPDATE/DELETE/txn-commit/txn-rollback/cursor-typed+isNull/
# reopen — 7 bands. Guards two defect classes: F-026 (bare rawQuery had NO
# handler → fail-soft null cursor on every scalar read) and F-027
# (String.contentEquals answered the api_dispatcher always-false stub —
# §8 fail-wrong-law class).
F026_FIX_SRC="$MA/tests/fixtures/f026_room_sql_law"
rm -rf /tmp/battery_f026sql; mkdir -p /tmp/battery_f026sql
if cached "F-026+F-027 Room/SQLite law fixture build (ECJ+D8)"; then
    skip "F-026+F-027 Room/SQLite law fixture build (ECJ+D8)"
    skip "F-026+F-027 Room/SQLite pixel golden (7 bands)"
elif [ -d "$F026_FIX_SRC" ]; then
    bash "$REPOSCRIPTS/build_fixture_apk.sh" \
        "$F026_FIX_SRC" /tmp/battery_f026sql/f026_room_sql_law.apk \
        > /tmp/battery_f026sql/build.log 2>&1
    gate "F-026+F-027 Room/SQLite law fixture build (ECJ+D8)" $?
    (cd "$MA" && timeout 120 ./build/miniandroid run /tmp/battery_f026sql/f026_room_sql_law.apk \
        -o /tmp/battery_f026sql/out --data-root /tmp/battery_f026sql/data \
        > /tmp/battery_f026sql/run.log 2>&1)
    gate "F-026+F-027 Room/SQLite law fixture run (rc=0 SUCCESS)" $?
    rc=0
    grep -q "Status: SUCCESS" /tmp/battery_f026sql/run.log || rc=1
    grep -q "SQLITE-SHADOW. rawQuery rows=" /tmp/battery_f026sql/run.log || rc=1
    python3 "$REPOSCRIPTS/f026_pixel_golden.py" /tmp/battery_f026sql/out/screenshot.ppm \
        > /tmp/battery_f026sql/pixel.log 2>&1 || rc=1
    gate "F-026+F-027 Room/SQLite pixel golden (7 bands)" $rc
    tail -1 /tmp/battery_f026sql/pixel.log
else
    gate "F-026+F-027 Room/SQLite law fixture build (ECJ+D8)" 1
    gate "F-026+F-027 Room/SQLite pixel golden (7 bands)" 1
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
