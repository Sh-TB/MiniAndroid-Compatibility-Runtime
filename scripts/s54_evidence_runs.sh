#!/usr/bin/env bash
# S54 fresh evidence runs at HEAD 8c575f71 — §5 HelloWorld, §6 game gate, §20 re-verifications.
# Every run: fresh -o dir, click-test where interaction is expected, gate audit after.
set -uo pipefail
REPO=/home/z/my-project
BIN=$REPO/miniandroid/build/miniandroid
CACHE=$REPO/apk_cache
OUT=$REPO/local/s54/runs
EXT=/home/z/corpus/external_hello
mkdir -p "$OUT"

run_app() {  # run_app <name> <apk> [extra args...]
    local name=$1 apk=$2; shift 2
    local dir="$OUT/$name"
    rm -rf "$dir"; mkdir -p "$dir"
    echo "=== $name ==="
    ( cd "$REPO/miniandroid" && timeout 300 "$BIN" run "$apk" -o "$dir" "$@" > "$dir/run.log" 2>&1 )
    echo "rc=$?"
    tail -2 "$dir/run.log" | head -2
}

# §5 HelloWorld — canonical external HelloWorld APK (SHA-verified 009b4671…)
run_app helloworld_ext01 "$EXT/HelloWorldSelfAware-1.1.0-android.apk"
# §5 HelloWorld interaction — EXT-02 long-press (runtime dispatch into app DEX)
run_app helloworld_ext02 "$EXT/HelloWorldSelfAware-1.1.0-android.apk" --long-press 540,960

# §6 game gate — GM Dice (real F-Droid game APK 1621eda1…)
run_app gmdice "$CACHE/de.duenndns.gmdice_8.apk" --click-test

# §20 re-verifications
run_app microtimer "$CACHE/dubrowgn.microtimer_8.apk" --click-test
run_app simplestopwatch "$CACHE/omegacentauri.mobi.simplestopwatch_26.apk" --click-test
run_app headingcalculator "$CACHE/org.debian.eugen.headingcalculator_1.apk" --click-test
run_app unote "$CACHE/app.varlorg.unote_30.apk" --click-test

# §15/§16 root-cause subjects — confirm blank-class at this HEAD
run_app chessclock "$CACHE/com.chessclock.android_29.apk" --click-test
run_app notes "$CACHE/org.billthefarmer.notes_139.apk" --click-test

echo "ALL RUNS DONE"
