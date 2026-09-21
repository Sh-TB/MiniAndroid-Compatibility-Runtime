#!/usr/bin/env bash
# s77_baseline_battery.sh — S77 §1 baseline re-establishment.
# 26 pinned foundation APKs on the current binary (S72-W4b recipe).
# Output: run/s77_baseline/battery.jsonl
set -uo pipefail
ROOT=/home/z/my-project
ENG=$ROOT/miniandroid/build/miniandroid
SRC=$ROOT/upload/foundation_apks
OUT=$ROOT/run/s77_baseline
mkdir -p "$OUT"
: > "$OUT/battery.jsonl"

pass=0; fail=0
for apk in "$SRC"/*.apk; do
  name="$(basename "$apk" .apk)"
  run="$OUT/$name"
  rm -rf "$run"; mkdir -p "$run"
  (cd "$run" && timeout 120 "$ENG" run -o "$run" "$apk" > engine.log 2>&1)
  rc=$?
  px=$(python3 "$ROOT/scripts/w4_px.py" "$run" 2>/dev/null || echo 0)
  if [ "$rc" = "0" ]; then pass=$((pass+1)); else fail=$((fail+1)); fi
  echo "{\"name\":\"$name\",\"rc\":$rc,\"frame_px\":$px}" >> "$OUT/battery.jsonl"
  echo "$name rc=$rc frame_px=$px"
done
echo "BATTERY RESULT: $pass/26 rc=0, $fail failed"
