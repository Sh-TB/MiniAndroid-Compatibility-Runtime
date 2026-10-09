# CONT-30 REGRESSION MATRIX — final binary b84114cd6f8bad1d

Date: 2026-10-09. Engine changes this wave: F-NEW-286 (M3-19 zero-payload
re-entrancy law), F-NEW-287 (Method.getAnnotations never-null + F-087c
proxy marker + annotationType arm). Baseline binary d35a60d43f83331c
(byte-exact HEAD rebuild).

## Anchors (canonical harness, 1080x1920, --frames 5)

| anchor | want (frozen) | r1 | r2 | r3 | verdict |
|---|---|---|---|---|---|
| dooz (io.github.yamin8000.dooz_23) | d602648e8e401895 | MATCH | MATCH | MATCH | BYTE-IDENTICAL ×3 |
| microtimer (dubrowgn.microtimer_8) | da73010a37dd0189 | MATCH | MATCH | MATCH | BYTE-IDENTICAL ×3 |
| unote (app.varlorg.unote_30) | 4f1a9e4e8f64fae8 | MATCH | MATCH | MATCH | BYTE-IDENTICAL ×3 |
| gmdice (de.duenndns.gmdice_8) | f3b483fe7b7cf51b | MATCH | MATCH | MATCH | BYTE-IDENTICAL ×3 |
| opencalc (opencalculator_53) | a976d2f9fb675cb3 | MATCH | MATCH | MATCH | BYTE-IDENTICAL ×3 |
| tttdeluxe (com.emmanuelmess.tictactoe_3) | af6094295ecb50e3 | MATCH | MATCH | MATCH | BYTE-IDENTICAL ×3 |
| flappycow (Surface/GL control) | 13cf47464d9787f4 | MATCH | MATCH | MATCH | BYTE-IDENTICAL ×3 |
| g2048 (Canvas control) | 59ca1526611c4622 | MATCH | MATCH | MATCH | BYTE-IDENTICAL ×3 |

24/24 rows MATCH. Zero drift from the two generic laws.

## Probe battery

| probe | rc | PASS | FAIL | vs CONT-28/29 record |
|---|---|---|---|---|
| fcol (run/w7/fcol.apk) | 1 | 140 | 0 | == 140/0 |
| f259 (run/w7/f259.apk) | 1 | 49 | 0 | == 49/0 |
| f259g (run/w7/f259g.apk) | 1 | 84 | 7 | == 84/7-known (honest F259-L rows) |
| f266 (run/w8/f266.apk) | 1 | 42 | 0 | == 42/0 |
| f268 (run/cont18g/f268.apk) | 1 | 96 | 0 | == 96/0 |
| fnew253 (positive control, rebuilt) | 1 | 147 | 0 | == 147/0 (CONT-26 record) |
| **fnew286 (NEW this wave)** | 1 | **10** | **0** | new contract — all rows PASS |

## Track A / Track B instruments

| instrument | result |
|---|---|
| oracle baseline (pre-fix binary) | b270ff040b3601dc ×3 == CONT-29 |
| oracle post-fix (final binary) | b5a7a35d5fe0564b ×3 deterministic — frame-1 deletion GONE; content blocked by F-NEW-288 (registered CLASSIFIED) |
| dooz M3-19 stub census | 5 → 1 (payload-distinct key; anchor byte-identical — semantic neutrality proven) |
| Simple Calculator vc8 | APK absent in this container (reset loss); FULL SUCCESS RETAINED from the CONT-27/28/29 records (7960bce447ac6d8f ×3) — re-fetch + re-run owed by the next wave that has the APK |

## Verdicts

- Regression gate: **GREEN** — zero anchor drift, probe battery == records,
  new probe green.
- Track A: PARTIAL (advancement + 2 roots fixed; content pixels still
  honestly NOT claimed).
- Track B: RETAINED (unchanged by this wave; APK re-supply owed).
