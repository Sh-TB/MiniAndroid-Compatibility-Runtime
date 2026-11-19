# Dalvik split + dev-so development path — architecture, operation and rollback

Status: IMPLEMENTED / TESTED / PUSHED (wave-9 `1e5c8fb9`, wave-10 `f727991e`, integration evidence `96cd29e2`).

## Why the Dalvik split is required

Before the split the Dalvik VM lived in one translation unit (~96k lines of engine,
interpreter, bridge and opcode-table code). Every edit to any of them forced one
huge compile plus a full program relink, so an edit-to-test cycle cost minutes
regardless of how little code changed. The split carves the volatile Dalvik code
into 7 translation units (`dalvik_engine`, `dalvik_engine_invoke`, `dalvik_engine_core`,
`dalvik_engine_tail`, `dalvik_interpreter`, `dalvik_bridge`, `dalvik_opcodes` +
`dalvik_opcodes_invoke`, declared in `core_sources.manifest`) so make can rebuild
exactly the TU that changed. The stable runtime (activity lifecycle, views,
resources, graphics, storage) is untouched by this work and never recompiles.

## How the dev-so path works

`make dev-so` (opt-in) builds the 7 Dalvik TUs as PIC objects into
`build_dev_so/objects/` and links them into `build_dev_so/libminiandroid_dalvik.so`
(SONAME pinned, `$ORIGIN` rpath, make-escaped `$$ORIGIN`). The test executables and
`miniandroid_dev` keep the stable runtime + quickjs + thunk **static** and link the
Dalvik set **dynamically**, so an incremental cycle is: 1 PIC compile of the edited
TU + 1 `.so` relink — test executables are never relinked (`ldd` proves the loader
resolves the library from `build_dev_so/` via `$ORIGIN`; `test_core` records no
`NEEDED` entry because it has no Dalvik references by design).

Staleness safety: `dev-so-test` depends on the `.so`, which depends on every PIC
object; PIC objects carry `-MMD` dep files, so header edits rebuild correctly and a
missing or stale `.so` is always rebuilt **before** any test runs — a stale library
can never be silently loaded.

## Why the production default remains static

The production build (`make all`, default `DALVIK_SPLIT=1` static split) is
byte-for-byte independent of the dev path: `make -n all` references
`build_dev_so` zero times. Production per-TU optimization flags are unchanged
(interpreter `-O2` + wave-7 inline budget, bridge `-Og`); the dev-so PIC rules use
separate development profiles and never affect production objects. The monolith
fallback (`DALVIK_SPLIT=0`) is kept and live-verified. Deploy shape, parity and
performance of production binaries are therefore not exposed to dev-path
experiments.

## Accepted compiler profiles and limitations

Wave-10 profiles, dev-so path only, chosen from a measured 11-candidate sweep
(attribution: both TUs codegen-bound, `callgraph functions expansion` 63%/50%):

| TU | Wave-9 | Wave-10 | Edit-to-test (median) |
|---|---|---|---|
| dalvik_interpreter | `-O2` | **`-O1`** | 21.94 s → **12.16–12.26 s** (<15 gate MET) |
| dalvik_opcodes | `-O2` | **`-O1`** | 9.85 s → **8.08–8.18 s** (<10 gate MET) |
| dalvik_bridge | `-Og` | **`-O0`** | 40.98 s → **25.51–26.89 s** (<30 gate MET) |
| no-op | 0.05 s | **0.04 s** | — |

Limitations: bridge `-O1` is **blocked** — `cc1plus` is OOM-killed by the 4 GB
cgroup (measured, not assumed); dev-profile `.so` output is proven byte-identical
on the 3-APK parity set (3 reps × hashes identical), but the reduced-optimization
library is for development iteration only. Peak RSS ≤ 2,886 MB.

## How to run the tests

```
make all                # production static split (default), then: make test-core
make DALVIK_SPLIT=0 test-core   # monolith fallback build + battery
make dev-so             # opt-in shared-library dev build
make dev-so-test        # dev battery (rebuilds .so first if anything is stale)
make dev-so-clean       # rollback: removes build_dev_so entirely
```
Reproduction scripts: `scripts/w9_clean_verify.py`, `scripts/w9_bench.py`,
`scripts/w8_gate.py`, `scripts/w10_verify.py`, `scripts/w101_acceptance.py`.

## Measured edit-to-test timings and evidence

Full runs, medians and per-rep data: `evidence/wave9/w9_clean_results.json`,
`evidence/wave9/wave9_final_evidence.md`, `evidence/wave10/wave10_final_report.md`,
`evidence/wave10/w101_acceptance.json`. Clean dev-so build 122.7–148.5 s; test
battery `test_core` = 3 PASS in ~0.05 s on warm `.so`; no-op 0.04 s.

## Runtime classifications (preserved)

Guess `ru.zxalexis.ugaday_15` = **SUCCESS** (screenshot hash `87fe2676…` identical
to canonical); DiceRoller `tech.gaskell.diceroller_1_debug` = **PARTIAL**
(`46b07062…`); TicTacToe `com.itsfrz.tictactoe_5` = **PARTIAL** (`d55056a8…`).
Hashes are stable across reps and across dev-profile transitions; screenshots are
not claimed as interaction evidence for PARTIAL apps.

## Remaining limitations

- Bridge `-O1`/`-Og` dev profiles require more than the 4 GB cgroup allows.
- Dev `.so` trades optimization for iteration speed; production keeps `-O2`.
- PR #626 (wave-10) integration into `main` waits on the PR retarget gate
  (base change requires pull-request write that the automation token lacks).
