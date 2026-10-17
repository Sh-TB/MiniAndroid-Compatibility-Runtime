# CONT-77 — #364 continuation: closure re-verified in a fresh container + F-NEW-380 ROOT-CAUSED-FIXED (RenderNode.beginRecording accumulate-amplification)

**Wave:** CONT-77 · **Date:** 2026-10-17 · **HEAD at start:** `fa97fdd1` (CONT-76, synced) · **Binary at end:** `fc12647ff1a7b13a` (deterministic rebuild verified) · **Baseline A/B binary:** `1ef983a6ff71dade` (CONT-76 record, rebuilt byte-identical in-container)

## 1. Fresh-container re-verification of the CONT-76 closure (all verdicts re-proven)

The local environment had reset to a pre-CONT-74 snapshot; recovered via `git fetch + reset --hard origin/main` (remote history intact: CONT-74 `aabf7bb9`, CONT-75 `ae558af8`, CONT-76 `fa97fdd1`; #364 comments `6234354571` + `6234924269` verified via API). Then every CONT-76 claim was re-executed in-container:

| Gate | Result |
|---|---|
| MG-310 clinit fence | **7/7 PASS** |
| MG-150 transform hit-test fence | **3/3 PASS** |
| c72priv privacy fence | **13/13 rows OK** (gate A probe rebuilt: libprobe `ad413625925ed8e5` == record; probe-prelude law respected) |
| negatives | **19/19 PASS** |
| reinstall matrix | **8/8 PASS** |
| user goldens | **4/4 PASS** (`helloworld` `83720c1028f832d0`) |

**The #364 closure verdicts stand as posted.**

## 2. The P0 lever advanced: dooz runtime facts at this HEAD (all runtime-proven)

- The frame pump **does re-arm** (`[F277-POLL]` parity), recomposition #2 **does re-invoke** the NavHost lambda with real backQueue entries (1024 `[F259-INS]` destination-insert rows), and the draw window **reaches real content** (`[C013-CUSTOMVIEW] onDraw replayed 926 ops` for AndroidComposeView).
- The presented face stays `31ddd4d5b8e6d18e` because the F-NEW-298 frame-honesty law **correctly** skips presentation of every budget-halted frame — the frame never completes inside 30s.

## 3. F-NEW-380 (NEW, ROOT-CAUSED-FIXED P0): beginRecording accumulate-amplification

**AOSP law:** `RecordingCanvas.beginRecording` — *"the previous recording is discarded"* — every record starts a **fresh display list**. The engine appended to the node's prior op list instead.

Runtime proof chain:
1. `[C77-RECORD] node=9348 prior_ops=1..9 growing within one frame` (re-record accumulation, direct evidence).
2. `MINIANDROID_CANVAS_OP_TRACE` pre-fix stream: **2471 ops with 1562 identical `New game` TEXT ops** at (765,1829.976) + 189 `Dooz` ops — **all from the single paint site `Lj7;.e`** (compose MultiParagraph; chain `Lj7.e ← Lj7.f ← Lwu0.i ← Lnt1.Q ← Lgl0.c`, stack depth 157–164; caller attribution via the extended S81 diag).
3. Mechanism: accumulate at beginRecording → `drawRenderNode` replay copies ever-growing lists per level → the compose draw burns the whole wall budget re-recording duplicate content → frame never completes → F-NEW-298 keeps the splash.
4. **Fix (generic):** `render_nodes_[recv].clear()` at `beginRecording`. Post-fix stream: **2477 ops, ZERO flood rows**. No app/R8-specific logic; re-recording is idempotent under any invalidation cadence.

## 4. F-NEW-381 (NEW, CLASSIFIED P1): the interpreter throughput wall — the honest residual

- dooz's first content composition is **~10–12M interpreted instructions**; the engine sustains **~310K ins/s** (PROGRESS linear scaling: 3.1M@10s / 6.2M@20s / 9.2M@30s; `--frames 1` consumes the same budget). opencalc (Compose, Kotlin+R8) completes its whole launch in **<100K instructions** — the 100× contrast is dooz's NavHost/destination materialization volume.
- The sampler profile (16.5K samples) is **FLAT** (top leaf 4.7%): the cost is architectural — `DalvikValue` carries **two `std::string` members (~112 B) in every tagged value**, so every register read/write copies them (~60–90M copies/run).
- Honest null: hoisting the two per-instruction `getenv` scans (~18M environ scans/run eliminated) measured **no gain** — kept as hygiene, recorded as a falsified quick fix.
- Fix surface: a DalvikValue register-file representation change (tagged-union fast path, strings out-of-band). Its own wave; full anchor battery required.

## 5. Regression at `fc12647ff1a7b13a` — zero drift

- **Wall 9/9 MATCH:** dooz `31ddd4d5b8e6d18e` ×3 + opencalc `f25b754c4565c38b` ×3 + unote `90a67cc1ddda57b7` ×3.
- chess `b270ff040b3601dc` + microtimer `bbd350b6c14fbd52`: **A/B byte-identical** vs the baseline binary `1ef983a6ff71dade` (their hashes differ only from pre-CONT-74-era records — zero drift from this wave).
- goldens 4/4 · negatives 19/19 · reinstall 8/8 · c72priv 13/13 · MG-310 7/7 · MG-150 3/3 · s82 validator rc=0.

## 6. Updated #364 scoreboard (the user's percentage question)

| Verdict | Count | Share |
|---|---|---|
| CONFIRMED (fixed + gates green, re-verified) | **5** (4 from CONT-76 + **F-NEW-380 this wave**) | **55.6%** |
| REJECTED_WITH_REASON (evidence-backed) | 3 | 33.3% |
| BLOCKED_NEEDS_EVIDENCE (architectural) | 1 | 11.1% |
| **Total terminal verdicts over the 9 tracked items** | **9** | **100%** |

Corpus face split (unchanged from CONT-76): 60% REAL_APP_CONTENT, 20% native-mismatch, 20% compose-family blanks — with the compose-family blocker now precisely split into F-NEW-380 (fixed) + F-NEW-381 (named architecture work) + the 4-op wrapper-unwrap residual (`RecordingCanvas.drawBitmap` bitmap-unresolved ×2, `Path.addRoundRect` RectF-unresolved, `clipPath` path-unresolved — pre-existing, recorded, untouched this wave).

**Registry:** 685 → 687 roots (F-NEW-380 ROOT-CAUSED-FIXED P0, F-NEW-381 CLASSIFIED P1), id-unique, canonical mirrored. **Evidence:** `evidence/cont77/cont77_evidence.json`. **Next wave owns:** F-NEW-381 register-file representation (or the wrapper-unwrap residual), then re-measure dooz inside the 30s budget.
