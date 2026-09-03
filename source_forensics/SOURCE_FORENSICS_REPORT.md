# SOURCE FORENSICS REPORT — COMPLETE CROSS-ARCHIVE SOURCE DIFFERENTIAL AUDIT
Date: 2026-09-03 · Auditor branch: read-only; **no push performed; canonical source NOT modified.**

## 1. Scope and method (what was actually done — not assumed)

1. **Inventory**: every ZIP/bundle/patch on all project volumes hashed (SHA256), deduplicated, and
   cross-checked against the remote filebin bin (26 files, SHA-per-file verified from the bin's
   JSON API — all 15 non-doc remote archives are byte-identical to local copies).
   `evidence/00_archive_inventory.json`.
2. **Independent extraction**: every non-empty ZIP (`unzip -t` integrity OK first) extracted into
   its own isolated directory under `miniandroid_ws/forensics/extract/<ARCHIVE_ID>/`; originals
   untouched. `evidence/02_extraction.json`.
3. **Git forensics per repository** (11 ZIP-embedded repos + 4 bundles cloned to temp):
   HEAD/branches/tags/commit-count/shallow-status, `fsck --full`, `fsck --unreachable --dangling`,
   reflog, stash, earliest/latest commit, full object-set export. `evidence/03_git_forensics.json`.
4. **Content differential vs canonical HEAD f714420**:
   - HEAD-tree diff (path + git-blob-SHA) per archive → SAME / ADDED / REMOVED / MODIFIED /
     RENAMED-MOVED / SUPERSEDED;
   - rename/move detection by content hash across paths (0 candidates);
   - untracked worktree files hashed (`blob <len>\0` SHA-1) and checked against the canonical
     object DB;
   - complete object-set difference (commits/trees/blobs/tags) per archive and per bundle;
   - shallow-boundary parent presence check;
   - tag-set comparison. `evidence/04_content_differential.json`.
5. **Deep dive of every unique object** found (all in A-10 + 1 in A-18): full `git show` of each
   unique commit, blob extraction, nearest-version and HEAD-version diffs, function-level reading
   of the two source-code variants. `evidence/05_deep_dive.json`.
6. **Ancestry proof**: `merge-base --is-ancestor` for all 11 archive HEADs + 4 bundle heads →
   all ANCESTOR of canonical HEAD.
7. **Canonical self-forensics**: canonical's own unreachable objects (5 diagnostics) identified as
   2 Pass-3-era stash commits + 3 private trees; **0 unique blobs** (every blob reachable from HEAD).
8. **Knowledge crosscheck**: 50-row KNOWLEDGE_LEDGER.csv parsed; every referenced artifact probed
   at HEAD; K-34…K-42 code markers + fixtures + pass-3 docs verified present; semantic anchors
   grepped in HEAD source. `evidence/06_knowledge_hygiene.json`.

## 2. Headline numbers

```text
ARCHIVES (unique, incl. zero-byte):            20  (23 on-disk copies deduped by SHA256)
  - ZIPs: 14 (12 non-empty + 2 zero-byte) + 2 zero-byte temp ZIPs
  - git bundles: 4
GIT-BEARING ARTIFACTS INSPECTED:               15/15  (11 ZIP repos + 4 bundle clones)
FILES EXTRACTED & INVENTORIED:                 11,764 (12 ZIPs) + 4 bundle HEAD-tree inventories
HEAD-TREE FILE VERSIONS COMPARED (path+blob):  9,392 across 11 repos (A-04: 1014/1014 byte-exact)
BUNDLE TREES COMPARED:                         4 (1,014 / 981 / 981 / 981 files)
CANONICAL OBJECT DB:                           8,865 objects (5,231 blobs, 365 commits, 3,262 trees, 7 tags)
UNIQUE HISTORICAL OBJECTS:                     A-10: 8 commits + 4 tags + 35 trees + 17 blobs; A-18: 1 tag
UNIQUE HISTORICAL IMPLEMENTATIONS (source):    2 blobs — BOTH proven present in canonical HEAD
POTENTIAL LOST FIXES:                          1 candidate (UNIFIED_011.2 FNA-FIX) → NOT LOST
UNTRACKED HISTORICAL CHANGES:                  305 files — 0 source files (all runtime logs/artifacts)
REVERTED FIXES:                                0
KNOWLEDGE/SOURCE MISMATCHES:                   0 open (50/50 ledger rows verified at HEAD)
CORRUPT ARCHIVES:                              4 zero-byte ZIPs (recorded CORRUPT_EMPTY)
OVERSIZED/NON-SOURCE IN FINAL CANONICAL ZIP:   0 APK/AAB/PPM/SO/JAR/class/node_modules/gradle
CANONICAL SOURCE MODIFIED BY THIS AUDIT:       NO
PUSHED:                                        NO (remote re-verified at bbe0ce3 during this pass)
```

## 3. What the differential proved

1. **Canonical handoff ZIP (A-04) is byte-exact** against canonical HEAD tree (1014/1014 same
   blobs, 0 unique objects, 0 untracked-unknown files).
2. **Every archive HEAD is an ancestor of canonical HEAD** and **every archive's tracked-file
   content is contained in the canonical object DB** (unique-object diff = 0 everywhere except
   A-10/A-18 below). Consequently no archive holds any tracked source version that canonical
   lacks — the classic "file differs" deltas are pure ancestor-version evolution, with canonical
   holding the full version chain.
3. **A-10 (v0.11.3 original shallow repo) is the only archive with content unknown to canonical**:
   git-stash captures from the UNIFIED_002/007/011 era + 4 original annotated tag objects.
   Function-level forensics of its two source-code variants:
   - `dalvik_engine.cpp` (blob 195e88c): contains the UNIFIED_011.2 FILLED_NEW_ARRAY fix —
     **present verbatim at canonical HEAD line 6530** (`fna_regs[5]` block, identical comments).
   - `android_shadows.cpp` (blob dfb6c581): strictly OLDER than canonical HEAD (HEAD carries the
     CAMPAIGN-010-R14 `getStackTrace` fix and the CAMPAIGN-013 inverted inflate policy; the stash
     holds the pre-R14 `handled_null()` and the weak-tree guard that HEAD deliberately replaced).
4. **The 12 source files from the UNIFIED_007 untracked stash are byte-for-byte IN canonical**
   (arsc_parser, axml_parser, layout_inflater, resource_runtime ×.cpp/.h + 4 test tools) — the
   "recovered work" was fully committed downstream.
5. **No reverted fix exists**: no archive blob and no unreachable canonical blob contains code that
   canonical HEAD lacks, except the two items above which are superseded intermediates of code
   that IS at HEAD.
6. **Zero-byte ZIPs** (FULL_VALIDATION@6c9a91e, v0.14.0, handoff, handoff2) recorded as
   CORRUPT_EMPTY — their intended content is separately represented (A-09, A-14).
7. **Untracked-but-unknown files** in the rebuilt version ZIPs (34×6) and the review ZIP (101) are
   runtime logs/evidence only — none is source, config, or test.
8. **A-18's single unique object** is the `pre-integration-github-baseline` annotated tag
   (metadata; target commit bbe0ce3 is canonical's own remote baseline).

## 4. §7 targeted historical areas — how they were covered

The named areas (opcode table/lit8/lit16/12x/35c/3rc/switch/invoke/exceptions/conversions; String/
parse/XmlPullParser/AtomicReference/InputStream bridges; View/inflation/onDraw/event dispatch;
ARSC/resources; rendering/APK pipeline) were covered by the combination of:
- **blob-universe containment**: any historical variant of any of those files, if it exists in any
  surviving archive, must appear as a blob in the archive's object set — all such sets were
  diffed against canonical; the only non-contained variants are the two analyzed in §3.3;
- **function-level reading** of those two variants (FNA decode function; setContentView/getStackTrace
  functions);
- **HEAD semantic anchors**: `div-int/lit8` (3 hits), `XmlPullParserException` (5), `compareAndSet`
  (3), `available()` (7), `NumberFormatException` (7), `Infinity` (4) — grep-proven present at HEAD;
- **ledger + fixtures**: pass-3 fixture files and the RESULT_001/009/010/12x tests exist at HEAD
  (`tests/semantic_pass3_bridge_test.cpp`, `semantic_long_cmp_conv_test.cpp`,
  `semantic_switch_parse_neg_test.cpp` — all present, 144/144 recorded green at Pass-3).

## 5. Final verdict

```text
SOURCE FORENSICS: PASS

Every discovered source archive was independently inspected (20/20; 4 zero-byte recorded, skipped
for cause only); every .git inspected (15/15 incl. bundles); every tracked source file compared at
blob-SHA level with rename/move detection; function/class-level analysis performed on the only two
unique source variants in existence; Git-only and ZIP-only changes investigated (stash families,
reflog-only commits, unreachable objects on BOTH sides); reverted/lost fixes investigated (1
candidate → resolved present-at-HEAD); knowledge crosschecked against source (50/50 rows; byte-level
doc identity for the pass-3 report); all 20 archives carry explicit statuses; all unresolved
differences are listed (none requires source integration; two optional metadata-level actions:
SRC-010 tag resurrection, SRC-020 filebin parity upload).

Previous OMISSION AUDIT (Pass-3) was NOT used as evidence here; this verdict rests solely on this
pass's own independent extraction, hashing, object-set arithmetic, and function-level reading.
```

## 6. Items requiring a future integration/validation decision

| # | Item | Type | Recommendation |
|---|------|------|----------------|
| 1 | SRC-010 `pre-integration-github-baseline` tag object (A-18 only) | metadata | optional: recreate tag in canonical (points at bbe0ce3; zero risk, no source change) |
| 2 | SRC-020 A-18 bundle missing from filebin mirror | availability | optional: upload for remote parity |
| 3 | SRC-017 campaign-014 raw logs (untracked in 7 archives) | evidence | keep OUT of canonical (hygiene); retrievable from A-01/A-06 on demand |
| 4 | SRC-021 destroyed UNIFIED_000–011 container ZIPs | provenance | permanent BLOCKED record — compensating controls verified; nothing further actionable |

No source-code integration candidates exist. Nothing in any historical archive is missing from
canonical.
