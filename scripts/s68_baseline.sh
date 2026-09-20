#!/usr/bin/env bash
# s68_baseline.sh — FINAL BASE CLOSURE: canonical APK BEFORE-state capture.
# Per-app canonical recipes (S65/S66/S67 validated). Records rc + frame SHAs.
# Output: run/s68_baseline/<app>/ + baseline.jsonl
set -uo pipefail
ROOT=/home/z/my-project
ENG=$ROOT/miniandroid/build/miniandroid
APKS=$ROOT/upload/canonical_apks
OUT=$ROOT/run/s68_baseline
mkdir -p "$OUT"
: > "$OUT/baseline.jsonl"

sha_all() { # dir → json array of frame shas (sorted)
  local d="$1"
  python3 - "$d" <<'EOF'
import sys, os, json, hashlib
d = sys.argv[1]
shas = []
for root, _, files in os.walk(d):
    for f in sorted(files):
        if f.endswith(".png"):
            p = os.path.join(root, f)
            shas.append((os.path.relpath(p, d), hashlib.sha256(open(p,'rb').read()).hexdigest()[:16]))
print(json.dumps(sorted(shas)))
EOF
}

run_app() {
  local name="$1"; shift
  local apk="$1"; shift
  local run="$OUT/$name"
  rm -rf "$run"; mkdir -p "$run"
  echo "=== $name ==="
  ( cd "$run" && timeout 500 "$ENG" run "$@" -o "$run" "$apk" > "$run/engine.log" 2>&1 )
  local rc=$?
  echo "{\"name\":\"$name\",\"rc\":$rc,\"frames\":$(sha_all "$run")}" >> "$OUT/baseline.jsonl"
  echo "$name rc=$rc frames=$(ls "$run"/frames/ 2>/dev/null | wc -l) shot=$(ls "$run"/*.png 2>/dev/null | wc -l)"
}

run_app fishrings "$APKS/fishrings_v1.23_vc6.apk" --execution-mode real-dalvik --frames 9 --frame-delay 1500 \
  --tap 5,5 --tap 5,5 --tap 5,5 --tap 5,5 --tap 540,960 --tap 270,960 --tap 810,960
run_app tripeaks  "$APKS/tripeaks_v1.2.1_vc4.apk"  --execution-mode real-dalvik --frames 5 --frame-delay 1500 --tap 5,5
run_app opmt      "$APKS/opmt_v0.1.2_vc1.apk"      --execution-mode real-dalvik --frames 6 --frame-delay 1500 --tap 277,1379
run_app tictactoe "$APKS/com.emmanuelmess.tictactoe_3.apk" --execution-mode real-dalvik --frames 3 --frame-delay 1500
run_app gmdice    "$APKS/de.duenndns.gmdice_8.apk" --execution-mode real-dalvik --frames 3 --frame-delay 1500
run_app stopwatch "$APKS/com.github.muellerma.stopwatch_6.apk" --execution-mode real-dalvik --frames 3 --frame-delay 1500
run_app microtimer "$APKS/dubrowgn.microtimer_8.apk" --execution-mode real-dalvik --frames 3 --frame-delay 1500
run_app unote     "$APKS/app.varlorg.unote_30.apk" --execution-mode real-dalvik --frames 3 --frame-delay 1500
run_app bouncy    "$APKS/bouncy.apk"               --execution-mode real-dalvik --frames 3 --frame-delay 1500
run_app dooz23    "$APKS/io.github.yamin8000.dooz_23.apk" --execution-mode real-dalvik --frames 3 --frame-delay 1500
echo "BASELINE DONE"
