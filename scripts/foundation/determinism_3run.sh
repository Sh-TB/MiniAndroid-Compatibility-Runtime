#!/usr/bin/env bash
# scripts/foundation/determinism_3run.sh — user §13: run × 3, compare SHAs.
# deterministic != correct (correctness is the verifier's job); this proves
# the pipeline is deterministic on top of the verifier's semantic PASS.
set -euo pipefail
ROOT=/home/z/my-project
ENG=$ROOT/miniandroid/build/miniandroid
APKS=$ROOT/upload/foundation_apks
OUT=$ROOT/docs/evidence/foundation/determinism
mkdir -p "$OUT"

FIXES="f01_color f04_text f14_relative f21_button f27_nav f05_persian"
for name in $FIXES; do
  for run in 1 2 3; do
    d="$OUT/${name}_run${run}"
    rm -rf "$d"; mkdir -p "$d"
    extra="--dump-view-tree"
    case "$name" in
      f21_button|f27_nav) extra="$extra --click-test";;
    esac
    (cd "$d" && timeout 120 "$ENG" run $extra -o "$d" "$APKS/${name}.apk" > engine.log 2>&1)
  done
done

python3 - <<'PYEOF'
import hashlib, json, os
OUT = "/home/z/my-project/docs/evidence/foundation/determinism"
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()
results = {}
for name in "f01_color f04_text f14_relative f21_button f27_nav f05_persian".split():
    shas = []
    for run in (1, 2, 3):
        d = f"{OUT}/{name}_run{run}"
        s = sha(os.path.join(d, "screenshot.png"))
        vt = sha(os.path.join(d, "view_tree.json")) if os.path.exists(os.path.join(d, "view_tree.json")) else "MISSING"
        shas.append({"frame": s[:16], "view_tree": vt[:16]})
    det = len({x["frame"] for x in shas}) == 1 and len({x["view_tree"] for x in shas}) == 1
    results[name] = {"runs": shas, "deterministic": det}
    print(f"[{'DET×3' if det else 'NONDET'}] {name}: " + " | ".join(x["frame"] for x in shas))
with open(f"{OUT}/DETERMINISM.json", "w") as f:
    json.dump(results, f, indent=1)
n = sum(1 for v in results.values() if v["deterministic"])
print(f"SUMMARY: {n}/{len(results)} deterministic")
PYEOF
