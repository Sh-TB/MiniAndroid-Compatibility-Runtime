## WAVE 3 CHECKPOINT 1 — Baseline established (start of wave)

**Commit:** `5e7090e3` (Wave-2 commit, verified — rebased sha of the reported `4c7b0dc0`, same tree/message)
**Branch:** `main` · **Working tree:** clean (0 dirty files)
**Safety reference:** tag `safety/pre-dalvik-wave3-5e7090e3` created (never force-updated)
**Toolchain:** g++ (Debian 14.2.0-19) 14.2.0, 2 vCPU / 4 GB host

**Wave-2 changes inspected:** DEV=1 profile (`-O0 -g0`) into separate `build_dev/` tree; manifest-filtered `make module`; L0 mutf8 component test (24 checks); `dev.py` driver. Production profile byte-untouched by that wave.

**Baseline tests (this checkpoint, commands + exit codes captured in `evidence/issue612_audit/wave3_baseline_tests.txt`):**
- `make test` → 5/5 PASS (TextView/Activity/Trace/Paint/View-hierarchy operations), rc=0
- `make test-core` → simple_test + s130_laws_test + gp582_engine_probe_test PASS, rc=0
- `make test-law` → 37 PASS lines, no FAIL observed

**Production build command:** `make -j1 all` → rc=0, 245.8 s wall (this run repaired a mixed-profile `build/` tree: Wave-2 experiment steps ran BEFORE the `build_dev/` separation landed and left some -O0 objects; the recompile set was therefore partially stale. This is recorded as a Wave-2 lesson — the separation now prevents recurrence).
**DEV build command:** `make DEV=1 -j1 all` → writes to `build_dev/` only.

**Known failures:** `resources/real_layout.cpp` (broken dormant TU, not in manifest, not linked — Wave-2 finding); cmake binary not installed on this host (apt blocked) — CMake parity will be reported accordingly.

**APK selection (P0) — not arbitrary:** continuing the already-considered candidate with the strongest existing evidence: **#614 Guess (`ru.zxalexis.ugaday_15.apk`)**, SHA-256 `000ae2e5751f9a85c331d6205881d3db5dc81a00d10522485d9026b0494f8c3d`, prebuilt original artifact from the prior verified batch (`upload/handoff_apks/`, prior run log + view tree exist in `download/batch614_624_evidence/`). Prior batch status: SUCCESS render — this wave must add: provenance URL, full-chain trace, interaction via the runtime's canonical `--tap` pipeline, and 3 repeat runs.

**Next checkpoints:** benchmarks with compiler-phase breakdown → APK execution evidence → Dalvik pilot extraction (or documented blocker) → equivalence proof → final report.
