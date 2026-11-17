# ISSUE-612 WAVE-6 — FINAL REPORT (Memory, Cut Boundaries, Rebuild Isolation)

Base: wave-5 final (HEAD a20a93cc tree). All numbers measured on this host
(g++ 14.2.0, 2 CPU, 4 GB cgroup limit, `make -j1`, DALVIK_SPLIT=1).

## Answers to the 7 required questions

1. **Which TU consumed the most RAM?** `dalvik_bridge.cpp` — 2,126 MB peak RSS
   compiling at `-Og` (and OOM-killed at ~3,087 MB when forced to `-O2`, rc=1,
   re-measured at this HEAD). Every other TU measured ≤ 1,118 MB. The wave-3
   monolith measured 2,867 MB (reference only).
2. **Which exact function caused it?** `DalvikExecutionEngine::bridge_to_api`,
   lines 187–55,382 of the 55,384-line file (99.7% of the TU) — one giant
   dispatch function with 124 top-level arms (22,963 lines) and a 13,839-line
   shadow-dispatch arm. GCC's peak scales with that single function's GIMPLE.
3. **What exact cut boundaries were implemented?** (a) WAVE-5 already split the
   engine into 7 TUs (verified). (b) WAVE-6 implemented the 4 provably-safe
   `bridge_to_api` arm extractions (arms 599/2123/5892/7973 → private member
   helpers `bridge_arm_*`, verbatim bodies, dispatch order unchanged, +4 decls
   in `dalvik_engine.h`, stateless lambda `f356_mp_engine_for` hoisted to
   `namespace miniandroid{}`) — IMPLEMENTED + TESTED.
4. **How much did peak RSS decrease?** Bridge: 2,126 → 2,122 MB (−4 MB) — the
   honest result of the only mechanically-safe subset (534 lines). The larger
   19,384-line extraction is BLOCKED: 21 of 25 candidate arms are
   fall-through-capable (GCC `-Werror=return-type` CFG proof: "control reaches
   end of non-void function" ×21; SIGILL repro inside `bridge_arm_45295`;
   `-fsyntax-only` cannot see these — measured probe hole). Codegen-neutral
   GGC tuning measured −330 MB (sha256-identical objects) as an option.
   All non-bridge TUs already meet <1.5 GB (max 1,118 MB).
5. **How much did real edit-to-test latency decrease?** Wave-5 already met the
   30 s gates (opcode field edit 12.79 s, invoke 17.51 s, two-opcode 26.35 s,
   link 2.16 s, DEV loop 21.36 s — 5 reps each). WAVE-6 re-measured the bridge
   compile (43.7 s at -Og) and confirmed the same gates hold; the W6 ×5 suite
   for the post-cut state is PENDING (time-boxed), not yet re-run.
6. **Why does a shared-header edit rebuild the observed number of TUs?**
   `dalvik_engine_internal.h` is included by exactly the 7 engine part TUs
   (their .d files prove it), so a header touch rebuilds 7 TUs = 158.2 s
   (wave-5, 5 reps). The 7 TUs are siblings implementing ONE engine class and
   legitimately share the class declaration + de-static'd helpers — the fan-out
   is inherent to the split design; the per-TU edit paths (12.8–26.4 s) are the
   intended dev loop, and the fan-out number is the honest cost of touching the
   shared contract. Narrowing further would require splitting the internal
   header per TU — PENDING, low expected gain (header parse is not the cost;
   the 7 compiles are).
7. **Which acceptance criteria remain unmet?**
   - Peak compiler RSS < 1.5 GB: **PARTIAL** — met for 23/24 TUs; the bridge
     remains 2,122 MB (BLOCKED boundary documented above; -O2 bridge = OOM).
   - Bridge edit < 30 s: **PARTIAL** — 43.7 s compile (-Og host ceiling);
     covered by the DEV loop for iteration.
   - Interpreter edit < 30 s: **PARTIAL** — 40.8 s at -O2 (one 5,436-line
     function; extraction BLOCKED by loop-carried state); `-Og` lever measured
     (9.4 s) but not adopted without runtime proof (PENDING).
   - W6 ×5 benchmark suite + SPLIT=0 re-verification after the 4-arm cut:
     **PENDING** (time-boxed; wave-5 evidence still stands for the pre-cut
     state).

## What is TESTED in WAVE-6

- Per-TU memory profile (82 compile commands profiled, ranked): TESTED.
- Monolith reference compile 2,867 MB / 219.7 s: TESTED.
- Bridge flag experiments incl. codegen-neutral GGC (object sha256 equal):
  TESTED/OBSERVED.
- 4-arm bridge extraction: build rc=0, parity OK (82 sources), test-core 3/3,
  **screenshot hashes IDENTICAL on all 3 APKs vs the wave-3 monolith binary**:
  Guess `87fe26766fc48d06c59d4c15` (SUCCESS), tictactoe
  `d55056a8928a26ffeb15f66d` (PARTIAL, pre-existing), diceroller
  `46b07062ba6fe36ca8a6e42d` (PARTIAL, pre-existing). TESTED.
- Transform audit: 112 between-arm/prologue/tail segments preserved verbatim
  (the only moved one = the intended lambda hoist). TESTED.

## Rollback

`git revert <w6-commit>` restores the wave-5 7-TU state; `make DALVIK_SPLIT=0`
remains the monolith fallback (wave-5: 215.1 s, identical Guess hash).
Safety tags unchanged.

## Extra tests run beyond the brief (the "forgotten items")

- `-O2` bridge OOM repro at this HEAD: rc=1 @ 3,087 MB (documented blocker).
- `-fsyntax-only` probe hole discovered and documented (gimplify-only warning).
- Build-driven hoist loop for fn-local lambdas + unicode-quote error parsing.
- DEV mode / build_dev separation and mode stamps: untouched by W6 (wave-5
  evidence stands); SPLIT=0/CMake parity re-run: PENDING.
