#!/usr/bin/env bash
# validate_demo_proof.sh — reproducible validation fixture for the
# real-APK execution proof (demo/miniandroid-demo.apk).
#
# Verifies, from runtime-produced artifacts only:
#   1. run exits 0
#   2. frames/manifest.json exists with N clicks dispatched
#   3. every frame hash is distinct (state actually changed)
#   4. the app's own visible state advances exactly as the DEX logic dictates
#      (count increments, position cycles, color cycles)
#   5. deterministic replay: a second clean run produces the identical
#      SHA256 frame sequence
#
# Usage: bash demo/validate_demo_proof.sh <path-to-miniandroid-binary>
set -uo pipefail

BIN="${1:-build/miniandroid}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
APK="$REPO/demo/build/miniandroid-demo.apk"
WORK="$(mktemp -d)"
FAIL=0

say()  { printf '%s\n' "$*"; }
fail() { printf 'FAIL: %s\n' "$*"; FAIL=1; }

[ -x "$BIN" ] || { fail "binary not found: $BIN"; exit 1; }
[ -f "$APK" ]  || { fail "APK not built: $APK (run bash demo/build_demo_apk.sh)"; exit 1; }

run_once() {
    local dir="$1"
    mkdir -p "$dir"
    "$BIN" run "$APK" -o "$dir" --click-count 8 > "$dir/run.log" 2>&1
    echo $?
}

check_run() {
    local dir="$1" tag="$2"
    local manifest="$dir/frames/manifest.json"
    [ -f "$manifest" ] || { fail "$tag: manifest missing"; return 1; }
    python3 - "$manifest" "$tag" <<'PY'
import json, sys
manifest, tag = sys.argv[1], sys.argv[2]
m = json.load(open(manifest))
frames = m["frames"]
ok = True
def check(cond, msg):
    global ok
    if not cond:
        print(f"FAIL: {tag}: {msg}"); ok = False

check(m["clicks_dispatched"] == m["click_count_requested"] == 8,
      f"clicks dispatched {m.get('clicks_dispatched')}/8")
hashes = [f["sha256"] for f in frames]
check(len(set(hashes)) == len(hashes) == 9, "frame hashes must be 9 distinct values")
# The app's own state: count increments, positions/colors cycle per DEX logic
EXP_POS = [(220,370),(400,660),(580,950),(760,80),(40,370),(220,660),(400,950),(580,80),(760,370)]
EXP_COLOR = ["GREEN","BLUE","YELLOW","RED","GREEN","BLUE","YELLOW","RED","GREEN"]
for i, f in enumerate(frames):
    st = next((t["text"] for t in f["visible_texts"] if t["text"].startswith("count=")), None)
    check(st is not None, f"frame {i}: status text missing")
    if st is None: continue
    want = f"count={i+1} pos=({EXP_POS[i][0]},{EXP_POS[i][1]}) color={EXP_COLOR[i]}"
    check(st == want, f"frame {i}: state '{st}' != expected '{want}'")
    check(f.get("changed_pixels_vs_previous", 0) > 0 or i == 0,
          f"frame {i}: no pixel change vs previous frame")
sys.exit(0 if ok else 1)
PY
}

say "== run 1 =="
c1=$(run_once "$WORK/run1")
[ "$c1" = "0" ] || fail "run1 exit code $c1"
check_run "$WORK/run1" "run1"

say "== run 2 (deterministic replay) =="
c2=$(run_once "$WORK/run2")
[ "$c2" = "0" ] || fail "run2 exit code $c2"
check_run "$WORK/run2" "run2"

if python3 -c "
import json, sys
a = [f['sha256'] for f in json.load(open('$WORK/run1/frames/manifest.json'))['frames']]
b = [f['sha256'] for f in json.load(open('$WORK/run2/frames/manifest.json'))['frames']]
sys.exit(0 if a == b else 1)"; then
    say "deterministic replay: identical SHA256 sequence"
else
    fail "replay frame hashes differ"
fi

if [ "$FAIL" = "0" ]; then
    say "VALIDATION_PASS (all checks passed, workdir $WORK kept for inspection)"
else
    say "VALIDATION_FAIL (workdir $WORK kept for inspection)"
fi
exit $FAIL
