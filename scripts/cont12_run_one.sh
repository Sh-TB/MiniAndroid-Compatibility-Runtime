#!/bin/bash
# cont12_run_one.sh — baseline/A-B single-title run harness
# usage: cont12_run_one.sh <apk> <pkg> <tag>
set -u
APK="$1"; PKG="$2"; TAG="$3"
ROOT=/home/z/my-project
ENG=$ROOT/miniandroid/build/miniandroid
STORE=$ROOT/run/cont12/store_$TAG
RUN=$ROOT/run/cont12/$TAG
rm -rf "$STORE" "$RUN"; mkdir -p "$STORE" "$RUN"
"$ENG" install "$APK" --data-root "$STORE" > "$RUN/install.log" 2>&1 || { echo "INSTALL FAIL"; exit 1; }
"$ENG" run --package "$PKG" --data-root "$STORE" --dump-view-tree --max-seconds 90 --frames 6 -o "$RUN" > "$RUN/run.log" 2>&1
echo "rc=$?"
