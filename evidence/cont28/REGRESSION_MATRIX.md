# CONT-28 / REGRESSION MATRIX (Phase 4)

Binary: `miniandroid/build/miniandroid` at HEAD `9c42dd61` + F-NEW-284
(super-dispatch proto) + F-NEW-285 (RenderNode claim gate) + the two generic
diagnostics (MINIANDROID_OVERLOAD_TRACE, MINIANDROID_ALLOC_TRACE). Built with
the foreground `timeout 570 make -j1 BUILD_DIR=build` discipline. Baseline
binary reproduced byte-exact `6823170ebd443118` before any patch. Harness:
`scripts/cont28_regression.sh` + `cont28_resume.sh` (rc captured immediately
after each engine call — CONT-22 rc-truth law). Raw logs:
`run/cont28/regression/`.

## Anchor + control suite (byte-exact expectations)

| target | family | expected sha16 | r1 | r2 | r3 | verdict |
|---|---|---|---|---|---|---|
| dooz (io.github.yamin8000.dooz 23) | Compose | d602648e8e401895 | MATCH | MATCH | MATCH | PASS |
| microtimer (dubrowgn.microtimer 8) | View | da73010a37dd0189 | MATCH | MATCH | MATCH | PASS |
| unote (app.varlorg.unote 30) | View | 4f1a9e4e8f64fae8 | MATCH | MATCH | MATCH | PASS |
| gmdice (de.duenndns.gmdice 8) | View game | f3b483fe7b7cf51b | MATCH | MATCH | MATCH | PASS |
| opencalc (com.darkempire78.opencalculator 53) | View (Kotlin+R8) | a976d2f9fb675cb3 | MATCH | MATCH | MATCH | PASS |
| tictactoedeluxe (com.miniandroid.tictactoedeluxe) | Canvas | af6094295ecb50e3 | MATCH | MATCH | MATCH | PASS |
| flappycow (rebuilt) | Surface/GL | 13cf47464d9787f4 | MATCH | MATCH | MATCH | PASS |
| g2048 (com.miniandroid.g2048) | Canvas | 59ca1526611c4622 | MATCH | MATCH | MATCH | PASS |

**24/24 runs byte-identical ×3.** The Surface/GL family (flappycow) and the
Canvas family (tttdeluxe, g2048) prove neither new law touched the
non-Compose pipelines; dooz (the F-277 byte-anchored Compose target) is
unchanged at its recorded PARTIAL state.

## Probe battery (DEX-law regression probes)

| probe | rows | PASS | FAIL | expected | verdict |
|---|---|---|---|---|---|
| fcol (collection laws) | 20 | 140 | 0 | 0 unexpected FAIL | PASS |
| f259 (iterator/enum laws) | 7 | 49 | 0 | PASS | PASS |
| f259g (extended iterator) | 13 | 84 | 7 | the SAME single known-honest F259-L row | PASS |
| f266 (interface-default dispatch) | 6 | 42 | 0 | PASS | PASS |
| f268 (exception laws) | 12 | 96 | 0 | PASS | PASS |

All five probe counts EXACTLY equal the CONT-27 recorded numbers.

## 3-run proofs for the wave's causal claims

| target | sha16 ×3 | rc ×3 | claim |
|---|---|---|---|
| oracle12 (Track A instrument) | b270ff040b3601dc | 1 ×3 | post-F-NEW-284/285 state: exception-free draw pipeline (crash.log 0 errors), frame = the app's own theme surface `fef7ff`; rc=1 is the honest frame-truth verdict (DEFAULT_BACKGROUND_ONLY — compositing divergence named, evidence §5) |
| Simple Calculator (Track B target) | 7960bce447ac6d8f | **0 ×3** | FULL SUCCESS retained — Status: SUCCESS ✅ ×3, the app's own keypad rendered |
| dooz (Track A anchor) | d602648e8e401895 | 1 ×3 | F-277 post-fix state unchanged — byte-anchored |

## rc-truth

Engine exit code is 0 ONLY on full SUCCESS (main.cpp law). Anchor runs
showing rc=1 (dooz, opencalc) match their recorded rc exactly — PARTIAL
SUCCESS is the honest verdict for both, unchanged from the frozen records.
The oracle's rc=1 likewise reflects the frame-truth gate, not a crash (zero
uncaught exceptions). No recorded rc changed this wave.

## Environment notes

- F-Droid archive: REACHABLE (simplecalc vc8 re-captured, sha16
  `68da25fd9fdf54b4` EXACT — byte-identity of the Track B target re-locked).
- oracle12.apk rebuilt size-exact 8,233,173 bytes (sha16 `f2790da666890def`,
  honest non-byte-identical across rebuilds — identity = size + id-table +
  behavior parity; the recorded face reproduced at the recorded pc).
- The local container had lost 49 commits (previous waves' work lived on the
  remote); Phase 0 fast-forwarded to `9c42dd61` == origin/main before any
  work — recorded as the wave's truth-lock first line.
- New run artifacts: `run/cont28/*` (A1 reproduction, traces, fix1/fix2,
  regression).
