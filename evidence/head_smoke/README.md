# HEAD-SMOKE — anchor wall re-execution at freshly built HEAD binary

- Binary: `miniandroid/build/miniandroid` built from `60f08b6` (origin/main tip) via the
  canonical `miniandroid/Makefile` (container: cmake-4.4 present but CMakeLists was stale —
  see BUILD-TRAIN commit for the cmake-4.x compat fixes; Makefile path is the source of truth).
- Runner: `scripts/head_anchor_smoke.py` (install → run 90s window → screenshot sha16 + PNG metrics).
- Ledger: `HEAD_SMOKE_LEDGER.json` (14 rows).

## Verdict (honest)

| Anchor | Pin (CONT-42 wall) | HEAD sha16 | Verdict |
|---|---|---|---|
| unote | 7481e9b4 | 7481e9b468eaa376 | **BYTE-EXACT MATCH** (136,080 content px) |
| dooz (both APK copies) | 851cc176 | 851cc1761a1dfcdf | **BYTE-EXACT MATCH** (231,873 px — REAL board content) |
| microtimer | bbd350b6 | bbd350b6c14fbd52 | **BYTE-EXACT MATCH** (893,597 px) |
| gmdice | 3891679d | 3891679dff449331 | **BYTE-EXACT MATCH** (182,535 px) |
| tower3d | 11a38a5a | (early rc=1) | **MISMATCH — new named root**: `SharedLibraryLoadRuntimeException` unwound through `Lcom/badlogic/gdx/backends/android/AndroidApplicationConfiguration$1;.load` (libGDX native-load family; task issue registered) |

Non-pinned rows (rendered real pixels at HEAD): bouncy 978,380 px · opmt 1,258,563 px ·
tripeaks 559,878 px · fishrings 105,061 px · memory(secuso) 58,668 px.
Early-exit rows needing their own census pass: tictactoe, stopwatch (rc=1, blank shot).

Laws: every claim above carries the run artifacts under the external `run/head_smoke/` store
(gitignored by design); this ledger + hashes are the curated proof. No log bodies committed.
