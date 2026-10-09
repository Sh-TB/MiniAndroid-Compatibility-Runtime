# CONT-27 / REGRESSION MATRIX (Phase 4)

Binary: `6823170ebd443118` (HEAD `da92a9f6` + F-NEW-281/281b/281c +
F-NEW-282/282b + F-NEW-283; built with the foreground
`timeout 570 make -j1 BUILD_DIR=build` discipline). Harness:
`scripts/cont27_regression.sh` (rc captured immediately after each engine
call — CONT-22 rc-truth law). Raw logs: `run/cont27/regression/`.

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

**24/24 runs byte-identical.** The Surface/GL family (flappycow) and the
Canvas family (tttdeluxe, g2048) prove the skeleton-light destruction hazard
did NOT recur and the six law changes are semantically neutral where they
were never reachable — including the inflate-gate change (F-NEW-283), which
was exercised by no anchor's layout.

## Probe battery (DEX-law regression probes)

| probe | rows | PASS | FAIL | expected |
|---|---|---|---|---|
| fcol (collection laws) | 20 | 140 | 0 | 0 unexpected FAIL — PASS |
| f259 (iterator/enum laws) | 7 | 49 | 0 | PASS |
| f259g (extended iterator) | 13 | 84 | 7 | the SAME single known-honest F259-L row repeated — matches the recorded 12/13 drift — PASS |
| f266 (interface-default dispatch) | 6 | 42 | 0 | PASS |
| f268 (exception laws) | 12 | 96 | 0 | PASS |

## 3-run proofs for the wave's causal claims

| target | sha16 ×3 | rc ×3 | claim |
|---|---|---|---|
| Simple Calculator (Track B target) | 7960bce447ac6d8f | **0 ×3** | FIRST FULL SUCCESS — uncaught 2→0, Toolbar NPE family eliminated, app keypad rendered (F-NEW-283) |
| fnew253_probe (Track B positive control) | 7602563f52cce823 | recorded | real render + 147 PASS / 0 FAIL rows |
| dooz (Track A anchor) | d602648e8e401895 | 1 ×3 | F-277 post-fix state unchanged — composition #2 still starved (honest PARTIAL; this wave's Track A laws do not touch the scheduler) |
| oracle12 (Track A instrument) | 3359ed00e3add03d | 1 | draw-pipeline state stable at the final binary (GraphicsLayer ctor-skip face recorded) |

## rc-truth

Engine exit code is 0 ONLY on full SUCCESS (main.cpp law). Anchor runs showing
rc=1 (dooz, opencalc) match their recorded rc exactly — PARTIAL SUCCESS is the
honest verdict for both, unchanged from the frozen records. Simple Calculator
moves 1→0 under the SAME law — the wave's only rc change.

## Environment notes

- GitHub REST API: REACHABLE this session (issues #383/#384/#385 read via
  API — no rate limit encountered, unlike CONT-25/26).
- F-Droid archive: REACHABLE (simplecalc vc8/vc7/vc6 re-captured, SHAs exact).
- ARM-only native compatibility: not treated as a runtime blocker this wave
  (LAW-001 scope); all executed targets are x86/x86_64-compatible.
