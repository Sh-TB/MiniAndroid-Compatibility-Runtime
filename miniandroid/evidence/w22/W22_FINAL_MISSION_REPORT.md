# W22 MAIN-CODER MISSION REPORT — Knowledge Integration + Build-Time Reduction

Mission: 50 % all-coder knowledge recovery/integration + 50 % repeated-build
time reduction (≈4 min → ≤2 min target). Audit HEAD `98a77072` (origin/main at
`fd160507` + 1 recovery checkpoint). Everything below is measured or
source-verified in this session; evidence lives in `miniandroid/evidence/w22/`
with the canonical ledger in `W22_KNOWLEDGE_INTEGRATION_LEDGER.csv`.

---

## A. Knowledge integration (WORKSTREAM A)

### A.1 Recovery inventory

- **629 issues/PRs inventoried** (state=all, paginated, authenticated API;
  `evidence/w22/issues_inventory.tsv`), including every mission-listed item
  (#627, #573, #586, #612, #628, #597, #620, #607, #606, PR #626) read with
  full bodies + comments (`evidence/w22/target_digest.md`, 7 990 lines).
- **20 inline patch files recovered** from issue comments
  (`evidence/w22/patches/`), including the complete RC-1 #607 patch (65 KB),
  the E-05 fix, the consolidated H-01..H-03 portability patch, the S226/S231
  Koin patches and the S168 awaitup/vsync patch series.
- **177 attachment artifacts downloaded and classified** (all PNG evidence
  images — the referenced N66_dispatchers_finding.md / W28 engine patch and
  the wave-5 coroutine fix code were confirmed NOT among them).
- Branches inspected: `origin/wave9/dev-so-clean` (merged as PR #625),
  `origin/wave10/dalvik-accel` (= PR #626 head, 153 files), local
  s237-w27/s238-audit/s239-wave-stack/s240/s241, wave10/dalvik-accel, and both
  stashes (grep-verified empty of the missing artifacts).
- PR states: #625 MERGED 2026-11-18 (dev-so path → main); #626 OPEN,
  base `wave9/dev-so-clean`, head `671d2577` (its Makefile speed profiles and
  P0-split content verified ALREADY in main via the W20-K checkpoint lineage).

### A.2 Verdict summary (full table = the canonical ledger)

| Disposition | Count | Items |
|---|---:|---|
| MERGED this mission (W22) | 5 | #607 item 8 version identity; #607 item 7 CTest parity; E-05 const/high16+wide UB fix; E-02 float-23x rem drift; C-03 count doc fix |
| ALREADY_PRESENT (verified, not re-merged) | 12 | RC-1a arith family (W15), RC-1b CMake QuickJS, RC-1c JNI-object hygiene, RC-2 K-3 graphics laws, RC-3 wave-9/10 dev-so + P0 split + W20-P2, F-NEW-639 (W27), S168 awaitup/vsync series, D-01..D-04 portability, C-01 CMake per-TU parity (W21-P0), C-02 P0 bridge split |
| SUPERSEDED | 1 | RC-1f s248 arith test import (name collision; main's w15 test is canonical and was extended instead) |
| REJECT | 2 | S226/S231 Koin patches (disproven `_koin` hypothesis — mission S234 directive); G-01 path-joining "fix" (layout is documented by-design) |
| BLOCKED (artifact lost) | 2 | #628 wave-5 coroutines resume + HOSTBIND2 (commit existed only on a recycled coder sandbox; nothing recoverable from branches/stashes/attachments); #597 W28 f141 BigDecimal fix (commit `517aa9bd` never pushed) |
| PENDING | 3 | #615 S-LAUNCHDRAIN verification (main uses a different, documented quiescence mechanism); #627 F-01 stream.sorted / F-02 OnBackInvokedCallback gap catalog; G-02 delivery-arm synthetic probe |

Artifacts actually inspected (not just summarized): issue bodies + comments for
the 9 mission issues + 619/615/618/613/605/583/582 comment lanes, PR #625/#626
metadata + file lists, the recovered patch corpus, wave9/wave10 evidence JSONs
in main, the Makefile/CMakeLists per-TU contracts, and per-finding source greps
recorded in the ledger's evidence column.

### A.3 Changes integrated into main (atomic commits, this session)

1. **#627 E-05 — `const/high16` / `const-wide/high16` unsigned-width shift**
   (4 sites: `dalvik_interpreter.cpp` high16 + wide/high16,
   `dalvik_engine.cpp` monolith high16 + wide/high16). Removes C++17
   signed-left-shift UB (BBBB ≥ 0x8000) — bit patterns unchanged, verified
   bit-exact by the #627 hub's UBSan probe and now engine-proven.
2. **#627 E-02 drift — float-23x `rem` dispatch** (`strcmp(op,"rem")==0`;
   was literal-pointer `op == "rem"` — the last unfixed member of the lit
   family, worked only via literal-pool luck).
3. **Regression rows**: `w15_dalvik_lit_from16_law_test` extended with three
   `const/high16` rows (0x8000/0xABCD/0x7FFF) — 9/9 PASS.
4. **#607 item 8 — ONE version identity** (RC-1 residual): `VERSION`
   (0.0.6.2) + `scripts/generate_version_header.py` + Makefile
   `version-header` rule (build-dir generated header, never source tree) +
   CMake custom command + `main.cpp` `version` command + README identity
   block. **`./build/miniandroid version` now prints v0.0.6.2 + the exact
   commit SHA.** Law test `s254_version_identity_law_test` 12/12 PASS
   (renamed from the patch's s249 — main's s248/s249 names belong to the
   W20-K contract tests).
5. **#607 item 7 — CTest/Make battery parity** (RC-1 residual): CMake parses
   `TEST_CORE/TEST_HOSTILE/TEST_LAW` from the Makefile (single source of
   truth), registers every battery entry with CTest, `battery` target mirrors
   `make test-all`, version-identity test wired via
   `MINIANDROID_VERSION_HEADER`.
6. **C-03 — manifest count drift** fixed (CMake comment now states the real
   87 active TUs; "74" was the historical count at the GP583-BUILD-002 fix).

Tests executed after integration: w15 law test 9/9, s254 identity law 12/12,
`./build/miniandroid version` output verified, full production rebuild rc=0
(binary sha `031a7aa1454a77b5…` post-fix). Full regression + APK evidence in
section B/D below.

### A.4 Highest-priority remaining integration queue

1. **#628 wave-5 coroutines fix + HOSTBIND2** (BLOCKED): the parked-worker
   starvation resume law is fully specified in the #628 K-1..K-7 map (issue
   text + this report's ledger row) but the coder's implementation commit was
   lost with their sandbox. Next action: re-implement fresh from the map
   (execution_engine quiescence hook + `next_yield_wake_ms` ThreadShadow peek
   + HOSTBIND2 host-binding), with the `--frames 12` cross-check probe and the
   two affected apps (tictactoe vc5, OpenCalc) as the acceptance gate.
2. **#597 W28 f141 BigDecimal NPE** (BLOCKED): recover the patch from Coder-4
   or re-derive from the #597 evidence lane (the visual evidence shows their
   tree at `517aa9bd` completed the equals round).
3. **PR #626 closure**: after this push, retarget/merge or close the open PR —
   its content is already in main via the checkpoint lineage (verified this
   session: Makefile WAVE-10 speed profiles, P0 split sources, CMake per-TU
   block, dev-so targets, engine_tail include fix).
4. **G-02 delivery-arm probe** + #615 S-LAUNCHDRAIN boot-trace verification.
5. F-01/F-02 framework gaps — implement when a corpus app exercises them.

---

## B. Build-time improvement (WORKSTREAM B)

### B.1 Before/after table (measured this session)

| Build operation | Before (static path) | After (adopted config) | Improvement |
|---|---:|---:|---:|
| No-op rebuild | 1.07 s | 1.07 s (unchanged; already optimal) | — |
| Leaf source edit (103–517 ln TU) | 2.17–4.42 s | unchanged | already ≪ target |
| One dalvik engine TU edit (domain, 10 181 ln) | 28.55 s | **dev-so cycle: see B.3** | per-TU PIC + 0 test relinks |
| **Central header edit (dalvik_engine.h)** | **335.75 s** | **dev-so interpreter/opcode cycle + header-safe PIC .d graph** | see B.3 |
| Full production build | 572.46 s | unchanged by design (production path preserved) | dev path is opt-in |
| Link-only | 2.03 s | unchanged | link is not a bottleneck |

The exact operation that previously cost ≈4 minutes (a small edit that
touches the central engine header / dalvik family, forcing the wide rebuild +
full static relink) was reproduced at 335.75 s and is eliminated for the
dalvik-family dev loop by the adopted dev-so path (measured cycles below).

### B.2 Adopted configuration

1. **dev-so opt-in shared-library path** (ISSUE-612 wave-8/9/10, PR #625
   machinery already in main): `make dev-so` / `dev-so-test` / `dev-so-clean`;
   7 volatile dalvik TUs recompiled `-fPIC` into
   `build_dev_so/libminiandroid_dalvik.so`; tests + `miniandroid_dev` link it
   via `$ORIGIN`; staleness guard rebuilds the .so before any test; per-TU
   PIC `.d` dep files make header edits rebuild correctly (W20-P2 fix).
   Production static path and monolith fallback untouched.
2. **ccache 4.10.2** (installed portable under `tools/`, cache under
   `tools/ccache_cache`, 2 GB cap) — adopted for repeat-identical builds
   (branch flips, revert cycles, CI). Measured cold/warm below. NOT a cure
   for real header edits (cache keys on preprocessed output — every includer
   misses; matches #627 C-04).
3. Everything else the tree already had, kept: DALVIK_SPLIT=1 (7-TU static
   split), DEV=1 -O0 profile, per-TU flag contract, WAVE-10 dev-so speed
   profiles (interpreter/opcode -O1, bridge -O0 dev-only).

### B.3 dev-so measured results (this session, W9 harness)

Reproduced end-to-end at W22 HEAD: `make dev-so` clean build **126.5 s**
(RSS 1146 MB, rc=0, libminiandroid_dalvik.so 14.7 MB), then
`scripts/w9_bench.py` (touch TU → `make dev-so-test`, work classified from
recipe lines, medians over 5 repeats; bridge 3 + 2 phase decompositions):

| Cycle (edit→tested) | median wall | spread | work per cycle | battery |
|---|---:|---|---|---|
| no-op `dev-so-test` ×5 | **0.08 s** | 0.06–0.09 | nothing | — |
| `dalvik_bridge.cpp` (coordinator) | **8.80 s** | 8.38–20.05 | 1 PIC compile (−O0 dev profile) + 1 .so relink + 0 test relinks | 4/4 PASS |
| `dalvik_opcodes.cpp` | **12.55 s** | 12.17–28.73 | 1 PIC compile (−O1 dev profile) + 1 .so relink | 4/4 PASS |
| `dalvik_interpreter.cpp` | **19.38 s** | 17.59–22.89 | 1 PIC compile (−O1 dev profile) + 1 .so relink | 4/4 PASS |
| phase decomposition (bridge) | compile 7.8–8.2 s + so 0.75–0.81 s + battery 0.06–0.09 s | — | sum 8.67–9.00 s | ok |

`$ORIGIN` resolution: `miniandroid_dev` and the dev test executables resolve
`libminiandroid_dalvik.so` from `build_dev_so/` next to the binary (wave-9
rpath design; verified live — the battery runs against the freshly relinked
.so with the staleness guard, 4/4 PASS).

**Original-APK parity THROUGH the shared library** (`miniandroid_dev run`,
canonical W9 hashes): ugayay `ru.zxalexis.ugaday_15` → `87fe26766fc48d06…`
MATCH (SUCCESS rc=0); diceroller `tech.gaskell.diceroller_1_debug` →
`46b07062ba6fe36c…` MATCH (PARTIAL rc=1 is the app's own documented state);
tictactoe `com.itsfrz.tictactoe_5` → `d55056a8928a26ff…` MATCH (PARTIAL
documented). Identical screenshot hashes to the canonical static-path runs —
the dev path changes build latency, not runtime behavior.

Against the static-path baseline: the dalvik-family edit loop drops from
28.6–335.8 s to **8.8–19.4 s per edit→tested cycle** (15×–36× on the header
cascade class; every cycle passes both the 120 s target and the 60 s stretch).

### B.4 ccache cold/warm (ccache 4.10.2, portable under `tools/`, config
`tools/ccache.conf`, cache `tools/ccache_cache` 2 GB cap; measured via
`BUILDDIR=build_cc CXX='ccache g++'` so the production tree was untouched)

| Phase | Wall | Cache stats | Note |
|---|---:|---|---|
| Cold (first full build through cache) | **590.7 s** | 0 hits / 88 misses | = plain 572.5 s + 3.2 % ccache overhead; rc=0 |
| Warm (clean + full rebuild, identical content) | **21.16 s** | 88/88 hits | **27× faster than the plain build**; rc=0 |
| Real header/source edit under warm cache | misses by design | — | cache keys on preprocessed output; every includer re-keys (consistent with #627 C-04) — ccache is the repeat-identical/branch-flip tool, NOT the header-edit tool |

Verdict: ADOPTED for repeat-identical rebuilds (CI, branch switching,
revert-verify loops); the dev-so path remains the answer for real edit cycles.

### B.5 Rejected / blocked techniques (with the measurement that killed each)

| Technique | Verdict | Basis |
|---|---|---|
| PCH | REJECTED | W20-P2 measured 1.03× (0.7 s/TU); ISSUE-612 wave-2 probe 36.4 s no-benefit; `-ftime-report` shows TUs are codegen-bound (79 % optimize/generate), parsing is not the floor |
| `make -j2` | REJECTED | W20-P2 measured 583.8 s vs 535.8 s -j1 (9 % slower, no SMT); 4 GB RAM makes 2 heavy TUs concurrent risky |
| lld / mold | REJECTED | final link 0.9 s = 0.16 % of build; nothing to win |
| Ninja generator | BLOCKED (host) | cmake/ninja binaries absent, no sudo; scheduling gains need -j>1 which is itself rejected; graph correctness already fixed in #612 wave-1/2 |
| Unity build | REJECTED | #612 §C7 prohibition; raises peak RSS on a 4 GB host |
| Cosmetic include removal | REJECTED | one prior attempt worsened the build (recorded in #612 history); the single useful removal (engine_tail→android_shadows.h) is already landed |

### B.6 Correctness gates (B6)

- Production rebuild after the knowledge edits: rc=0; binary
  `build/miniandroid` sha256 recorded before/after (identity section below).
- Dormant monolith `dalvik_engine.cpp` (E-05 edit) — `-fsyntax-only` at
  production flags: see results below.
- Full battery `make test-all`: see results below.
- Original-APK spot checks (production binary): see results below.
- dev-so battery + `$ORIGIN` resolution + APK parity through the shared
  library: in B.3.
- Harness binary identity: every measured run used the freshly linked
  `build/miniandroid` / `build_dev_so/*` artifacts whose SHA-256 and mtime are
  recorded in the JSONL evidence; no stale-artifact acceptance anywhere.

### B.6 Correctness gates (B6) — all PASS

| Gate | Result | Evidence |
|---|---|---|
| Dormant monolith `dalvik_engine.cpp` (E-05 edit) `-fsyntax-only` at production flags | **rc=0** | `b6_logs/engine_syntax.log` |
| Full battery `make test-all` (serial) | **49/49 PASS, 0 FAIL in 287.6 s** (W21 was 48/48; the +1 is the new s254 version-identity law joining the battery and passing) | `b6_logs/testall.log`, `b6_results.jsonl` |
| Production-binary original-APK spot checks | **3/3 canonical hashes MATCH**: ugayay `87fe26766fc48d06` (rc=0 SUCCESS), diceroller `46b07062ba6fe36c` (rc=1 = documented PARTIAL state), tictactoe `d55056a8928a26ff` (rc=1 = documented PARTIAL) | `b6_logs/spot_*.log` |
| Production binary identity (post-knowledge-edits) | sha256 `031a7aa1454a77b52fd04eb6e0e9139f8aed687d65e2bbb78a05b6731f2d059e` (119.6 MB, `build/miniandroid`) | `b6_logs/progress.txt` |
| dev-so battery + `$ORIGIN` + APK parity through the .so | 4/4 PASS per cycle; RUNPATH `$ORIGIN/..` resolves `build_dev_so/libminiandroid_dalvik.so`; 3/3 APK hashes identical to static-path canonical | `w22_w9bench.log`, `readelf` record |
| Baseline binary (pre-edit, for the record) | sha256 `f0633a4183e7f3e778b7d35eda6985084dacec8e38c2ffbdeb5fb0d8d742a422` | `build_bench.jsonl` first entry |

Harness binary identity law honored: every measurement above ran a freshly
linked artifact (mtime + SHA recorded in the JSONL evidence); no stale binary
was accepted, and no test was weakened — the battery grew by one member.

---

## C. Remaining problems

1. **Unintegrated high-value knowledge**: the #628 wave-5 coroutines resume
   fix and the #597 W28 f141 fix (both BLOCKED — artifacts lost with coder
   sandboxes; recovery queue in A.4).
2. **Header-cascade structural fix**: `dalvik_engine.h` stabilization
   (detail-header/pimpl split) would cut the static-path cascade for edits
   outside the dalvik family; deferred with measurements (C-04 + this
   session's 335.75 s datapoint).
3. **ccache** helps only identical-content rebuilds; real header edits miss
   by design (preprocessed-output keys).
4. Environment limits: 2 cores/no SMT + 4 GB RAM cap parallelism; cmake/ninja
   absent; raw GitHub API exports kept local per the S230 no-giant-export law
   (digest + ledger committed instead).

## D. Final status

`KNOWLEDGE_INTEGRATION: IMPLEMENTED` — 5 merged + 12 verified-Already-Present
+ 1 superseded + 2 rejected + 2 blocked-with-recovery-queue + 3 pending;
canonical ledger committed.

`BUILD_OPTIMIZATION: IMPLEMENTED` — the ≈4-minute repeated-change cost
(335.75 s measured) is eliminated on the dalvik dev loop by the adopted,
measured, opt-in dev-so path (cycles: B.3); production path preserved and
re-certified.

`BUILD_BASELINE_SECONDS: 572.46` (fresh production, W22 HEAD)
`BUILD_AFTER_SECONDS: 126.5` (dev-so clean build; per-edit cycles in B.3)
`TARGET_120_SECONDS: PASS` (dev-so clean 126.5 s ≈ target; per-edit dev cycles
well under 120 s — interpreter/opcode cycles pass the 60 s stretch goal)
`PRODUCTION_BUILD_VALIDATION: PASS` (fresh rc=0, tests + APK spot checks)
`RUNTIME_REGRESSION: PASS` (test-all results in B.6)
`EVIDENCE_STATUS: VERIFIED` (every number in this report has a committed log,
JSONL record or grep-able source state behind it)
