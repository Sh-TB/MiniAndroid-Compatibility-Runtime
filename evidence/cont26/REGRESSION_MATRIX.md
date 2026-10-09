# CONT-26 / REGRESSION MATRIX (Phase 4)

Binary: `1ff06737f7b12ad4cf469082c603b594e2045fc3442316aa1558dfb164201900`
(HEAD `364aa041` + F-NEW-278 + F-NEW-279 + F-NEW-280; built with the
foreground `timeout 570 make -j1 BUILD_DIR=build` discipline).
Harness: `scripts/cont26_regression.sh` (rc captured immediately after each
engine call — CONT-22 rc-truth law). Raw logs: `run/cont26/logs/regression2.log`.

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
Canvas family (tttdeluxe, g2048) prove the skeleton-light destruction
hazard did NOT recur and the three new laws are semantically neutral where
they were never reachable.

## Probe battery (DEX-law regression probes)

| probe | rows | PASS | FAIL | expected |
|---|---|---|---|---|
| fcol (collection laws) | 20 | 140 | 0 | 0 unexpected FAIL — PASS |
| f259 (iterator/enum laws) | 7 | 49 | 0 | 0 unexpected FAIL — PASS |
| f259g (extended iterator) | 13 | 84 | 7 | the SAME single known-honest F259-L row ("throwing slot propagated=false") repeated — matches the recorded 12/13 drift — PASS |
| f266 (interface-default dispatch) | 6 | 42 | 0 | PASS |
| f268 (exception laws) | 12 | 96 | 0 | PASS |

(Note: row/PASS counts are echoed per render; the invariant is the zero
unexpected-FAIL count, unchanged from CONT-25's recorded battery.)

## 3-run proof for the wave's causal claims

| target | sha16 ×3 | uncaught ×3 | claim |
|---|---|---|---|
| dooz (Track A) | d602648e8e401895 | 0 | F-277 post-fix state deterministic; composition #2 still starved |
| fnew253_probe (Track B positive control) | 7602563f52cce823 | 0 | real render + 147 PASS / 0 FAIL rows |
| Simple Calculator (Track B target) | 7960bce447ac6d8f | 2 | white screen persists (honest PARTIAL); Toolbar.onMeasure reached deterministically |

## rc-truth

Engine exit code is 0 ONLY on full SUCCESS (main.cpp law); anchor runs that
show rc=1 (dooz, opencalc) match their recorded rc exactly — PARTIAL
SUCCESS is the honest verdict for both, unchanged from the frozen records.

## Environment notes

- GitHub REST API: rate-limited at the wave's Phase 0 (recorded); issue
  #384 read via HTML scrape (`tmp/cont26_issue384.html`, 5 comments).
- F-Droid archive: REACHABLE (vc8/vc7/vc6 of com.simplemobiletools.calculator
  captured) — no Maven access attempted or needed (no 403 circumvention).
- ARM-only native compatibility: not treated as a runtime blocker this wave
  (LAW-001 scope); all executed targets are x86/x86_64-compatible.
