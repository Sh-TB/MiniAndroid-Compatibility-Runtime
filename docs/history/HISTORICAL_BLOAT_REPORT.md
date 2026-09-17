# HISTORICAL_BLOAT_REPORT — S51 finalization

**Date:** 2026-09-17 · **HEAD at report:** S51-finalization cluster
**Law:** current-tree cleanup ≠ history cleanup. This report covers both,
separately and honestly. No history rewrite was performed (see §3).

## 1. Current tree (tracked) — POST-CLEANUP STATE

| Metric | Value |
|---|---|
| Tracked files | 3,447 (was 3,498 pre-cleanup; 51 dead stubs + 93 META-INF + 2 archived removed) |
| Tracked bytes | ~11.0 MB (max single file: `miniandroid/src/dex/dalvik_engine.cpp` 1.52 MB — source) |
| APK/AAB/SO/ZIP/TAR tracked | **0** |
| Tracked `.log` | 2 — Telegram `tg_run1/2_distilled.log` (10.9 + 29 KB, distilled evidence class) |
| Traced files > 500 KB | dalvik_engine.cpp (1.52M), upstream sources jars (~1.0M, 0.72M, 0.65M, 0.59M), nlohmann json.hpp (0.92M), campaign014 compose-interaction trace (0.58M, deliberately kept — documented research evidence, `docs/research/compose-study.md`), SYMBOL_INDEX.json (0.52M) |
| Zero-byte tracked files | 3 (deliberate: EOF-law fixture `empty.bin`, package `__init__.py`, documented-empty `p1_mining/verify_log.txt`) |

## 2. Git history (reachable objects) — MEASURED, NOT REWRITTEN

| Scope | Blobs > 1 MB | Uncompressed size | Dominant classes |
|---|---|---|---|
| main-reachable history | ~122 | **~987 MiB** | session stderr logs (~885 MiB, 56 files: `sttt_run*_stderr` ~30 MB ×4, `s26_*` 17 MB ×…), dooz/telegram campaign traces |
| all remote refs (main + 4 `archive/*` branches) | ~286 | **~1.99 GiB** | + `llvm-mingw.tar.xz` 83.9 MB, `Telegram.apk` 82.7 MB, `libLLVM` 78.1 MB, `telegram_call_graph.json` 65.5 MB, `fdroid_index` 53.3 MB |
| `.git` on disk (packed) | — | 625 MB (pack 491.5 MiB) | includes loose-object tail from campaign churn |

Top offender classes (all **history-only** — none in the current tree):

| Path (historical) | Size | Class | Safe to remove from history? |
|---|---|---|---|
| `llvm-mingw.tar.xz` | 83.9 MB | toolchain blob | YES — documented reproducible download; zero current-tree dependency |
| `miniandroid/download/exp038_telegram/Telegram.apk` | 82.7 MB | corpus APK | YES — re-acquirable; provenance recorded (SHA `193ad551…`) |
| `libLLVM*` | 78.1 MB | toolchain blob | YES — same law as llvm-mingw |
| `telegram_call_graph.json` | 65.5 MB | raw exhaust | YES — compact extraction exists in research docs |
| `fdroid_index` | 53.3 MB | raw exhaust | YES — re-fetchable |
| `sttt_run*_stderr` (~30 MB each) | ~885 MB total | raw logs | YES — decisive signatures already extracted into solved cards |

Estimated post-rewrite pack size if all history-only log/APK/toolchain blobs
were excised: **roughly 491 MiB → well under 100 MiB** (the current tracked
tree is ~11 MB; the remaining history is real source/evidence work).

## 3. History rewrite status — NOT PERFORMED (law)

- No force-push, no filter-repo, no ref rewrite happened in S51 finalization.
- Standing authorization exists in the brief ("If explicit authorization …
  already available, still make a full backup first"), but the **push
  credential is currently invalid** (GitHub: "Invalid username or token",
  401 on both token variants), so any rewrite-and-push would strand the repo
  mid-operation. Sequencing law: first a successful authenticated push of the
  current honest state; only then a backup + `HISTORY_PURGE_PLAN.md` +
  executed rewrite + fresh-clone verification.
- Full mirror backup exists: `/home/z/archive/s51_full_mirror` (506 MB, all
  refs) — created S51 phase 0. External cleanup archive:
  `/home/z/archive/miniandroid/s51_finalization/` (2 files + SHA256s).

## 4. GitHub ecosystem (beyond git)

| Surface | Status |
|---|---|
| Releases (7 tags, v0.0.1…v0.0.6) | VERIFIED — v0.0.6-Leghorn assets re-downloaded + SHA256 EXACT MATCH (`evidence/cleanup/RELEASE_V0.0.6_CHECKSUM_VERIFICATION.json`) |
| LFS | not used (no objects) |
| Issue/PR/comment attachments | **PARTIALLY-VERIFIED** — API returned 403 unauth / 401 with provided token; HTML-level audit done in S51 phase 0; attachment-level deletion impossible without valid credential |
| GitHub repo size metric | not observable via API this session (auth) — Git-side numbers above are the authoritative proxy |

## 5. Removal decision record (this campaign)

| Removed from tree | Why | Where the knowledge went |
|---|---|---|
| `corpus_cache/dooz23_extracted/` (93 files, 516 KB) | extraction residue, zero consumers, reproducible from the APK | `docs/upstream/dooz23_meta_inf_provenance.md` (verbatim version pins + APK SHA + repro command) |
| 50 zero-byte campaign014 stubs + 1 s26 stub | dead placeholders, no knowledge content | nothing to preserve (empty); dirs keep their non-empty evidence |
| `docs/runtime/EXP083_run_inventory.csv` (721 KB) | historical machine inventory of deleted `miniandroid/run` state | external archive + SHA256 (`/home/z/archive/miniandroid/s51_finalization/ARCHIVE_SHA256.txt`) |
| `A10_unique_blobs/195e88c810b6_unknown` (646 KB) | unknown-blob research artifact (C++ source) | external archive + SHA256 (same manifest); references in research JSONs describe its role |
