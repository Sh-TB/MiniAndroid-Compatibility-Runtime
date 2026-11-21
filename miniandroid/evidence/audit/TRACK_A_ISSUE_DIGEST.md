# TRACK A — Issue-body digest & batch-source map (S7b + S3 closure)

Fetched 2026-11-21 via the GitHub REST API during the sandbox-down web-recon turns.
Purpose: durably persist the app-acceptance issue bodies gathered for the
integration ledger, and close Track A S3 by recording where every
`632_FINDINGS.csv` batch_source lives. Nothing here replaces the CSV — it is the
pointers + summaries behind it.

## S3 closure — batch-source map for 632_FINDINGS.csv (234 rows)

`batch_source` distribution (awk over the committed CSV at a88101e7):

| batch_source | rows |
|---|---|
| body (issue #632 itself) | 140 |
| comment 7038195837 | 18 |
| comment 7037681554 | 17 |
| comment 7034483805 | 13 |
| comment 7038515790 | 8 |
| comment 7034329407 (BATCH 3) | 7 |
| comment 7038547151 | 6 |
| comment 7038248330 | 6 |
| comment 7034418989 | 6 |
| comment 7034254502 (BATCH 2) | 6 |
| comment 7034373205 (BATCH 4 — FINAL) | 4 |
| comment 7034447952 | 3 |

The stale hunt for "#632 batches 5-11 via pagination" is closed: the registry
already holds 234 rows ≥ the 194-item target, with per-row provenance by comment
ID. **Parentage resolved 2026-11-21 via the authenticated API** (token read at
runtime from git credential, never stored): ALL 11 comment IDs are comments on
**#632 itself** — the earlier "3 comments" reading was a WebFetch line-window
truncation artifact, now corrected. The full batch stream on #632:

| comment ID | BATCH label (first heading, abridged) | CSV rows |
|---|---|---|
| 7034254502 | BATCH 2 — two layout engines; six own P0 items retracted | 6 |
| 7034329407 | BATCH 3 — view_renderer/real_layout NOT COMPILED | 7 |
| 7034373205 | BATCH 4 — live engine faithful AOSP port; NEW-11/12 falsified | 4 |
| 7034418989 | BATCH 5 — text pipeline; P0 Persian/Arabic shaping-order defect | 6 |
| 7034447952 | BATCH 6 — resource system faithful + style-value heuristic | 3 |
| 7034483805 | BATCH 7 — NEW-14 CONFIRMED: CENTER/CROP drawn with no clip | 13 |
| 7037681554 | BATCH 8 — sweep S2: 174 XML attributes silently dropped | 17 |
| 7038195837 | BATCH B1 — build performance, 18 new findings | 18 |
| 7038248330 | BATCH B2 — CMake `all` links 52 executables | 6 |
| 7038515790 | BATCH 10 — SQLite law mapped + 8 verified defects | 8 |
| 7038547151 | BATCH 11 — subsystem reuse registry (~600 KB) | 6 |

Batch highlights preserved in-tree:
BATCH 2 retracted six of its own P0 items after discovering TWO layout engines;
BATCH 3 proved `view_renderer.cpp`/`real_layout.cpp` are NOT COMPILED (40 claims
dead-code); BATCH 4 closed the live-engine question — so the S18 D/E law
families must target the LIVE inflater path, not the D/E rows' cited
view_renderer.cpp lines (dead file).

## App-acceptance / engineering issue bodies (S7b, 13 fetched)

| # | Title (abridged) | State | Key facts worth keeping |
|---|---|---|---|
| 296 | [MG-007] Vector path strokeLineJoin — resource/asset | open | PARTIAL; upstream VectorDrawable.java (VPath); 4-step fix protocol: real aapt2/ECJ/D8 APK fixture → implement-or-fence vs AOSP law → named battery stage, 99-stage battery ALL PASS → close with commit SHA + before/after |
| 297 | [MG-008] Vector path trimPath — resource/asset | open | PARTIAL; same protocol, same upstream file |
| 597 | [W27][Coder-4] the "777" root-caused & fixed | open | Root cause: `StringBuilder.append(CharSequence,int,int)` had NO bounded arm — generic append stringified the whole sequence, so `replace()` rebuilds tripled one tap → "777". Fix = law F-NEW-639; one tap = one digit; full 4-tap dispatch battery; 6-pin gate (5 HOLD + microtimer SHIFT). Forensics: ONE logical `v0/r` run, 3 state-machine entries, regex matched once, body read the EMPTY display ×2 |
| 618 | Counter app — one Activity, two XML onClick buttons | closed (completed) | Acceptance complete; package split correction `myfirstapplication`/`couterapp` |
| 628 | kotlinx-coroutines Dispatchers.IO in the engine | open | Knowledge-transfer: F-NEW-XXX-9 in `execution_engine.cpp`; parked-worker starvation; spurious-wakeup resume law; HOSTBIND2; remaining frontier: window ref → FragmentNavigator → FCV paint |
| 614 | Guess 0.15 (`ru.zxalexis.ugaday`) | open | Single-Activity number-guessing; binary-search ≤7 guesses acceptance |
| 610 | n-Puzzle 1.1 | open | Correction: ImageSelection is MANDATORY at start, default grid 4×4 |
| 621 | Rock Paper Scissors (`com.setharvila.rockpaperscissors`) | open | ImageButton ×3 + reset; Random.nextInt(3); six image assets; MainActivity blob `20c9fbde…`; AppCompat 1.2.0/Material 1.3.0/ConstraintLayout 2.0.4 |
| 622 | Classic Calculator (`ng.com.techsoft.calculator`) | open | exp4j 0.4.4; EditText input_box; mandatory MainActivity source audit before implementation; blob `a5a4829f…` |
| 624 | Coin Toss (`com.dhairya.cointoss`) | open | One Button → `r.nextInt(2)` → heads/tails PNG + Toast + RotateAnimation 0→360, 1000 ms; blob `0b09c5ad…` |
| 623 | Random Number Generator (`com.example.test`) | closed | EditText bound + `rand.nextInt(bound)+1` inclusive [1,bound]; invalid input message path |
| 626 | ISSUE-612: WAVE-10 dev-so speed profiles (PR 2 of stacked series) | open | Dev profiles: interpreter/opcode `-O1`, bridge `-O0` (4 GB host memory bound). Wave-10.1 acceptance: clean dev-so 122.7 s, battery 3/3; incremental: no-op 0.04 s, interpreter 12.16 s, bridge 26.89 s, opcode 8.08 s — one PIC compile + one relink, zero test relinks; `$ORIGIN` resolution verified. Base = wave9 branch; merge #625 first, retarget after |
| 612 | P0 BUILD PERFORMANCE task book | open | Measured-baseline discipline: record host/cgroup limits every benchmark; no speed claim without clean+incremental; CMake PRE_LINK missing-source defect documented; 300 s harness window kills single-job Release at ~7% on `dex_interpreter_batch.cpp` |

## S3 — mission + vector-domain issue bodies (fetched 2026-11-21, authenticated API, `scripts/s3_fetch_issue_bodies.py`)

| # | Title (abridged) | State | Key facts worth keeping |
|---|---|---|---|
| 635 | MASTER CROSS-CODER ACHIEVEMENT AUDIT — 50-claim item-by-item verification ledger | open | Independent audit from HEAD `d8b8fbb9` + audit commit `9b953ce1`; host 2 vCPU / 4 GB, hypervisor steal 24-25% of every build window; cmake ABSENT (CMake graph measurements BLOCKED, not skipped); 300 issues+PRs fetched, every mission-referenced issue exists. §1.A dispositions that settle #632 census rows: B1/B2 CMake-battery CONFIRMED; B3 ccache CONFIRMED (cold 553.42 s / 0 hits, warm 20.94 s / 88-88); B4 mold/lld REJECTED (link 1.5 s of 350 s); B5 gsplit-dwarf REJECTED-MEASURED (+4% on heaviest TU, ABBA probe); B6 ggc-min REJECTED-MEASURED (3× slower — GC thrash); B7 -fno-var-tracking-assignments REJECTED-MEASURED (no win; GCC14 fixed VTA; -g1 already covers); B8 .DELETE_ON_ERROR CONFIRMED-missing → **FIXED in this audit** (in-tree, verified by grep today); Make-path peak RSS 1221 MB / 4 GB across ~40 full builds (OOM NOT observed — bounds the -j co-scheduling risk); layout path = `layout_inflater.cpp` verified; NEW-9 guard CONFIRMED (retraction justified) |
| 633 | [MG-009] vector pathData parse failure — aapt2 string refs unreachable through VectorRefResolver | open | Coder claims root-caused + fixed LOCALLY, **commit blocked from pushing**; upstream law: `android.util.PathParser` + aapt2 resource-table inlining; domain resource/asset — integration candidate pending actual patch delivery (same class as MG-007/MG-008) |
| 634 | [MG-012] animated-vector decodes to nothing; drawable references never resolve to a document | open | Same "fixed locally, push blocked" status; TWO defects — AVD rejection outright + a shared-layer drawable-reference resolution bug "far wider than animated vectors"; upstream: `AnimatedVectorDrawable.getConstantState()`, `VectorDrawable.draw()` — integration candidate pending patch delivery |

The #635 §1 dispositions are external measured evidence: this session settles #632
rows B6/B7/B8/B9 by cross-referencing them (see the S18-CONT-2 registry stamps),
and A2-A8 by re-measurement (`RAW_LOGS/s18_a_census_2026-11-21.log`).

## Why this file exists

Sandbox recycles repeatedly restore the repo to an older checkout and wipe
context; in-conversation fetches do not survive. The bodies above were fetched
from `api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/N`
on 2026-11-21; future integration work should re-fetch any body it needs
verbatim — this digest is a map, not a substitute.
