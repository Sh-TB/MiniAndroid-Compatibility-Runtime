# S104 REPORT — ROOT-CAUSE EXECUTION → REAL APK IMPACT

Wave: S104 (continues S103 HEAD `5ea74751`). Rule honored: every NEXT
TEST/NEXT ROOT from S103 either executed this wave or moved to a named,
evidence-backed queue — nothing silently re-labeled.

## Wave summary (report format §17)

```text
ROOT    R-009 SWITCH-KEY-WIDENING
STATUS  FIXED (L5) — commit 4feaaeda
FINDINGS        P082 SOLVED (packed-switch), P084 PARTIAL (merged lambdas:
                law fixed; family rerun exposes the NEXT divergence below)
SOURCE EVIDENCE AOSP dalvik bytecodes (31t + packed-switch-payload i32
                targets); R8 horizontal class merging ($r8$classId ctor
                dispatch); DEX ground truth parsed raw (scripts/s104_*)
PROBE           [S104-SW] pre: key=0/dest=5 (wrong branch);
                post: key=5/dest=11 + key=4/dest=5 — 3/3 deterministic
REAL APKs       solitaire (12->0 errors, SHA 59fdbfcd60b86a23 x3),
                sgtpuzzles (0->0, unchanged), dooz (18->18, mix changed)
BEFORE/AFTER    solitaire census errors 12 -> 0
REGRESSION      battery 105/105 ALL PASS; census distribution unchanged
3-RUN           solitaire 3/3 byte-identical screenshots
NEW ROOTS       compose onAttachedToWindow Handler-null (see NEXT)
NEXT ROOT       Lr;.onAttachedToWindow PFQ null-recv (compose host
                wiring, ticket #350) — the exact S103 NEXT TEST, now
                executing: solitaire rerun done, chain walked past
                LocalDensity/LocalSavedStateRegistryOwner
```

## Second root: R-004 CLASS-IDENTITY (S103 ROOT-005) — implemented, TESTED

- Law: AOSP AppCompatViewInflater creates the AppCompat/material class;
  real objects ARE those classes. The engine inflated the family under
  platform descriptors → identity divergence.
- Measured fan-out (bytecode-accurate, corrected decode): **60/201 APKs**
  bundle + statically type-test the family; 12-class coverage.
- Fix: real-descriptor inflation (S101 Toolbar law corpus-wide) + 6
  missing kFrameworkViews extends edges (commit series this wave).
- Gate: battery 105/105; 6 affected titles pixel-identical before/after;
  errors unchanged. Preventive identity law — no error-count delta
  claimed (honest: no census title currently fails on this family).
- Discovered + corrected: the S103 "22/59 type-test" file conflated
  dex-presence with type-testing; both measurements now committed
  (run/s104/r004_typescan.json).

## GL frontier measured (GL_NEED_LEDGER)

- `docs/GL_NEED_LEDGER.{json,md}` built by raw `method_ids[]` scan.
- Census verdict: **EGL10 setup only, 6/54 APKs; GLES20+ refs = 0** —
  the libGDX-family titles render through bundled `libgdx.so` (JNI),
  not Java GLES. The GLES bridge stays demand-gated (measured demand
  = 0); the true GL frontier is native-library loading (out of the
  Java-runtime scope). S103's non-implementation decision now carries a
  corpus-wide number.

## Living ticket registry (P001..P500)

- `docs/RESEARCH_500_PROBLEM_REGISTRY.{json,md}` — canonical ticket
  layer over the R500 audit ledger: P001..P136 real tickets +
  **P137..P500 = 364 explicit TRUNCATED_INPUT rows** (nothing invented).
- `docs/RESEARCH_FIX_CROSSWALK.md` — FIX-001..005 → every ticket each
  fix solves, checked individually.
- `docs/RESEARCH_PROGRESS.md` — mechanical roll-up.

```text
registered: 500 (136 real + 364 TRUNCATED_INPUT)
solved: 31   implemented/tested: +1 (P084 PARTIAL)
reproduced: 28   observed: 19   confirmed(repo): 12
researched: 21   out-of-scope: 20   false-lead: 4   blocked: 0
unique named roots: 11 (R-001..R-009 + umbrella + host-only family)
largest shared root: R-001 (18 tickets L5)
```

## Honest deltas this wave

- Real runtime improvement: **solitaire 12 → 0 census errors** with the
  first divergence now past the whole saved-state wiring (the exact
  S103 NEXT TEST). Visual state remains blank — the compose draw path
  is the open frontier; no visual-improvement claim is made.
- Two S103-era claims corrected by re-measurement (22/59; R8-merged
  lambda row) — both recorded in the ledger with evidence.
- API stuffing check: zero new APIs added; one interpreter widening
  law + one inflation identity law + 6 seed edges (all shared, all
  AOSP-factual, no package/method special-casing).

## Remaining blockers

- Compose host wiring: `Lr;.onAttachedToWindow` Handler-null (dooz +
  solitaire family). Requires the Handler/Looper lifecycle chain
  (U-003 law) — source-first wave, next.
- DECOR-LINKAGE (R-005) sub-decor attach — unchanged, queued.
- GL titles blocked by native `.so` loading — out of current scope.

## NEXT ACTION

Attack `Lr;.onAttachedToWindow pc=50 Handler.postAtFrontOfQueue
null-recv` (compose ViewTreeOwner chain): disassemble Lr; in
io.github.yamin8000.dooz + com.vayunmathur.games.solitaire, find the
Handler field producer, apply the SOURCE→LAW→PROBE→REAL-APK→REGRESSION
protocol, then rerun both titles + battery.
