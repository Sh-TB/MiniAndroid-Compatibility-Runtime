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
ID. #632 itself carries only 3 comments (7034254502 = BATCH 2, 7034329407 =
BATCH 3, 7034373205 = BATCH 4 FINAL); the later batches (7034418989 …
7038547151) were harvested in earlier sessions from subsequent comment pages /
follow-up threads. This session did not re-verify which issue number hosts each
later comment ID (web calls timed out); the CSV's comment IDs are the
authoritative provenance either way. Batch highlights preserved in-tree:
BATCH 2 retracted six of its own P0 items after discovering TWO layout engines;
BATCH 3 proved `view_renderer.cpp`/`real_layout.cpp` are NOT COMPILED (40 claims
dead-code); BATCH 4 closed the audit with "the live engine is
MeasureSpec-compliant".

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

## Why this file exists

Sandbox recycles repeatedly restore the repo to an older checkout and wipe
context; in-conversation fetches do not survive. The bodies above were fetched
from `api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/N`
on 2026-11-21; future integration work should re-fetch any body it needs
verbatim — this digest is a map, not a substitute.
