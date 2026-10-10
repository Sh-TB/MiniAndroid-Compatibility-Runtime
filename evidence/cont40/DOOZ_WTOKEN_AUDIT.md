# CONT-40 — Independent Audit: the friend's Dooz "getWindowToken" claim and the Recomposer frontier

**Binary (audit)**: prototype `feaf224d48c9b229` (with the getWindowToken law) / A/B base
**Binary (shipped)**: `111340a583d48d92` (byte-exact CONT-39 record — the law PARKED, see §6)
**Target**: `io.github.yamin8000.dooz_23.apk` SHA-256 `299eab21ac8b3c6192edbd887966554fef84ad026d269b9067310215201b362b`
**Launch**: `miniandroid run <apk> --width 1080 --height 1920 --frames 5 --max-seconds 15` (extended probe: `--frames 8 --max-seconds 45`)

## 1. Registry reconciliation (friend's labels)

F-NEW-253..259 are OCCUPIED in this lineage by unrelated roots (SaveableStateRegistry
parcel fidelity, kotlinx exception-chain edges, List.listIterator null, the Compose
real-content frontier refinement, Bundle parcel-family fidelity, instance-of STRING_REF,
DEX-list iterator protocol). F-NEW-260/261 are absent. Per the standing directive the
friend's numbers were DISCARDED; the claims were verified BY CONTENT against the real
(R8-renamed) DEX: `Lr;` = AbstractComposeView, `Le81;`/`Lho;` = its subclasses (ComposeView
family), `Lt4;` = AndroidComposeView, `Lh9;`/`Lj9;` = the AndroidUiDispatcher/FrameClock
callback family (F-050), `Ldo1;`/`Lwo1;` = IME-hide helpers.

## 2. Static decode (scripts/cont40_decode*.py — field-ref-exact)

- `getWindowToken` call sites: 3 (`Ldo1;->e`, `Lr;->c`, `Lwo1;->e`).
- `Lr;->c` (attach): `isAttachedToWindow` → `getWindowToken()` → **stored RAW** via
  `setPreviousAttachedWindowToken` — **NO null-gate**; then the child-context propagation;
  then `getShouldCreateCompositionOnAttachedToWindow()` = **CONSTANT TRUE** → `g()`.
- `Lr;->g` (ensureCompositionCreated): no token check; creates the composition via
  `La72;.a` → new `Lt4;` + `Lx62;` → **`x62.f(content)` runs unconditionally**.
- The token field `Lr;->f` has exactly ONE reader: its own setter's equality pre-check
  (write-only bookkeeping). The setter clears the `Lr;->e` WeakReference **only when the
  token CHANGES** (the androidx window-migration law; `e` = the windowRecomposer cache,
  read by `Lr;->k`).
- `Lr;->onAttachedToWindow`: the real gate is the PARENT WALK — if the climbed root's
  `getParent()==null` → defer via `Handler.postAtFrontOfQueue(new Lp;(this))`; else `c()`.

**Static conclusion: a null token cannot gate composition creation in this DEX.**

## 3. Runtime verification (Phase 2/3)

Baseline ×3 + extended ×1 on the pre-law binary (fresh runs, this HEAD):

- The getWindowToken call FIRES on the real path: `[WTOKEN] view_id=1123 class=Lho;
  attached=1 parent_node=44` — exactly once per run, inside the deferred `Lp;` Runnable
  (the onAttachedToWindow defer path executes and reaches `c()`).
- Frame clock: registrations `[CHOREO] postFrameCallback cb=1180 class=Lh9;` (+ `Lj9;`),
  the dispatcher's handler-side win removes the entry (`[S34-RFC]`), **2 doFrame
  deliveries** at strictly monotonic virtual vsyncs (1016666667 → 1033333334 ns) — the
  recomposer's continuation RESUMES and executes **14.3 MILLION instructions** (45 s
  budget also exhausted: the same face at 4.5M+ instructions/15 s).
- The budget halts land mid-draw (`F084`); the frame-honesty law keeps the last complete
  frame → the honest keep-empty white `31ddd4d5b8e6d18e` (verdict DEFAULT_BACKGROUND_ONLY,
  first_missing_stage=APP_DRAW_OPS; first render carried **151 real app-owned draw ops**).

A–F classification (the directive's taxonomy):

| Case | Verdict | Evidence |
|---|---|---|
| A no frame clock | REJECTED | F-050 virtual clock; deliveries logged |
| B callback never registered | REJECTED | `[CHOREO] postFrameCallback` lines |
| C registered never delivered | REJECTED | 2× `[CHOREO-DISPATCH] doFrame … invoked` |
| D delivered, coroutine not resumed | REJECTED | 14.3M instructions executed post-resume |
| E resumes but exceeds the execution budget | **VERIFIED — the real frontier** | F084 halts at 15 s AND 45 s; 151 ops painted mid-draw |
| F completes but layout/draw/presentation fails | REJECTED (subordinate) | the composition never completes within budget |

## 4. The prototype law and the A/B (same binary `feaf224d48c9b229`)

The AOSP-faithful law (attached → one window-stable `Landroid/os/IBinder;` singleton,
detached → null) was prototyped with env-gated trace + a `MINIANDROID_WTOKEN_NULL`
audit mode:

| Run | Mode | Frame | Content |
|---|---|---|---|
| dooz ×3 | token | `d602648e8e401895` ×3 | (250,250,250) full-screen — theme background, 0 ops every frame |
| dooz ×1 | forced null | `31ddd4d5b8e6d18e` | the honest keep-white, 151-op inline compose path |
| csw ×3 | token | `5c4a0172628849ba` ×3 | **SINGLE color (23,25,31) — the visible text LOST** |
| csw ×1 | forced null | `3442d9a9dc0fa0f9` | the recorded frame byte-exact (text visible) |

Mechanism (log-diff proven): the token's non-null answer clears the `Lr;->e` recomposer
cache at first attach; combined with the heap-oid shift from the IBinder allocation, the
app's identity-hash ordering changes and the compose machinery takes a DIFFERENT VALID
interleaving (StateFlow spin + inline compose vs the `Lrz1;.j` cycle-stub + NPE-recovery
path) — the inline compose short-circuits and the frame completes EMPTY. The composition
was never "prevented" in either mode (creation happens both ways).

## 5. The probe (fixtures/fnew302_probe, com.probe.fclk — standing battery)

9 generic rows, real toolchain: FC-01 Choreographer identity; FC-02 first delivery at the
virtual base quantum; FC-03 the RE-REGISTRATION LOOP (3 deliveries, exact 16666667 ns
quanta); FC-04 cross-frame state mutation; FC-05a/b/c/d the window-token contract
(pre-attach null / post-attach non-null / identity-stable / one-per-window); FC-06
cancellation; FC-07 the visible render control.

- WITH the law: **9/9 ×3**, byte-stable `79ae50ff59468c1a`.
- WITHOUT the law (shipped binary): **6/9** (FC-05b/c/d = the parked-law face, documented;
  FC-01..04+06+05a all PASS — the frame-clock loop is fully proven).

## 6. Verdicts and the parked law

1. `getWindowToken()` null on the failing path — **VERIFIED** (pre-law observation: no law
   existed; the call fires on the real path; typed-default null).
2. That null prevents composition creation — **REJECTED** (DEX: zero null-gates; runtime:
   creation + content compose happen both ways).
3. A token fix restores composition creation — **REJECTED** (nothing to restore).
4. The coroutine waits for MonotonicFrameClock — **REJECTED for the failing path** (case E:
   it resumes and burns the budget; the clock delivered twice).
5. The precise missing transition — **VERIFIED**: first-composition completion within the
   execution budget (case E).
6. Composition resumes and creates a non-empty LayoutNode tree — **VERIFIED for the
   pre-presentation stage** (151 app-owned ops reached the draw); **the frame never
   completes** (budget).
7. Dooz produces a completed meaningful frame — **NOT YET** (honest empty frame).
8. Three-fresh-run reproduction — **VERIFIED** (every result ×3 deterministic).
9. Independent Compose target — composeStopwatch retained its content frame
   (`3442d9a9dc0fa0f9` ×3) on the shipped binary; **its visible text was LOST under the
   prototype law** (`5c4a0172628849ba`, causality proven via forced-null on the same
   binary) — the reason the law is parked, not shipped.
10. Golden/negative-control regressions — **NONE on the shipped binary** (anchors 8/8 ×3
    byte-identical; battery == CONT-28..39 records exactly; simplecalc ×3 rc=0).

**The law is PARKED, not shipped**: it fixes a non-problem (claim 2 REJECTED) and its
heap-oid butterfly regresses composeStopwatch's visible content. The exposed frontier
(the compose-scheduling interleaving's identity-hash sensitivity + the fresh-recomposer
drain path) is the recorded next root candidate — it needs its own decode + probe wave.

**Next actions**: (a) root-cause the identity-hash interleaving sensitivity (the
`Lrz1` cycle-stub vs StateFlow-spin divergence) with a discriminating probe before any
engine change; (b) the dooz boot-cost root (case E) — the 14.3M-instruction first
composition — remains the standing frontier.
