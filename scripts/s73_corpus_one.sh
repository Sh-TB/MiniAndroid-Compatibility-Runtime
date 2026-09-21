#!/usr/bin/env bash
# s73_corpus_one.sh <apk-name> — single canonical-corpus run (S73 PART B)
set -uo pipefail
ROOT=/home/z/my-project
ENG=$ROOT/miniandroid/build/miniandroid
CORPUS=$ROOT/upload/canonical_apks
OUT=$ROOT/run/s73_corpus
apk="$1"; name="${apk%.apk}"
d="$OUT/$name"; rm -rf "$d"; mkdir -p "$d"
(cd "$d" && timeout 150 "$ENG" run --execution-mode real-dalvik \
   --frames 9 --frame-delay 1500 --dump-api-trace --dump-view-tree \
   -o . "$CORPUS/$apk" > engine.log 2>&1)
echo "$name rc=$? frames=$(ls $d/frames 2>/dev/null | wc -l)"
