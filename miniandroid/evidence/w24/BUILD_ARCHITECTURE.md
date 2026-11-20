# W24 Build Architecture — current state and what was measured

## Command surface (all opt-in layers preserved)
- Canonical production: `make -j1 all` (592.78 s today; 541.33 s best-day).
- Fast path: `make FASTPROFILE=1 -j2 all` (-g1; 349.35 s today).
- W24 candidate (verified): `make FASTPROFILE=1 W24TIERS=1 -j2 all`
  = 289.85 s avg (ABBA reps ±0.4 %, byte-identical binary), −17.3 % wall and
  −17.7 % CPU vs the matched-steal BASE (350.39 s), battery 49/49 PASS,
  5-APK gate 11/11 screenshot hashes identical on candidate codegen.
- Developer loops: warm no-op 1.02 s; leaf edit 2.55 s; identical-tree
  rebuild via ccache 25.40 s.

## What governs the wall time
1. Total CPU work (513.9 CPU-s FASTPROFILE): -O2 pipeline 76% of heavy TUs.
2. Effective parallel capacity 1.47 of 2 cores — hypervisor steal ~24% of
   build-window budget; make/Ninja/xargs all land within ±2% (349.35 /
   355.91 / 348.90). Scheduling and build-system choice are NOT levers here.
3. Remaining CPU-work levers, measured: per-TU -O1 on cold TUs (-37..-44%
   heavy, -18..-23% small — implemented as W24TIERS=1, now FULL A/B VERIFIED
   at −91.9 CPU-s); PCH REJECTED (third measurement: load ≈ parse cost,
   over-inclusion hurts).
4. BUG-8 (fixed): the tier lists used ':=' before BUILDDIR was defined —
   block relocated after the DEV=1 override; tier-1 domains got explicit
   PIC recipes so the dev-so gate exercises the candidate codegen.

## Parity notes
- CMake/Ninja parity requires -DCMAKE_CXX_FLAGS='-DMINIANDROID_HAVE_WEBP'
  (CMakeLists does not define it — W24 finding).
- BUG-7: two shadow_registry.h copies exist and differ; the framework one
  is authoritative (29 consumers); the dex one is a diverging duplicate.
