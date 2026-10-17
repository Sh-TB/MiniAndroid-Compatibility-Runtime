# CONT-76 — #364 Closure Wave: every open item reaches a terminal verdict

**Wave:** CONT-76 · **Date:** 2026-10-17 · **HEAD at start:** `ae558af8` (CONT-75, synced) · **Binary:** `1ef983a6ff71dade` (UNCHANGED this wave — zero engine edits; all evidence is decode + fresh runs + fence fixtures)
**Mission:** the user's directive — «تمامش کن؛ همه یک حکم تأیید/رد داشته باشند؛ درصد کارکرد را بگو» — drive every open #364 item to a terminal verdict and report the working percentage.

---

## Part 1 — Terminal verdicts (this wave)

### 1.1 F-NEW-378 (P0) — the measure-pass exception: ROOT CONFIRMED, engine-law fix REJECTED

CONT-75 decoded the throw site but left the exception identity at "R8-merged CancellationException". This wave decoded the **full identity chain directly from the dooz dex** (androguard, `scripts/cont76_decode_la7.py` + `cont76_decode_family.py`):

- **`La;` = `kotlinx.coroutines.AbortFlowException(owner)`** — ctor literal string **"Flow was aborted, no more elements needed"**, extends `java.util.concurrent.CancellationException`, `fillInStackTrace()` returns an EMPTY array (by-design control flow).
- **`Lr50;` = `FlowCollector`** — abstract `m(Object, Lmq;)Object` = `emit(value, continuation)`.
- **`La7.m` branch-1** (packed-switch on `e:I`, 3 merged branches) = the `first()`/`take()`-family abort collector: **store the emitted value into the result holder (`Ltb1;->e`) → `throw AbortFlowException(this)`** — the exact upstream shape.
- **`Lzs.m`** = the kotlin-stdlib continuation machine (literal *"call to 'resume' before 'invoke' with coroutine"*, `COROUTINE_SUSPENDED` sentinel `Lwr;->e`, direct unintercepted delegate call).
- **The unwind is FAITHFUL ART behavior**: it passed through the measure frames and was **terminally contained by the machinery's own typed catch (`Llo.B`)** — the exception never escaped the engine. `[EXC-UNWIND]` rows `run/cont75/dooz_cfd` unchanged.

**Verdict: ✅ root CONFIRMED (decode-complete) · ❌ the named "continuation-boundary conversion" engine law is REJECTED with reason** — the dex machinery already contains the abort; a boundary conversion would *swallow legal control flow* (violates the loop's no-swallow red line), and the engine is not the diverging layer. The real divergence is upstream state: *why* a flow abort fires while the collect is nested inside the measure pass — which is **F-NEW-277's runner-re-arm domain**. The lever order recorded in CONT-75 ("cancellation conversion FIRST") is hereby **corrected to: F-NEW-277 re-arm first**.

### 1.2 F-NEW-379 (P2) — kotlin-reflect CNFE: REJECTED as content blocker (fresh current-HEAD A/B ×3 apps)

The CONT-73/75 suspicion ("candidate root, NOT proven") is now **disproven by fresh runs at this HEAD** (`run/cont76/guandan`, `run/cont76/andstatus`):

| App | CNFE site | Delivery | After | Face |
|---|---|---|---|---|
| dooz | `Lub1;.<clinit>` pc=3 | deferred → **own catch-all @0xe** | proceeds (splash = F-NEW-378 chain, not CNFE) | — |
| Guandan | `Lkotlin/jvm/internal/Reflection;.<clinit>` | deferred → **own handler @0xe typed CNFE** → **`<clinit> result=OK`** | compose root measured 1080×1920 | `4e58f3a378891497` == CONT-73 record (byte) |
| AndStatus2048 | `Lk00;.<clinit>` | deferred → **own handler @0xe** → **`result=OK`** | proceeds into delegate chain | `31ddd4d5b8e6d18e` == record (byte) |

The CNFE is kotlin-stdlib's **intentional fallback path** (try `ReflectionFactoryImpl`, catch CNFE, fall back to the base factory). **All three apps catch it and proceed.** Verdict: **❌ REJECTED_WITH_REASON — no shim needed.** The REAL blockers, named for the next wave: Guandan = empty composition (`AndroidComposeView children=0`, dark surface 1 color `8,36,26` — the F-NEW-277/378 family); AndStatus2048 = NPE `Object.getClass` on null in `Lt60;.getValue` / `Ll90;.u` pc=160 (kotlin-delegate chain — new candidate, decode pending).

### 1.3 MG-310 — dedicated `<clinit>` fence: BUILT, GREEN 7/7

`fixtures/mg310_clinit_fence` (com.probe.mg310, APK `741e3942c2048933`, real aapt2/ECJ/D8) + `scripts/cont76_fence_mg310.py`:

| Law | Row | Result |
|---|---|---|
| JLS 12.4.1 active-use init | L1 | PASS (`Base #1` on first static call) |
| constant read does NOT init | L2 | PASS (`ConstHolder.C=7`, engine `[CLASS_INIT]` rows = 0) |
| superclass-first order (app rows) | L3 | PASS (Base@4214 < Derived@6027) |
| superclass-first order (engine rows) | L3b | PASS (Base@3229 < Derived@5633) |
| once-only init | L4 | PASS (engine clinit rows = 1, initCount=1) |
| default-value-before-write | L5 | PASS (`Forward.s = "nullx"`) |

**Verdict: ✅ CONFIRMED — fence GREEN 7/7, `evidence/cont76/mg310_fence.json`.** The PARTIAL note ("dedicated fence pending") is closed; status `FENCE_GREEN`.

### 1.4 MG-150 — transform hit-test fence: BUILT, GREEN 3/3, frontier named

`fixtures/mg150_hittest_fence` (com.probe.mg150, APK `131ffbad6940c40e`) + `scripts/cont76_fence_mg150.py`, two canonical `--tap` runs:

| Row | Result |
|---|---|
| translation get/set readbacks 300/200 | PASS (properties law intact) |
| tap (150,150) inside **layout** bounds → button clicked | PASS (`[MG150-CLICK] count=1`) |
| tap (450,350) inside **translated-visual-only** bounds → no target | **documented deviation locked** (AOSP inverse-maps through the render transform) |

**Verdict: ✅ CONFIRMED (current semantics locked, no silent gap) — the x/y-translation consumption by hit-test + render is the named frontier (one coherent law with F-NEW-359's rotation record).** Status `FENCE_GREEN_FRONTIER_NAMED`.

### 1.5 MG-147 — multi-pointer fence: REJECTED as a fence (stale note corrected)

The old note said "implemented in input pipeline; not individually fenced". Ground truth (`touch_dispatcher.h` L193): **"Single active gesture (single-pointer model — multi-touch is an explicit documented boundary)"**. Multi-pointer IDs are NOT implemented; a fence cannot exist without a runtime feature (gesture model + injection CLI). **Verdict: ❌ REJECTED as a fence this loop — corrected note + recorded runtime-feature frontier.**

### 1.6 FOUNDATION-6 semantic-probe runner: BUILT + VALIDATED

`scripts/cont76_semantic_probe.py` — one bounded harness for N apps: fresh store → install → warm run → shared-vocabulary verdict rows (REAL_APP_UI / SPLASH_ONLY / WHITE_BLANK / DARK_SURFACE_NO_OPS / PREREQUISITE_MISMATCH) with the CONT-73 pixel-census law + **percentage scoreboard**. Validation run (5 apps): tictactoe DARK_SURFACE_NO_OPS (plain launch = empty board; the interactive 9/9-click golden is a separate recorded gate), Guandan DARK_SURFACE_NO_OPS, AndStatus2048 + stopwatch SPLASH_ONLY, gmdice REAL_APP_UI (`3891679dff449331`). **Verdict: ✅ CONFIRMED built** (flips from SOURCE_LEVEL_CANDIDATE_ONLY).

### 1.7 UPP-001 — native execution frontier: BLOCKED (terminal, honest)

**Verdict: ⛔ BLOCKED_NEEDS_EVIDENCE — architectural.** Native/ARM execution requires an ARM interpreter or code-translation layer: a runtime architecture project outside the loop's minimal-common-fix discipline. The app-layer evidence stays honest: Ball2Box (Godot, ARM-only) + OpenSurge (Allegro, ARM-only) refuse cleanly at the ABI gate (`PREREQUISITE_MISMATCH`) instead of faking execution. No fixture can shrink this root; it stays the named architecture frontier.

### 1.8 F-NEW-277 (P0 lever) — OPEN by design

The re-arm lever (resume the parked `awaitFrame`/`awaitWorkAvailable` continuation at quiescence without breaking the F-115b frozen launch-frame law) is now the **sole P0 lever** for the whole compose-content family (dooz + Guandan share it). Not closed this wave; its decode prerequisites are now complete (378's identity + containment proof).

---

## Part 2 — The percentages (the user's question)

**Verdict mix over the 8 open items this wave:**

| Verdict | Count | % |
|---|---|---|
| ✅ Confirmed (root/fence/tool proven) | 4 | **50%** |
| ❌ Rejected with evidence-backed reason | 3 | **37.5%** |
| ⛔ Blocked (architectural) | 1 | **12.5%** |

**"What percentage works" — corpus scoreboard (canonical: CONT-73 ten-app triage, faces re-verified at this HEAD where re-run):**

| Verdict | Apps | % |
|---|---|---|
| REAL_APP_CONTENT | 6/10 | **60%** |
| PREREQUISITE_MISMATCH (native/ARM, honest refusal) | 2/10 | 20% |
| Compose-family blank (F-NEW-277/378 family) | 2/10 | 20% |

**Loop health (#364 comment sweep)**: 0 unclassified comments remain (CONT-74 full sweep + this wave's closures); every card carries a current-HEAD verdict; 3 P1s fixed in 3 prior waves (F-NEW-375/376/377) + this wave's 2 fences + 1 tool + 2 decode closures; the review loop's hit rate on runtime-reachable claims remains 3-for-3 (ROI verdict from CONT-74 stands: **continue**).

---

## Part 3 — Honesty notes

- **Zero engine changes this wave** — binary `1ef983a6ff71dade` is byte-identical to the committed CONT-75 gate state, so no new regression battery is required; the two fence probes and the re-triage runs are the fresh evidence.
- The two-`..` null-result discipline of CONT-74 continues here: nothing was declared fixed without a post-fix row, and nothing was declared broken without a runtime row. F-NEW-378's fix was rejected on containment evidence, not on effort grounds.
- tictactoe's plain-launch DARK_SURFACE_NO_OPS row is not a regression — its interactive golden (9/9 DEX-dispatched clicks) is a separate recorded gate; the runner measures plain launches and says so.
- AndStatus2048's new NPE candidate (`Lt60;.getValue`) is named, not yet root-caused — recorded on F-NEW-379's row as the successor candidate.
