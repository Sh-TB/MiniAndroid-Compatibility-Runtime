# CONT-29 REGRESSION MATRIX — at binary d35a60d43f83331c (HEAD baa6654c)

Gate set mirrors CONT-27/28 (evidence/cont2{7,8}/REGRESSION_MATRIX.md).
NO engine code changed this wave (zero-regression expectation; the gate
certifies it). rc captured per call (rc-truth law). All hashes sha256[0:16]
of screenshot.png at 1080x1920, frames=5, max-seconds=15.

## 1. FROZEN ANCHORS ×3 (byte-exact expectation)

| anchor | family | r1 | r2 | r3 | sha16 | verdict |
|---|---|---|---|---|---|---|
| dooz | Compose (F-277 byte-anchor) | rc=1 | rc=1 | rc=1 | d602648e8e401895 | 3/3 MATCH |
| microtimer | app | rc=0 ×3 | | | da73010a37dd0189 | 3/3 MATCH |
| unote | app | rc=0 ×3 | | | 4f1a9e4e8f64fae8 | 3/3 MATCH |
| gmdice | game/GL | rc=0 ×3 | | | f3b483fe7b7cf51b | 3/3 MATCH |
| opencalc | app | rc=1 ×3 (known face) | | | a976d2f9fb675cb3 | 3/3 MATCH |
| tttdeluxe | game | rc=0 ×3 | | | af6094295ecb50e3 | 3/3 MATCH |
| flappycow | Surface/GL control | rc=0 ×3 | | | 13cf47464d9787f4 | 3/3 MATCH |
| g2048 | Canvas control | rc=0 ×3 | | | 59ca1526611c4622 | 3/3 MATCH |

24/24 byte-identical — Surface/GL and Canvas families intact.

## 2. TRACK RUNS ×3

| track | run | rc | sha16 | verdict |
|---|---|---|---|---|
| A (oracle12, real-Compose) | r1-r3 | 1 ×3 | b270ff040b3601dc | deterministic, == CONT-28 record |
| B (Simple Calculator vc8) | r1-r3 | **0 ×3** | 7960bce447ac6d8f | **FULL SUCCESS retained, == CONT-27/28 record** |

## 3. PROBE BATTERY

| probe | rc | PASS | FAIL | note |
|---|---|---|---|---|
| fcol | 1 | 140 | 0 | == CONT-27/28 |
| f259 | 1 | 49 | 0 | == CONT-27/28 |
| f259g | 1 | 84 | 7 | the known-honest F259-L row only |
| f266 | 1 | 42 | 0 | == CONT-27/28 |
| f268 | 1 | 96 | 0 | == CONT-27/28 |

## 4. VERDICT

Zero drift against the CONT-28 records on every gate row. The wave's Track A
work was pure evidence-gathering (no engine source edits), so the expectation
was exact equality and exact equality is what every row shows.

Gate artifacts: run/cont29/regression/* (runs + logs), run/cont29_regression_gate.log.
