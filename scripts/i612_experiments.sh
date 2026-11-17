#!/usr/bin/env bash
# ISSUE-612 WAVE-2 — Phase 9 experiments A–F + Phase 8 acceptance measurements.
# Timing via python (bc absent on this host). All steps DEV=1 (-O0 -g0): the
# host-reliable profile (the production -O2 -g profile OOM-killed
# build/resources/real_layout.o during this experiment pass — recorded as
# finding, follows the CONT-37/39 precedent family).
cd /home/z/my-project/miniandroid
R=evidence/issue612_audit/experiments.tsv
echo -e "experiment\tstep\tseconds\trc" > $R
step() { # step <label> <cmd...>
  local label=$1; shift
  python3 - "$label" "$R" "$@" <<'PYEOF'
import subprocess, sys, time
label, out = sys.argv[1], sys.argv[2]
cmd = sys.argv[3:]
t0 = time.monotonic()
r = subprocess.run(cmd, capture_output=True, text=True)
dt = time.monotonic() - t0
with open(out, "a") as f:
    f.write(f"{label}\t{label}\t{dt:.2f}\t{r.returncode}\n")
print(f"[{label}] {dt:.2f}s rc={r.returncode}")
if r.returncode != 0:
    print("\n".join((r.stderr or "").splitlines()[-5:]))
PYEOF
}

echo "== F: no-change rebuild (3 runs, DEV=1)"
for i in 1 2 3; do step "F$i no-change" make --no-print-directory DEV=1 module MODULE=resources; done

echo "== A: arithmetic-opcode law change (dalvik TU, DEV=1)"
printf '\n// I612-EXPERIMENT-A: opcode-law touch (reverted)\n' >> src/dex/dalvik_engine.cpp
step "A dalvik-TU -O0" make --no-print-directory DEV=1 build/dex/dalvik_engine.o
step "A link-full" make --no-print-directory DEV=1 build/miniandroid

echo "== B/C: register + reflection laws live in the SAME TU (dalvik_engine.cpp) — same measured cost as A until the Wave-3 split lands"

echo "== D: framework component change (DEV=1)"
printf '\n// I612-EXPERIMENT-D: shadow-law touch (reverted)\n' >> src/framework/android_shadows.cpp
step "D shadows-TU -O0" make --no-print-directory DEV=1 build/framework/android_shadows.o
step "D link-full" make --no-print-directory DEV=1 build/miniandroid

echo "== E: shared header change (android_shadows.h → 18-TU fan-out, DEV=1, -j1 isolated)"
printf '\n// I612-EXPERIMENT-E: header touch (reverted)\n' >> src/framework/android_shadows.h
step "E affected-TUs -O0" make --no-print-directory DEV=1 build/miniandroid
step "E relink-only" make --no-print-directory DEV=1 build/miniandroid

echo "== L0 loop: component change → minimal-closure test (target < 5s)"
printf '\n// I612-EXPERIMENT: component touch (reverted)\n' >> src/dex/mutf8.cpp
step "L0 mutf8-loop" python3 -I dev.py test component mutf8

echo "== revert all experiment touches"
git checkout -- src/dex/dalvik_engine.cpp src/framework/android_shadows.cpp src/framework/android_shadows.h src/dex/mutf8.cpp
echo "revert verified: $(git status --porcelain src/dex/dalvik_engine.cpp src/framework/android_shadows.cpp src/framework/android_shadows.h src/dex/mutf8.cpp | wc -l) dirty"
