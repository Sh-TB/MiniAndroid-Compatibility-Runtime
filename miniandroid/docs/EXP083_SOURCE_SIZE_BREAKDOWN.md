# EXP-083 Phase 39.3/39.15 — Source-Size Breakdown

**Generated:** 2026-08-22T19:04:51.627356+00:00

This report calculates the true source-code size of the MiniAndroid
repository, excluding all generated/downloaded/built artifacts.

---

## Exclusion Criteria

The following were excluded from "source-only":

- `.git/` — Git object database (history)
- `miniandroid/run/` — runtime experiment output
- `miniandroid/build/`, `miniandroid/build_asan/`, `miniandroid/build_exp*/` — build artifacts
- `miniandroid/reports/` — generated reports
- `miniandroid/download/` — downloaded APKs and indices
- `miniandroid/experiments/` — historical experiment traces
- `tool-results/` — transient tool outputs
- All `*.log`, `*.tmp`, `*.dmp`, `*.core` files
- All `*.apk`, `*.aab`, `*.zip`, `*.jar` files outside allowed fixture dirs
- All `*.o`, `*.so`, `*.dylib`, `*.dll` build objects
- All `*.ppm` screenshots

---

## Source-Only Size

| Category | Files | Size |
|---|---:|---:|
| SOURCE_CODE | 75 | 2.31 MB |
| TOOLS_SCRIPTS | 97 | 2.25 MB |
| TEST_SOURCE | 0 | 0.00 B |
| DOCUMENTATION | 144 | 4.46 MB |
| RESEARCH_SCRIPTS | 0 | 0.00 B |
| THIRD_PARTY_SOURCE | 1 | 898.41 KB |
| REPO_META | 3 | 199.49 KB |
| **SOURCE-ONLY TOTAL** | **320** | **10.09 MB** |


---

## Tracked Test Fixtures

| Category | Files | Size |
|---|---:|---:|
| REGRESSION_FIXTURES (`test_apks/`, `golden/`) | 55 | 30.85 KB |
| RUNTIME_DATA_FIXTURES (`runtime/data/`) | 1 | 383.00 B |
| DATABASE_INDEX (`database/`) | 43 | 520.58 KB |
| **FIXTURES TOTAL** | **99** | **551.81 KB** |

---

## External Test Inputs (committed APKs)

| Description | Size |
|---|---:|
| All tracked APK files in `miniandroid/download/` | 91.52 MB |

(See `docs/EXP083_APK_INVENTORY.md` for the full APK inventory.)

---

## Generated Local Artifacts

| Description | Size |
|---|---:|
| `miniandroid/run/` tracked | 19.18 MB |
| `miniandroid/reports/` tracked | 0.00 B |
| `miniandroid/experiments/` tracked | 12.10 MB |
| `tool-results/` tracked | 996.88 KB |
| `run/` (root-level) tracked | 5.94 MB |
| **GENERATED TOTAL** | **39.42 MB** |

---

## Git Object Database

| Description | Size |
|---|---:|
| `.git/` directory | 145.48 MB |

---

## Final Repository Size Summary (39.15)

| Category | Size |
|---|---:|
| SOURCE ONLY | **10.09 MB** |
| TRACKED TEST FIXTURES | 551.81 KB |
| EXTERNAL TEST INPUTS (APKs) | 91.52 MB |
| GENERATED LOCAL ARTIFACTS | 39.42 MB |
| `.git/` | 145.48 MB |
| **TOTAL WORKING TREE** | **287.05 MB** |

The most important metric is **SOURCE ONLY: 10.09 MB**.

