# CONT-17 — THE 100-TASK MARCH: EXECUTION REPORT

Session: 2026-10-07 · HEAD a0184622 · start binary a8761a482a186eac (CONT-16 record)
· final binary **f73705cf6e159ef8** · registry 575 rows.

## A. Lineage + lock

- GitHub live access verified; issues #375/#379/#380 re-fetched — **zero new
  directives** since CONT-16 (evidence/cont17/github_issues_refetch.json).
- Git lineage map for CONT-1..16 built from 60 commits (lineage_map.json):
  CONT-13 = NOT FOUND IN GITHUB (severed session); CONT-14/16 = local waves.
- Registry integrity: 575 rows, 0 duplicate IDs, 0 invalid statuses, declared
  counts == actual counts (registry_audit.json).
- KB searchlight compliance: manifest present, 0 bulk-import markers.
- F-NEW-266 protection: both dispatch wiring sites + probe + registry intact.

## B. The march (100 tasks; full per-task ledger in TASK_RESULTS.md)

49 DONE · 6 PARTIAL · 45 DEFERRED-with-reasons. Two engine rebuilds. Key events:

### B.1 F-NEW-265 re-attribution (runtime-proven)
The dooz null-text chain is downstream of the F084 spin:
`Lnb0.H()V#2837` active-cycle stub → nested state-machine step skipped →
`Lrh0.b` spins 99.97M instructions in one invocation → F084 budget halt →
VirtualMachineError → APP-BOUNDARY → next-frame partial state → null
CharSequence into `Lm7.<init>` → NPE cascade → measure death → 0 content ops.
**The true first divergence is the spin — F-NEW-217's waiter-resume domain.**

### B.2 F-NEW-265 ARM-A implemented (bounded re-entrance law)
The M3-19 active-cycle stub assumed same-identity re-entry == infinite recursion.
ART has no such stub. LAW: the FIRST simultaneous same-identity re-entry executes
real DEX (nesting==1); deeper simultaneous re-entries stub (nesting>=2);
MAX_RECURSION_DEPTH remains the backstop. Live proof: 7 [M3-19-REENABLE] legal
re-entrances executed at f73705cf; deeper cycles still bounded; 6 anchors ×3
byte-identical (zero drift); dooz verdict honestly unchanged (the spin dominates).

### B.3 F-NEW-264d six collection laws implemented (fcol 3/18 → 11/18)
- LAW-A indexOf/lastIndexOf; LAW-B iterator write-back (remove with the real ISE
  law, set/add via last-returned cursor bookkeeping);
- LAW-C FUNCTION-OBJECT CHANNEL: the engine executes collection lambdas
  (removeIf/forEach/merge/computeIfAbsent/sort comparators) as REAL DEX —
  engine `invoke_function_object` + shadow `dex_lambda_slot`;
- LAW-D deque kind-faithful access + ArrayDeque claim; LAW-E kind-store equality
  + getOrDefault; LAW-F removeAll/retainAll/containsAll.
- Flipped PASS: K4, K5, K9, K11, K13, K16, K17, K18. Residuals documented
  (probe-APK-bundled java.util double-store; 2 probe expectation bugs vs the
  OpenJDK cursor law; subList view + stream pipeline = future bounded tasks).

## C. Roots closed / flipped this wave

| ID | Change | Evidence |
|----|--------|----------|
| F-NEW-265 | PENDING → PARTIAL (ARM-A implemented; re-attributed to the F-NEW-217 spin) | run logs + 7 re-entrances live |
| F-NEW-264d | REGISTERED → PARTIAL (6 laws implemented; 8 probe rows flipped) | fcol 11/18 at f73705cf |
| F-NEW-256 | → SUPERSEDED-BY-EVIDENCE (265 chain pointer) | registry |
| R-NEW-381 | linkage to the 265 chain recorded | registry |
| Counter | status_counts regenerated; total_roots=575 | registry_audit |

## D. Verification battery (final binary f73705cf6e159ef8)

- Anchors ×3 byte-identical 6/6: dooz d602648e · microtimer da73010a ·
  unote 4f1a9e4e · gmdice f3b483fe · opencalc a976d2f9 · chess b5a7a35d
  (chess re-run under the correct package jwtc.android.chess — cont16 script's
  stale package row recorded as a script bug).
- f266 6/6 · f259 7/7 · f259g 12/13 (row L = registered honest artifact) ·
  fcol 11/18 · negatives 19/19 · skill 13/13.
- Six games 6/6 REAL_APP_CONTENT ×3 (28/71/401/263/44/35 ops — exact CONT-15
  values). Telegram forkgram cf4c41e62ceb6557 REAL_APP_CONTENT (11 ops,
  117,133 px). tictactoe_emmanuel b5a7a35d honest DEFAULT_BACKGROUND_ONLY
  (F-NEW-219 JNI entry unchanged).

## E. Next frontier

**F-NEW-217** — MutexImpl waiter-resume across the virtual thread park/resume
model. The spin arm (`Lrh0.b`, state-machine cycling under changed decision
inputs — invisible to the visit-threshold detector) is the single highest-ROI
root: every Compose app that reaches coroutine dispatch machinery rides the same
law. Fix sketch: extend the park-drain law (R-NEW-345) to bound-spin points —
interleave queued scheduler work at spin checkpoints so the unlocker executes,
instead of destroying the frame at the budget halt; plus the waiter-resume
protocol (a resumed continuation must not re-run release paths twice).
Secondary queue: Integer.compareTo bridge law (K14), subList write-through view
(K3), stream pipeline (K15), probe-expectation fixes (K2/K12), stale-status
sweeps T-30..T-36.
