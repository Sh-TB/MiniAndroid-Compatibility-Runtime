# MiniAndroid Test Corpus Policy

**Status:** EXP-083 Phase 39.6
**Last updated:** 2026-08-22

This document defines the rules for what APKs and test inputs may live in the
source tree, what must be external, and how the test runner handles missing
inputs.

---

## APK Classification

APKs are classified into five categories. The category determines whether the
APK may live in the source tree or must be fetched externally.

### MICRO APK
- **Size:** < 5 KB
- **Origin:** Deliberately hand-crafted DEX/APK fixture
- **Examples:** `miniandroid/test_apks/exp052/case1_no_catch.apk` (444 B),
  `miniandroid/test_apks/exp043/a_finite_loop.apk` (720 B)
- **Storage policy:** May live in `miniandroid/test_apks/` (tracked).
- **Justification:** Tiny, deterministic, byte-stable across runs. Used to test
  specific opcode/exception/invoke paths without depending on real-world app
  complexity.

### SYNTHETIC CORPUS APK
- **Size:** 0.5–5 KB
- **Origin:** Programmatically generated minimal APKs (`HelloWorld_original.apk`,
  `SimpleCalculator.apk`, `NotesApp.apk`, etc.)
- **Examples:** `miniandroid/download/apks/*.apk`, `miniandroid/download/exp027_real_apks/*.apk`
- **Storage policy:** May live in source tree (tracked). These are essentially
  DEX bytecode fixtures packaged as APKs.
- **Justification:** Synthetic, byte-stable, used as the baseline corpus for
  every regression run.

### SMALL REAL APK
- **Size:** 5 KB–1 MB
- **Origin:** Real F-Droid apps with minimal complexity
- **Examples:** `de.duenndns.gmdice_8.apk` (62 KB), `org.debian.eugen.headingcalculator_1.apk` (60 KB)
- **Storage policy:** **External when practical.** May be tracked ONLY when:
  - The APK is byte-stable across F-Droid releases (i.e. pinned by version+sha256)
  - The test that uses it cannot meaningfully run without it
  - The total tracked APK size remains under 10 MB
- **Justification:** Small enough that fetching adds friction without proportional benefit. But
  they should NOT multiply — one canonical copy per APK.

### LARGE REAL APK
- **Size:** > 1 MB
- **Origin:** Real production APKs from app vendors
- **Examples:** `com.benny.openlauncher_39.apk` (3.3 MB), `com.emmanuelmess.tictactoe_3.apk` (4.3 MB)
- **Storage policy:** **External / Git LFS / GitHub Release.** Must NOT be
  committed to the normal source tree.
- **Justification:** GitHub warns above 50 MiB and blocks above 100 MiB in
  normal Git. Large APKs bloat `git clone` and history. Fetch on demand via
  the manifest in `tests/corpus/apks.json`.

### TELEGRAM (the canonical large target APK)
- **Size:** 78.85 MB (as of v10.14.5)
- **Origin:** https://telegram.org/android
- **Storage policy:** **EXTERNAL INPUT — NEVER in source tree.**
- **Justification:**
  - 78 MB exceeds GitHub's 50 MiB soft warning.
  - It is downloaded content, not authored source.
  - Multiple EXPs (038, 042, 057, 059, 064, 066, 078, 079, 080, 081, 082)
    reference it, but they should fetch it from a single external source.
  - The `tests/corpus/apks.json` manifest declares the expected SHA256 and
    download URL; the runner verifies the hash on fetch.

### GENERATED APK
- **Size:** varies
- **Origin:** Produced by `miniandroid/tools/build_*.py` or test scaffolding
- **Storage policy:** **NEVER commit unless deliberately retained as a fixture.**
- **Justification:** Generated artifacts are reproducible from source inputs;
  committing them duplicates state.

---

## Required Metadata for Every Retained APK

Every APK that lives in the source tree (i.e. MICRO and SYNTHETIC categories
above) MUST have:

1. **SHA256** — recorded in `tests/corpus/apks.json`
2. **Source** — original download URL or `synthetic` / `hand-crafted`
3. **Purpose** — what test/experiment uses it
4. **Expected capability** — what the test asserts (e.g. "renders dice button",
   "executes if-eqz branch")
5. **Test command** — the exact CLI invocation that uses this APK

For external APKs (LARGE REAL, TELEGRAM), the manifest entry records the same
metadata plus a `download_url` so the runner can fetch on demand.

---

## Test Runner Behavior

The test runner reads `tests/corpus/apks.json` at startup. For each APK the
runner needs, it reports:

| State | Meaning |
|---|---|
| `APK FOUND`    | File exists locally and SHA256 matches manifest |
| `APK MISSING`  | File does not exist locally — fetch from `download_url` |
| `HASH MATCH`   | SHA256 verified after fetch |
| `HASH MISMATCH`| SHA256 does NOT match manifest — refuse to run |

Tests that depend on an external APK MUST fail loudly with a clear error
message when the APK is missing or hash mismatches. They MUST NOT silently
skip.

---

## Current State (as of EXP-083)

| Category | Count | Total size | Storage |
|---|---:|---:|---|
| MICRO_TEST_FIXTURE | 16 | ~12 KB | tracked in `test_apks/exp043/`, `test_apks/exp052/` |
| SYNTHETIC_CORPUS_APK | 41 | ~50 KB | tracked in `download/apks/`, `download/exp027_real_apks/` |
| REAL_CORPUS_APK_FDROID (small) | 8 | ~1.5 MB | tracked in `download/exp073_real_apps/`, `download/exp076_corpus/`, `download/exp037_real_apks/` |
| REAL_CORPUS_APK_FDROID (large) | 2 | 7.6 MB | tracked in `download/exp076_corpus/`, `download/tictactoe.apk` |
| REAL_LARGE_TARGET_APK (Telegram) | 1 | 78.85 MB | **tracked — VIOLATES policy** |

### Known violations
1. **`miniandroid/download/exp038_telegram/Telegram.apk`** (78.85 MB) — must be
   externalized. Pending: move to GitHub Release / Git LFS / external fetch.

### Cleanups applied in EXP-083 Phase 38
- 4 duplicate APK pairs removed (tictactoe × 2, unote × 2, cachecleaner × 2,
  exp052 case2/case4 × 2)

### Cleanups planned for EXP-083 Phase 39
- (39.1) Externalize Telegram.apk — untrack from working tree, document
  fetch procedure in `tests/corpus/apks.json`.
- (39.2) Audit large F-Droid APKs (>1 MB) — move to Git LFS or external fetch.

---

## Forbidden Patterns

The source tree purity checker (`tools/check_source_tree.py`) rejects:

- `*.apk` outside `miniandroid/test_apks/` or `miniandroid/download/apks/`
  or `miniandroid/download/exp027_real_apks/` (synthetic corpus locations).
- `*.apk` > 5 MB committed via normal Git (must be LFS or external).
- Any APK named `Telegram.apk` or matching `telegram*.apk` (case-insensitive)
  in the working tree — Telegram must be external.

---

## Updating the Policy

When adding a new APK to the corpus:

1. Compute SHA256 of the APK.
2. Add an entry to `tests/corpus/apks.json` with the required metadata.
3. Place the APK in the appropriate directory based on its category.
4. If the APK is > 5 MB or > 50 MB, request Git LFS or external fetch.
5. Run `python tools/check_source_tree.py` to verify the tree remains pure.
