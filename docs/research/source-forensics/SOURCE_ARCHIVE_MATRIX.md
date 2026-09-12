# SOURCE ARCHIVE MATRIX — COMPLETE CROSS-ARCHIVE DIFFERENTIAL AUDIT
Generated: 2026-09-03 · Canonical reference: `github.com/Sh-TB/MiniAndroid-Compatibility-Runtime`
local `integration/master-reconciliation` HEAD = **f7144209** (362 commits, tree faea179c)
Method: independent fresh extraction + object-set diff (`cat-file --batch-all-objects`) + HEAD-tree
blob-SHA diff + untracked-worktree hashing vs canonical object DB. Evidence JSONs in `evidence/`.

## 0. Archive universe (20 unique / 23 on-disk copies)

| ID | Archive | Bytes | SHA256 (first 12) | Kind | On filebin | Status |
|----|---------|------:|-------------------|------|------------|--------|
| A-01 | MiniAndroid_CAMPAIGN-012-baseline_GIT_HANDOFF.zip | 9,002,641 | a60f76a1c8f5 | ZIP+git | MATCH | EXTRACTED, inspected |
| A-02 | MiniAndroid_CAMPAIGN013_REPORTS_bundle.zip | 21,799 | 64080a22abbe | ZIP (docs) | MATCH | EXTRACTED, inspected |
| A-03 | MiniAndroid_CANONICAL_MASTER_RECONCILED_272f216c.zip | 158,318,788 | 2e93d27d11a9 | ZIP+git | MATCH | EXTRACTED, inspected |
| A-04 | MiniAndroid_CANONICAL_MASTER_RECONCILED_f714420.zip | 157,354,279 | 11b2c482d73d | ZIP+git | MATCH | EXTRACTED, inspected |
| A-05 | MiniAndroid_FULL_VALIDATION_HANDOFF_6c9a91e.zip | 0 | e3b0c44298fc | ZIP | — | **CORRUPT_EMPTY (recorded)** |
| A-06 | MiniAndroid_MASTER_INTEGRATION_REVIEW_0fd1ad6.zip | 161,103,433 | 4ae914c2daf6 | ZIP+git | MATCH | EXTRACTED, inspected |
| A-07 | MiniAndroid_v0.11-unified-011_GIT_HANDOFF.zip | 8,271,563 | 5a664aa7cda9 | ZIP+git | MATCH | EXTRACTED, inspected |
| A-08 | MiniAndroid_v0.11.1-unified-011-1_GIT_HANDOFF.zip | 8,873,186 | 7f58e8140fdf | ZIP+git | MATCH | EXTRACTED, inspected |
| A-09 | MiniAndroid_v0.11.2-unified-011-2_GIT_HANDOFF.zip | 8,952,162 | 3a56d479b07a | ZIP+git | MATCH | EXTRACTED, inspected |
| A-10 | MiniAndroid_v0.11.3-unified-011-3_GIT_HANDOFF.zip | 9,755,340 | 45bae5948c0f | ZIP+git | MATCH | EXTRACTED, inspected — **UNIQUE OBJECTS FOUND** |
| A-11 | MiniAndroid_v0.11.4-fix-01_GAP-RECONCILIATION_GIT_HANDOFF.zip | 9,058,888 | 294ba77ca3aa | ZIP+git | MATCH | EXTRACTED, inspected |
| A-12 | MiniAndroid_v0.13.0_GIT_HANDOFF.zip | 7,903,986 | 8beea37a5986 | ZIP+git | MATCH | EXTRACTED, inspected |
| A-13 | MiniAndroid_v0.14.0_GIT_HANDOFF.zip | 0 | e3b0c44298fc | ZIP | — | **CORRUPT_EMPTY (recorded)** |
| A-14 | MiniAndroid_v0.14.0_PARTIAL_GIT_HANDOFF.zip | 9,503,830 | fb1cfd4d23bc | ZIP+git | MATCH | EXTRACTED, inspected |
| A-15 | temp_files/handoff.zip | 0 | e3b0c44298fc | ZIP | — | **CORRUPT_EMPTY (recorded)** |
| A-16 | temp_files/handoff2.zip | 0 | e3b0c44298fc | ZIP | — | **CORRUPT_EMPTY (recorded)** |
| A-17 | BACKUP_CANONICAL_PASS3_f714420.bundle | 153,568,354 | 6263610fffcd | GIT_BUNDLE | MATCH | verify OK, clone-inspected |
| A-18 | BACKUP_GITHUB_MASTER_FULL.bundle | 152,704,964 | b0578280b39f | GIT_BUNDLE | NOT on filebin | verify OK, clone-inspected — **1 unique object (tag)** |
| A-19 | BACKUP_GITHUB_MASTER_bbe0ce3.bundle | 152,706,027 | b532dea8139b | GIT_BUNDLE | MATCH | verify OK, clone-inspected |
| A-20 | BACKUP_LOCAL_INTEGRATION_0fd1ad6.bundle | 153,497,937 | 81edb258ca11 | GIT_BUNDLE | MATCH | verify OK, clone-inspected |

Additional remote inventory: filebin bin `miniandroid-k7q9x2` = 26 files (1.0 GB, expires 2026-09-10);
all 15 non-doc archives on filebin are SHA256-identical to local copies; the 11 filebin-only files are
knowledge/manifest docs (see SRC-019). Local-only archive: A-18.

## 1. Git forensics per repository

| ID | HEAD | Commits (objects) | Shallow | fsck --full | Unreachable | Reflog | Stash | Tags | HEAD-tree files |
|----|------|------------------:|---------|-------------|------------:|-------:|------:|-----:|----------------:|
| A-01 | ea81e00 (campaign-012-baseline) | 121 | YES (boundary a9434de) | CLEAN | 0 | 9 | 0 | 9 | 823 |
| A-03 | 272f216c | 360 (361 obj) | no | CLEAN | 0 | 30 | 0 | 10 | 1,000 |
| A-04 | f7144209 | 362 | no | CLEAN | 0 | 5 | 0 | 10 | 1,014 |
| A-06 | 0fd1ad66 | 356 (357 obj) | no | CLEAN | 0 | 21 | 0 | 10 | 981 |
| A-07 | 388fb45 (v0.11) | 121 | YES (a9434de) | CLEAN | 0 | 5 | 0 | 9 | 635 |
| A-08 | 340a9cf (v0.11.1) | 121 | YES (a9434de) | CLEAN | 0 | 6 | 0 | 9 | 785 |
| A-09 | 6c9a91e (v0.11.2) | 121 | YES (a9434de) | CLEAN | 0 | 7 | 0 | 9 | 808 |
| A-10 | ea81e00 (v0.11.3) | 78 | YES (**b6ef1439**) | CLEAN | 12 | 56 | 0 (3 stash-capture branches) | 4 | 823 |
| A-11 | b9d93cc (v0.11.4-fix-01) | 121 | YES (a9434de) | CLEAN | 0 | 8 | 0 | 9 | 827 |
| A-12 | 2ede367 (v0.13.0) | 120 | YES (a9434de) | CLEAN | 0 | 0 | 0 | 8 | 850 |
| A-14 | 894eae2 (v0.14.0-partial) | 121 | YES (a9434de) | CLEAN | 0 | 10 | 0 | 9 | 973 |
| A-17 (bundle) | f7144209 | 362 | no | CLEAN | 0 | — | — | 10 | 1,014 |
| A-18 (bundle) | bbe0ce3 | 322 | no | CLEAN | 0 | — | — | +pre-integration-github-baseline | 981 |
| A-19 (bundle) | bbe0ce3 | 322 | no | CLEAN | 0 | — | — | — | 981 |
| A-20 (bundle) | 2ede367 | 356 | no | CLEAN | 0 | — | — | — | 981 |

All shallow boundaries (`a9434de`, A-10's `b6ef1439`) verified PRESENT in canonical object DB.

## 2. Content differential vs canonical HEAD (f714420)

| ID | Same | Added in archive | Removed from archive | Modified | Renamed/Moved | Superseded | Untracked-unknown | Unique objects |
|----|-----:|-----------------:|---------------------:|---------:|--------------:|-----------:|------------------:|----------------|
| A-01 | 810 | 0 | 191 | 13 | 0 | 0 | 34 | 0 |
| A-03 | 986 | 0 | 14 | 14 | 0 | 0 | 0 | 0 |
| A-04 | **1014/1014** | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| A-06 | 974 | 0 | 33 | 7 | 0 | 0 | 101 | 0 |
| A-07 | 605 | 0 | 379 | 30 | 0 | 0 | 34 | 0 |
| A-08 | 768 | 0 | 229 | 17 | 0 | 0 | 34 | 0 |
| A-09 | 792 | 0 | 206 | 16 | 0 | 0 | 34 | 0 |
| A-10 | 810 | 0 | 191 | 13 | 0 | 0 | 0 | **64 (8c+4t+35tr+17b)** |
| A-11 | 818 | 0 | 187 | 9 | 0 | 0 | 34 | 0 |
| A-12 | 846 | 0 | 164 | 4 | 0 | 0 | 0 | 0 |
| A-14 | 969 | 0 | 41 | 4 | 0 | 0 | 34 | 0 |
| A-17/18/19/20 (bundles) | object-set diff vs canonical | | | | | | | **A-17:0 A-18:1 A-19:0 A-20:0** |

Reading of the table:
* **Every archive HEAD commit is an ANCESTOR of canonical HEAD** (merge-base verified for all 11 ZIP
  repos and all 4 bundle heads). "Modified/Removed" rows are ancestor-version evolution, and every
  such archive blob was additionally proven to exist inside the canonical object DB
  (`unique_objects = 0` for all archives except A-10) — i.e., canonical contains the full content
  history of every file version any archive holds.
* A-04 (the current handoff ZIP) is byte-exact vs canonical HEAD tree (1014/1014, 0 unique objects,
  0 untracked-unknown).
* Rename/move detection across all archives: **0 candidates** (no archive path carries content that
  canonical stores only under a different path).
* A-10 is the single archive holding objects unknown to canonical — fully analyzed in
  `MASTER_SOURCE_DIFFERENTIAL_LEDGER.md` (SRC-001…SRC-009). Verdict: stash captures from the
  UNIFIED_002/007/011 era whose SOURCE content is byte-for-byte present in canonical (the
  UNIFIED_011.2 FNA-FIX is present verbatim at HEAD `dalvik_engine.cpp` line 6530; all 12
  UNIFIED_007 resource-pipeline source files are IN_CANON blobs; the U007 `android_shadows.cpp`
  real-inflation rewrite is present at HEAD `android_shadows.cpp` line 898 with strictly newer
  semantics). Remaining unique A-10 blobs are 5 build artifacts, 2 runtime-data files, 6 superseded
  doc snapshots, 1 superseded Makefile, 1 superseded .gitignore, plus 4 original annotated tag
  objects (metadata only).
* A-18's single unique object = annotated tag `pre-integration-github-baseline` (100e36ee → bbe0ce3,
  metadata only).
* Untracked-unknown files (305 across 7 archives) = campaign-014 raw runtime logs (crash.log/run.log)
  and `run/` runtime artifacts. **Zero source files.**

## 3. Explicit status — every archive (no archive left at "checked")

| ID | Unique files | Unique implementations | Git-only changes | Knowledge-only changes | Potential lost fixes | Final status |
|----|-------------:|------------------------|------------------|-----------------------:|---------------------:|--------------|
| A-01 | 34 untracked logs | none | 0 (all objects in canonical) | none | 0 | FULLY_REPRESENTED (ancestor ea81e00) |
| A-02 | 13 doc files | none | n/a (no .git) | campaign-013 reports — crosschecked | 0 | FULLY_REPRESENTED (docs subset of canonical) |
| A-03 | 0 | none | reflog-only commit b5d2140 → objects IN canonical | none | 0 | FULLY_REPRESENTED (ancestor 272f216c) |
| A-04 | 0 | none | none (byte-exact HEAD) | none | 0 | IS_CANONICAL_HANDOFF |
| A-06 | 101 untracked logs | none | reflog-only commit (in canonical) | none | 0 | FULLY_REPRESENTED (ancestor 0fd1ad66) |
| A-07 | 34 untracked logs | none | 0 | none | 0 | FULLY_REPRESENTED (ancestor 388fb45) |
| A-08 | 34 untracked logs | none | 0 | none | 0 | FULLY_REPRESENTED (ancestor 340a9cf) |
| A-09 | 34 untracked logs | none | 0 | none | 0 | FULLY_REPRESENTED (ancestor 6c9a91e) |
| A-10 | 17 unique blobs (0 source-loss) | 2 source intermediates — BOTH proven present at HEAD | 8 stash commits + 4 tag objects + 3 branches | 6 superseded doc snapshots | 1 candidate (FNA-FIX) → **NOT lost, present at HEAD** | FULLY_REPRESENTED + HISTORICAL_METADATA_HOLDER |
| A-11 | 34 untracked logs | none | 0 | none | 0 | FULLY_REPRESENTED (ancestor b9d93cc) |
| A-12 | 0 | none | 0 | none | 0 | FULLY_REPRESENTED (ancestor 2ede367) |
| A-14 | 34 untracked logs | none | 0 | none | 0 | FULLY_REPRESENTED (ancestor 894eae2) |
| A-05/A-13/A-15/A-16 | — | — | — | — | — | CORRUPT_EMPTY (recorded, not ignored) |
| A-17 | 0 | none | none | none | 0 | CANONICAL_BACKUP (0 unique objects) |
| A-18 | 0 | none | 1 tag object | none | 0 | GITHUB_BASELINE_BACKUP (metadata-only delta) |
| A-19 | 0 | none | none | none | 0 | GITHUB_BASELINE_BACKUP (pure subset) |
| A-20 | 0 | none | none | none | 0 | PASS1_INTEGRATION_BACKUP (pure subset) |
| filebin docs (11) | — | — | — | PASS3 report byte-identical to repo doc; others superseded/pass-era records | 0 | ACCOUNTED (SRC-019) |
| UNIFIED_000–011 + legacy coder-2 originals | — | — | — | — | — | NOT_ON_DISK — compensated by A-07..A-11 unified lineage + A-10 stash-era closure (SRC-021) |

## 4. Verdict matrix

* Archives inspected: **20/20** (plus 11 filebin knowledge docs) — none skipped.
* Git-bearing artifacts inspected: **15/15** (11 ZIP repos + 4 bundle clones).
* Potential lost fixes found: **1 candidate → resolved ALREADY_IN_CANONICAL** (0 actual losses).
* Untracked historical source changes: **0 source files** (305 runtime-log files recorded).
* Reverted fixes: **0** (no archive blob carries content absent from canonical object DB except the
  A-10 items individually resolved above; the two A-10 source intermediates are strictly OLDER than
  what canonical HEAD holds).
* Canonical source modified during this audit: **NO**. Pushed: **NO**
  (remote re-verified at bbe0ce3 via ls-remote during this pass).
