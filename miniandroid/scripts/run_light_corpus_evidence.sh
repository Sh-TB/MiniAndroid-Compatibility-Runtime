#!/usr/bin/env bash
# run_light_corpus_evidence.sh — real-APK interaction + determinism evidence
# for the light open-source corpus (owner task: prove the apps actually run).
#
# For each app:
#   run A  : launch frame + 6 dispatched clicks (real DEX listeners)
#   run B  : identical second run for byte-level determinism comparison
#
# All frames come from the MiniAndroid framebuffer — nothing is composited,
# retouched, or externally re-rendered. The analyzer records non-white and
# color statistics per frame.
set -u
cd "$(dirname "$0")/.."

CACHE="${MINIANDROID_APK_CACHE:-/home/z/my-project/apk_cache}"
OUT=run/light_corpus/evidence
BIN=build/miniandroid
mkdir -p "$OUT"

APPS="simplestopwatch gmdice unote chessclock bgclockhansdezwart headingcalculator tinymusicplayer microtimer"

for app in $APPS; do
    apk="$CACHE/corpus/$app.apk"
    [ -f "$apk" ] || { echo "SKIP $app (no apk)"; continue; }
    for run in A B; do
        dir="$OUT/$app/run$run"
        rm -rf "$dir"; mkdir -p "$dir"
        timeout 180 "$BIN" run "$apk" -o "$dir" --click-count 6 > "$dir/run.log" 2>&1
        echo "$app run$run exit=$?"
    done
done
echo "evidence runs complete: $OUT"
