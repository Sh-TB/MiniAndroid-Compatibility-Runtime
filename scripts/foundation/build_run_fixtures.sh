#!/usr/bin/env bash
# scripts/foundation/build_run_fixtures.sh — build + run + capture every foundation fixture.
# Deterministic: single-threaded build order, fixed output dirs, evidence per fixture.
set -uo pipefail
ROOT=/home/z/my-project
FDST=$ROOT/miniandroid/tests/fixtures_foundation
OUT=$ROOT/docs/evidence/foundation/fixtures
ENG=$ROOT/miniandroid/build/miniandroid
BUILDER=$ROOT/scripts/build/build_fixture_apk.sh
mkdir -p "$OUT" "$ROOT/upload/foundation_apks"

APKS=()
for f in "$FDST"/*/; do
  name=$(basename "$f")
  apk="$ROOT/upload/foundation_apks/${name}.apk"
  echo "=== BUILD $name ==="
  if ! bash "$BUILDER" "$f" "$apk" > "$OUT/${name}.build.log" 2>&1; then
    echo "BUILD FAIL $name (see ${name}.build.log)"; tail -5 "$OUT/${name}.build.log"
    continue
  fi
  APKS+=("$apk|$name")
done

for entry in "${APKS[@]}"; do
  apk="${entry%%|*}"; name="${entry##*|}"
  run="$OUT/$name"
  mkdir -p "$run"
  extra="--dump-view-tree"
  case "$name" in
    f21_button) extra="$extra --click-test";;
    f27_nav)    extra="$extra --click-test";;
  esac
  echo "=== RUN $name ($extra) ==="
  ( cd "$run" && timeout 120 "$ENG" run $extra -o "$run" "$apk" > "$run/engine.log" 2>&1 )
  echo "rc=$? for $name"
  # normalize engine outputs into the run dir
  find "$run" -maxdepth 2 -name 'frame*.png' -o -maxdepth 2 -name 'view_tree.json' -o -maxdepth 2 -name 'api_trace.json' 2>/dev/null | head
done
echo "=== DONE ==="
ls "$OUT"
