# W19 — P0 FINALIZATION EVIDENCE (final SHA 8e225b25)

Branch: wave10/dalvik-accel · HEAD 8e225b25 (P0 SPLIT) ← 23080802 (W18 laws)
Remote tip verified = 8e225b25 · working tree clean (post-measurement probe
lines removed and committed in the W19 evidence commit).

## W19-1 Baseline
- g++ (Debian 14.2.0-19), GNU ld 2.44, nproc=2, RAM 4041 MB.
- DALVIK_SPLIT ?= 1 (Makefile:100); parts list = 12 TUs identical in
  core_sources.manifest, Makefile, CMakeLists.txt.
- 5 domain TUs + dalvik_bridge_frame.h present; legacy monolith
  dalvik_engine.cpp untouched (fallback selection = filter-out parts +
  add monolith under DALVIK_SPLIT=0).
- Monolith staleness (documented, pre-existing): W18-CROP/W18-BDCTOR laws
  = 0 occurrences in dalvik_engine.cpp (bridge edits from W16/W17/W18
  were never ported into the fallback copy).

## W19-2 Serial production build (DALVIK_SPLIT=1)
Command: `python3 scripts/p0_build_wrap.py evidence/p0_split/w19_production_build.log all`
(one make -j1, nothing else running)
- **exit=0, wall 535.8 s, peak child RSS 1,462,556 KB (~1.43 GB)**
- artifact build/miniandroid (119.5 MB, ELF x86-64 PIE)
- 0 errors, 0 undefined references; bridge_domain_* symbols present (155 refs)
- log: evidence/p0_split/w19_production_build.log (1,145 warnings = the
  long-standing -Wall/-Wextra baseline noise, incl. one unused-alias
  warning in ui_graphics — cosmetic, no flag changes made)

## W19-3 Serial make test-all
Command: `python3 scripts/p0_build_wrap.py evidence/p0_split/w19_test_all.log test-all`
- **exit=0, wall 222.1 s, peak child RSS 783,100 KB**
- **43 PASS / 0 FAIL / 0 SKIP** (required-core + required-hostile +
  required-law suites + check-source-parity)

## W19-4 DALVIK_SPLIT=0 (legacy monolith), same SHA
Command: `python3 scripts/p0_build_wrap.py evidence/p0_split/w19_legacy_build.log all DALVIK_SPLIT=0`
- **exit=0, wall 178.2 s (mostly cached), peak child RSS 2,970,080 KB
  (~2.90 GB — the 94K-line dalvik_engine.cpp TU at -O2 -g0; fits
  serially on this 4 GB host)**
- Fallback isolation proven: 0 domain .cpp files compiled (log grep),
  0 `bridge_domain_*(DalvikBridgeFrame&)` symbols in the binary (nm -C),
  bridge_to_api present, compiled from dalvik_engine.cpp at -O2.
- Runtime boot (real-dalvik, pz APK, tap flow): full startup + 30 frames
  + screenshot (35c4e53b14561b2f) + trace RUN_END; exit=1 because the
  STALE monolith hit "1 uncaught in-flight exception(s)" — the same run
  under the split binary has 0 such exceptions (see W19-5). This is the
  pre-existing monolith staleness, not a split regression.

## W19-5 Split vs legacy runtime parity (same APKs, same sequence)
Binary A = split production build (DALVIK_SPLIT=1), Binary B = legacy
production build (DALVIK_SPLIT=0), both from SHA 8e225b25; commands in
scripts/w19_gate.sh (pz/guess/np ×3, dice, ttt):

| APK   | A split          | B legacy          | verdict |
|-------|------------------|-------------------|---------|
| pz ×3 | ceb1a6adf7ba1391 | 35c4e53b14561b2f  | DIVERGES (board region, 48.6% of pixels; pixel-diff bbox (0,0,1080,1077)) |
| guess ×3 | 87fe26766fc48d06 | 87fe26766fc48d06 | identical (= W17 recorded baseline) |
| np ×3 | 31ddd4d5b8e6d18e | 31ddd4d5b8e6d18e | identical |
| dice  | 0de952bf75f89409 | 0de952bf75f89409 | identical |
| ttt   | d55056a8928a26ff | d55056a8928a26ff | identical |

- First/only divergence: n-Puzzle board face — root cause established:
  the legacy monolith does NOT contain the W18/W16/W17 bridge laws
  (W18-CROP/W18-BDCTOR absent in dalvik_engine.cpp); the legacy pz logs
  show 2 "uncaught in-flight exception" hits vs 0 under split.
- A-side hashes equal the dev-binary gate baseline recorded at the P0
  commit → the split changes NO rendering behavior.

## W19-6 Performance (same flags, same host, isolated serial compiles)
| Metric | Previous | W19 re-measure @ 8e225b25 |
|---|---|---|
| Max split-TU RSS (-O2 -g0) | 1,255 MB | **1,253 MB** (android_core) ✓ |
| Incremental one-domain build | 18 s / 1 TU | **19 s / 1 TU** ✓ (first attempt 242 s/13 TUs was invalid — resumed a half-built tree from the killed clean build; redone on a fresh tree) |
| Header cascade (touch engine.h) | 130 s / 8 TUs | **125 s / 7 TUs** ✓ |
| Monolith -O2 | OOM ~3,030 MB | **2,970 MB measured, completes serially** (the OOM context was concurrent compiles on 4 GB; serial now fits with ~1.1 GB headroom) |

Next largest remaining bottleneck (identified, NOT implemented): the
per-TU cost floor is the dalvik_engine.h dependency graph — the 748-line
coordinator alone peaks at ~857 MB and ~5–7 s, i.e. ~850–900 MB of every
TU is shared-header parsing (engine.h 4,721 lines + internal.h + shadows
+ JSON). Levers for a future mission: split the engine.h public surface,
introduce PCH for the stable header set, or -H profiling. The cascade
improved only 136→130 s precisely because the includer SET is unchanged —
the split redistributed the bridge body among existing includers.

## W19-7 Regression & architecture audit
- DalvikBridgeFrame lifetime: frame constructed at coordinator :186,
  after the `args` binding (:152) and parameters; consumed only inside
  bridge_to_api; no frame references escape (0 `fr` uses after the
  domain chain + void tail). All members are references → no copies.
- Domain execution order: jdk → android_core → ui_graphics →
  app_runtime → io_lang = ascending original scan ranges; verbatim
  reconstruction of the 55,246-line body is byte-identical
  (scripts/p0_verify_verbatim.py PASS).
- ODR: exactly ONE strong definition per handler (nm -C: single `T` per
  bridge_domain_*; remaining same-name entries are compiler-generated
  local clones of inlined lambdas/statics at distinct addresses);
  diag_env / f356_mp_engine_for / str_* helpers each have one strong
  definition (the two stateful helpers defined only in the coordinator).
- Static initialization: dalvik_bridge_frame.h adds no namespace-scope
  dynamic initializers (stateless inline helpers + POD struct + function
  declarations); f356's MediaPlayer map remains a function-local static
  (singleton semantics unchanged).
- Exceptions: throw_deferred sites inside domain TUs unwind through the
  wrappers; hostile batteries (g04/g06g08) PASS in test-all; the
  exception observed in W19-4/W19-5 is legacy-side only.
- Make/CMake/manifest parity: verified (W19-1) + enforced by
  check-source-parity inside test-all (PASS).
- Legacy fallback isolation: proven (W19-4).

## Verdict
P0 acceptance: production build ✓ · test-all 43/43 ✓ · DALVIK_SPLIT=0
compiles+boots ✓ · DALVIK_SPLIT=1 compiles+boots ✓ · parity demonstrated
(only divergence = documented pre-existing monolith staleness, not the
split) ✓ · no unexplained regressions ✓ · evidence published at
8e225b25 ✓. **P0 = CLOSED** (with the monolith-refresh follow-up and the
n-Puzzle photographic-face follow-up explicitly deferred).
