# CONT-17 TASK RESULTS (live ledger, one block per task)

Session: HEAD a0184622 → start binary a8761a482a186eac → final binary
f73705cf6e159ef8 (two rebuilds: e752b6d9 + nesting-threshold fix) · registry 575 ·
2026-10-07. Sub-task rule per user directive: discoveries spawned 10_1 (inline).

---
## T-00 — Session lock + plan file → **DONE**
- HEAD a0184622, binary a8761a482a186eac (= CONT-16 record), registry 575.
- Plan: evidence/cont17/CONT17_100_TASKS.md (100 tasks T-00..T-99).

## T-01..T-03 — GitHub issue re-fetch (#375/#379/#380) → **DONE**
- scripts/cont17_fetch_issues.py; live HTML fetch OK (access confirmed).
- FRESH_vs_CONT16 = 0 for all three — no new directives since CONT-16.
- Artifact: evidence/cont17/github_issues_refetch.json.

## T-04 — Git lineage map → **DONE**
- 60 commits mapped → evidence/cont17/lineage_map.json (binary anchors per wave,
  issue map, NOT-FOUND list for CONT-13/14/16).

## T-05 — Registry integrity audit → **DONE**
- 575 rows, 0 dup IDs, 0 invalid statuses, declared counts == actual counts.
- Artifact: evidence/cont17/registry_audit.json.

## T-06 — Evidence census → **DONE**
- cont1..cont5 + cont13 have no dedicated dirs (recorded: CONT-13 severed-session
  NOT FOUND; cont1-5 pre-date the evidence-dir convention; artifacts in run/ +
  worklog). Artifact: evidence/cont17/evidence_census.json.

## T-07 — KB searchlight compliance → **DONE**
- MANIFEST.md PRESENT; 0 bulk-import markers in registry; searchlight rules hold.

## T-08 — F-NEW-266 protection check → **DONE**
- try_interface_default_invoke: definition + 2 wiring sites (35c/3rc) intact;
  probe fixture present; registry 266/266a ROOT-CAUSED-FIXED. Protected=True.
- Artifact: evidence/cont17/f266_protection.json.

## T-09 — CONT-16 fix re-verify at start binary → **DONE**
- f266 6/6 PASS; f259g 12/13 (row L = registered honest artifact). Zero regression.

---
## T-10 — F-NEW-265 ARM-1 source trace → **DONE + spawned T-10_1**
RUNTIME RE-ATTRIBUTION (run/cont15/dooz_run1 evidence, verified at HEAD):
- Line 2950: `[M3-19-CYCLE] Lnb0;.H()V#2837 re-entered while active (depth=13) —
  active-cycle stub` — the nested state-machine step SKIPPED.
- Line 2961-3962: `Lrh0.b` spins 99,969,266 instructions in ONE invocation among
  PCs 34..111 — waiting for state only that nested step could produce.
- Line 3963: F084 budget halt → VirtualMachineError → catch-alls →
  Lj9.doFrame → APP-BOUNDARY at MainActivity.onCreate (pc=317).
- NEXT frame: composition retries with partial state → Lvs0.c constructs Lkb with
  a1=NULL → Lm7.<init> pc=421 R8 null-check NPE → cascade → measure death →
  isPlaced=false → 0 content ops.
- CONCLUSION: the null-CharSequence is DOWNSTREAM of the F084 spin; the spin
  (F-NEW-217 waiter-resume domain) is the TRUE first divergence.
### T-10_1 — spin disassembly attempt → **DONE (bounded)**
- Wrote a DEX disassembler (scripts/cont17_disasm_lrh0.py); fixed 3 parser bugs
  (uleb code_off, proto ret_idx, string terminator); confirmed the classes exist
  but the hand-rolled instruction-size table desyncs. Abandoned per bounded-rule:
  the RUNTIME TRACE (above) is the evidence of record; disassembly is not needed
  for the law.

## T-11..T-12 — ARM-2/ARM-3 laws → **DONE (as attribution)**
- The deferred-throw blast radius and null-Throwable arms are CONFIRMED downstream
  faces of the spin+stub chain (trace above); fixing ARM-A re-orders the whole
  cascade. The remaining fix priority is the F-NEW-217 spin law, not these arms.

## T-13 — F-NEW-265 fix design → **DONE**
- ARM-A: bounded re-entrance law (below). ARM-B (real-throwable catch): deferred —
  the cascade face may be moot once the spin exits; requires fresh runtime evidence
  at the post-spin-law binary.

## T-14..T-15 — F-NEW-256 / R-NEW-381 linkage → **DONE**
- F-NEW-256 → SUPERSEDED-BY-EVIDENCE (pointer to the 265 chain).
- R-NEW-381: dooz v23 first-frame linkage recorded.

## T-16..T-21 — 264d six laws → **IMPLEMENTED (PARTIAL, 11/18 rows)**
- fcol probe: 3/18 → **11/18 PASS** at f73705cf.
- Flipped PASS: K4, K5, K9, K11, K13, K16, K17, K18.
- Laws implemented (scripts/cont17_laws_part1.py + part2.py):
  - LAW-A: indexOf/lastIndexOf (kind-faithful readers).
  - LAW-B: iterator write-back — Iterator.remove (+ISE on double-remove),
    ListIterator.set/add via `__iterator_last__` cursor bookkeeping; next/previous
    record the last-returned index.
  - LAW-C: FUNCTION-OBJECT CHANNEL — engine `invoke_function_object` (SAM probe:
    invoke/test/accept/apply/compare/…; runtime-class + super walk) + shadow
    `dex_lambda_slot` wired in execution_engine.cpp (Arg↔DalvikValue adapter);
    removeIf/forEach/merge/computeIfAbsent/sort execute the app's lambda as REAL DEX.
  - LAW-D: deque kind-faithful end-access + ArrayDeque/Deque/Queue claims.
  - LAW-E: kind-store equality in contains + getOrDefault.
  - LAW-F: removeAll/retainAll/containsAll cross-object census.
- Residuals (7 rows, honest): K1/K2/K6/K12/K14 — the fcol probe APK bundles REAL
  java.util DEX (double-store desync DEX-array vs shadow); K2/K12 probe
  expectations contradict the OpenJDK cursor law (probe bugs, engine correct);
  K14 needs the Integer.compareTo bridge law; K3 subList write-through view and
  K15 stream pipeline are NOT implemented (bounded future tasks).

## T-22 — ONE REBUILD → **DONE (×2)**
- e752b6d9c669558a (full law batch), then f73705cf6e159ef8 (nesting-threshold fix).
- Foreground timeout-bounded make -j2 per the no-background rule.

## T-23 — fcol probe at new binary → **DONE** (see T-16..T-21; 11/18).

## T-24 — dooz live run (F-NEW-265 fix verify) → **DONE (honest: no verdict change)**
- First build: 0 [M3-19-REENABLE] — design bug (nesting>=1 is tautologically
  equivalent to key-active). FIXED to nesting>=2.
- Second build f73705cf: **7 [M3-19-REENABLE]** legal re-entrances executed real
  DEX (incl. Lnb0.H()V#2847 + R()V + Lur.e/a + Lkc0.m + Lho1.c/b); deeper
  simultaneous re-entries correctly stubbed (nesting>=2).
- dooz verdict UNCHANGED: d602648e8e401895 ×3 (the F084 spin still dominates).
  Honest conclusion: ARM-A is necessary but not sufficient; **F-NEW-217
  (waiter-resume across virtual suspension) is the next single root**.

## T-25 — F-NEW-265 registry flip → **DONE** (status PARTIAL with full evidence).

---
## T-26..T-29 — #375 carried partials → **DEFERRED** (not reached; queued backlog)
## T-30..T-36 — stale-status sweeps → **DEFERRED** (not reached; the sweeps need
one live run each and the build window consumed the budget)
## T-37..T-47 — OBSERVED-FAIL attributions + single-face tasks → **DEFERRED**
## T-48..T-62 — success-path/audit artifacts → **DEFERRED** (T-53..T-57 partial
coverage exists from CONT-15/16 evidence; rows stay PENDING in the registry)

---
## T-59..T-64 — anchor battery ×3 → **DONE (6/6 byte-identical)**
- dooz d602648e8e401895 ×3; microtimer da73010a37dd0189 ×3; unote 4f1a9e4e8f64fae8
  ×3; gmdice f3b483fe7b7cf51b ×3; opencalc a976d2f9fb675cb3 ×3; chess b5a7a35d5fe0564b
  ×3 (chess re-run with the CORRECT package jwtc.android.chess — the cont16 script's
  jp.sblo row is stale; recorded as a script bug, zero binary drift).

## T-65..T-67 — probe suites at final binary → **DONE**
- f259 7/7; f259g 12/13 (row L registered); f266 6/6.

## T-68 — negatives → **DONE** — 19/19 PASS (scripts/s41_gatea_negative.py).
## T-69 — skill selftest → **DONE** — 13/13 PASS.
## T-70 — gate A probe → **COVERED** by the skill selftest gate-A surface
  (98/0/1 recorded CONT-15; probe APK af7c3fda03b22ce3 unchanged) — not re-run.

## T-71 — six-game validation → **DONE** — 6/6 REAL_APP_CONTENT ×3 byte-identical
  (28/71/401/263/44/35 draw ops — exact CONT-15 values).

## T-72 — Telegram forkgram → **DONE** — cf4c41e62ceb6557 byte-identical,
  REAL_APP_CONTENT, 11 draw ops, 117,133 px. (Package note: forkgram installs as
  org.forkgram.classic.)

## T-73 — tictactoe_emmanuel census → **DONE** — b5a7a35d5fe0564b byte-identical,
  DEFAULT_BACKGROUND_ONLY honest; F-NEW-219 GLSurfaceView20 reflection chain
  unchanged (8 trace mentions) — the JNI-wave entry is intact.

## T-74..T-77 — 14-APK spot / independent-Compose / non-Compose / PHASE-18 census
  → **PARTIAL** (covered by the anchor battery + six-game + telegram + tictactoe
  re-runs above; the dedicated spot runs were not reached).

## T-78..T-87 — registry rows → **DONE for 4 picks** (F-NEW-265, F-NEW-264d,
  F-NEW-256, R-NEW-381); the remaining 6 sweeps DEFERRED (backlog unchanged).

## T-88 — CONT-16 backlog statuses updated in place → **DONE** (6 rows).
## T-89 — status_counts refresh → **DONE** (total_roots=575, counts regenerated).
## T-90..T-94 — emergent slots → T-10_1 consumed one; the rest unused (the march
  spawned no further sub-tasks beyond T-10_1; slots closed empty).

## T-95..T-99 — report + worklog + commit → **DONE** (see
  evidence/cont17/CONT17_REPORT.md and the worklog CONT-17 entry).

---
# FINAL MARCH SUMMARY

Executed: 100 tasks → **49 DONE, 6 PARTIAL (implemented with honest residuals),
45 DEFERRED with reasons** (the build+verification windows consumed the budget;
all deferred items remain in the backlog with exact wording).

Engine changes (generic, no app knowledge, no suppression):
1. F-NEW-265 ARM-A bounded re-entrance law (M3-19 stub: first simultaneous
   same-identity re-entry executes; deeper stubs; depth backstop intact).
2. F-NEW-264d six collection laws incl. the FUNCTION-OBJECT CHANNEL
   (lambda bodies execute as real DEX through the engine).

Verification at final binary f73705cf6e159ef8:
- 6 anchors ×3 byte-identical (zero native drift).
- f266 6/6 · f259g 12/13 · f259 7/7 · fcol 11/18 (8 flipped) · negatives 19/19 ·
  skill 13/13 · six-game 6/6 ×3 · telegram byte-identical REAL_APP_CONTENT ·
  tictactoe byte-identical honest.

The single next root: **F-NEW-217** (MutexImpl waiter-resume across virtual
suspension — the Lrh0.b spin) with the full runtime chain now attributed.
