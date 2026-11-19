#!/usr/bin/env bash
# W20-P2 mandatory benchmark harness — 7 phases, per-phase wall + peak RSS.
# Phases: 1 clean prod build, 2 unchanged rebuild, 3 isolated domain edit,
# 4 ordinary non-domain edit, 5 shared-header touch, 6 final link,
# 7 test execution. Logs to evidence/w20/bench_*.log.
set -u
cd /home/z/my-project/miniandroid
EV=evidence/w20
WRAP="python3 scripts/p0_build_wrap.py"

phase() { echo "=== PHASE $1 @ $(date -u +%H:%M:%S) ==="; }

# ---- Phase 1: clean production build (serial) ----
phase 1; rm -rf build
$WRAP $EV/bench_p1_clean_prod.log all || echo "PHASE1 exit=$?"

# ---- Phase 2: unchanged rebuild ----
phase 2
$WRAP $EV/bench_p2_unchanged.log all || echo "PHASE2 exit=$?"

# ---- Phase 3: isolated domain modification (jdk.cpp marker) ----
phase 3
for run in 1 2; do
  printf '\n// W20 bench marker %s\n' "$run" >> src/dex/dalvik_bridge_domain_jdk.cpp
  $WRAP $EV/bench_p3_domain_r$run.log dev-so || echo "P3 r$run exit=$?"
  git checkout -q -- src/dex/dalvik_bridge_domain_jdk.cpp
  make dev-so -j1 > /dev/null 2>&1   # restore tree
done

# ---- Phase 4: ordinary non-Domain source modification ----
phase 4
printf '\n// W20 bench marker 1\n' >> src/framework/shadow_registry.cpp
$WRAP $EV/bench_p4_ordinary.log all || echo "PHASE4 exit=$?"
git checkout -q -- src/framework/shadow_registry.cpp
make all -j1 > /dev/null 2>&1

# ---- Phase 5: shared-header modification (true post-F1 cascade) ----
phase 5
for run in 1 2; do
  m=$(stat -c %y src/framework/android_shadows.h)
  touch src/framework/android_shadows.h
  $WRAP $EV/bench_p5_header_r$run.log dev-so || echo "P5 r$run exit=$?"
  touch -d "$m" src/framework/android_shadows.h
done
m=$(stat -c %y src/framework/android_shadows.h); touch src/framework/android_shadows.h
$WRAP $EV/bench_p5_header_prod.log all || echo "P5 prod exit=$?"
touch -d "$m" src/framework/android_shadows.h
make all -j1 > /dev/null 2>&1   # bring prod tree back in sync

# ---- Phase 6: final link (touch nothing, force relink of prod binary) ----
phase 6
rm -f build/miniandroid
$WRAP $EV/bench_p6_link.log build/miniandroid || echo "PHASE6 exit=$?"

# ---- Phase 7: test execution ----
phase 7
$WRAP $EV/bench_p7_testall.log test-all || echo "PHASE7 exit=$?"

echo "=== HARNESS DONE @ $(date -u +%H:%M:%S) ==="
grep -h "\[WRAPPER\]" $EV/bench_p*.log
