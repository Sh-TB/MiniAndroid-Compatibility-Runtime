# REGRESSION_010 — after EVERY major adoption (R28/R29/R31)

Golden baselines (pixel-data SHA-16, the Campaign 009 convention):
GMDice `26fc4116e4ba65b4` (158,040 non-white px) · Telegram `b9b06072ea17d7fd`
(41,233 px) · dooz attach records = 5.

## 1. After R1 — libpng PNG adoption (commit 8d4e25b)

| Target | Metric | Before | After | Verdict |
|---|---|---|---|---|
| GMDice | pixdata SHA-16 | `26fc4116e4ba65b4` | `26fc4116e4ba65b4` | **IDENTICAL** ✓ |
| GMDice | non-white px | 158,040 | 158,040 | ✓ |
| Telegram | pixdata SHA-16 | `b9b06072ea17d7fd` | `b9b06072ea17d7fd` | **IDENTICAL** ✓ |
| Telegram | non-white px | 41,233 | 41,233 | ✓ |
| dooz (flag ON) | attach records | 5 | 5 | ✓ |
| a4 PNG fixtures | PIL byte-identity | 8/8 (legacy set) | **12/12** (extended set) | ✓+ |
| PNG corpus | decode success | 97.07% | **100%** | improvement |
| simplestopwatch | exit code | 1 (known) | 1 | ✓ unchanged |

Note: PNG **file** hashes changed by design (libpng encoder stream ≠ custom
encoder bytes at identical pixel content). The pixdata hash is the contract.

## 2. After R9/R10 — PortableGL GLES backend (commit 4e128c0)

| Target | Verdict |
|---|---|
| All goldens | ✓ IDENTICAL (additive module: `src/gles/` compiles into new harness binaries only at this stage; no runtime dispatch touched) |
| New positive evidence | golden cube rasterized: 77,112/76,800-vs-7,200 non-bg px recorded (10.0% / 25.7% coverage), PNG written via libpng writer |

## 3. After R3 — Yoga adapter (commit f131606)

| Target | Verdict |
|---|---|
| All goldens | ✓ IDENTICAL (adapter lives in the experiment harness; runtime layout path untouched this campaign) |

## 4. After R14 — real stack traces (commit f9190da)

| Target | Metric | Before | After | Verdict |
|---|---|---|---|---|
| GMDice | pixdata | `26fc4116e4ba65b4` | `26fc4116e4ba65b4` | ✓ (behavioral code touched: getStackTrace path — goldens unaffected because goldens never call getStackTrace) |
| Telegram | pixdata | `b9b06072ea17d7fd` | `b9b06072ea17d7fd` | ✓ |
| Telegram auth chain | launch→StartMessaging→phone→onNextPressed→TL_auth_sendCode→controlled response→RequestDelegate→SMS View | PROVEN (UNIFIED_002) | NOT re-run in 010 (no behavior change to that path; click-audit tooling untouched) | standing 002 evidence + zero-diff goldens |
| dooz | attach records | 5 | 5 | ✓ |
| dooz | Intrinsics | livelock | **9 real NPEs thrown** | progression (positive) |

## 5. Final full-suite state at archive time

- `make -j4` clean build ✓
- GMDice golden ✓ · Telegram golden ✓ · dooz attach ✓
- 7,036-PNG corpus: 7,036/7,036 via the integrated decoder ✓
- a4 fixtures: 12/12 ✓
- GLES cube golden: exit 0 both resolutions ✓
- Yoga differential: 10/10 <8px ✓
- 7 new-corpus APK runs recorded (REAL_APK_MATRIX_010 §4) ✓
- simplestopwatch/known-fallback corpus behavior unchanged ✓

## 6. Known regressions: NONE

Nothing that worked before Campaign 010 works worse after it. The only
changed observable outside additions is the PNG file-byte stream (documented)
and honest correction of the 3 tRNS misdecodes (bugs fixed, not regressions).
