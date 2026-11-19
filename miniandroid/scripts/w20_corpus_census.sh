#!/usr/bin/env bash
# W20-P3: full local-corpus census with the current PRODUCTION binary.
# Per APK: launch 100s, 30 frames, screenshot sha, exit code, RUN_END state,
# uncaught exceptions count. Output: evidence/w20/corpus_census.md
set -u
cd /home/z/my-project/miniandroid
BIN=./build/miniandroid
OUT=evidence/w20/corpus
mkdir -p "$OUT"
SUM=evidence/w20/corpus_census.md
: > "$SUM"
echo "| APK | exit | RUN_END | uncaught | screenshot sha16 |" >> "$SUM"
echo "|---|---|---|---|---|" >> "$SUM"
for APK in /home/z/my-project/upload/handoff_apks/*.apk; do
  name=$(basename "$APK" .apk)
  d="$OUT/$name"
  mkdir -p "$d"
  timeout 140 "$BIN" run --max-seconds 100 --frames 30 --trace \
      -o "$d" --execution-mode real-dalvik "$APK" \
      > "$d/run.log" 2>&1
  rc=$?
  re=$(grep -ac "RUN_END" "$d/run.log")
  un=$(grep -ac "uncaught in-flight" "$d/run.log")
  sha=$(sha256sum "$d/screenshot.png" 2>/dev/null | cut -c1-16)
  sz=$(stat -c %s "$d/screenshot.png" 2>/dev/null || echo 0)
  echo "| $name | $rc | $re | $un | ${sha:-none} (${sz}B) |" >> "$SUM"
  echo "$name rc=$rc run_end=$re uncaught=$un sha=$sha"
done
echo CENSUS_DONE
