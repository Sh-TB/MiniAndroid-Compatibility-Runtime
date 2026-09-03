# MASTER SOURCE DIFFERENTIAL LEDGER
Generated: 2026-09-03 · Canonical: `Sh-TB/MiniAndroid-Compatibility-Runtime`, branch
`integration/master-reconciliation`, HEAD **f7144209aecc4a4adf991c86e0d16dadea62a68e** (362 commits).
Every discovered cross-archive difference receives a stable forensic ID. Evidence JSONs:
`evidence/04_content_differential.json`, `evidence/05_deep_dive.json`, patches in
`evidence/patches/` (raw), blob extracts in `evidence/A10_unique_blobs/` (raw).

Statuses: ALREADY_IN_CANONICAL / MISSING_FROM_CANONICAL / PARTIALLY_PRESENT / SUPERSEDED /
DUPLICATE / REJECTED_WITH_EVIDENCE / NEEDS_VALIDATION / BLOCKED / HISTORICAL_ONLY.

---

## SRC-001 · UNIFIED_011.2 FNA-FIX stash (the one §9 candidate) — **ALREADY_IN_CANONICAL**
* **archive**: A-10 (v0.11.3 original shallow repo), stash commit `321794dc` "On main: temp-fna-fix"
  (parent 340a9cf = v0.11.1; parent-in-canonical: YES), content blob `195e88c810b6`
  (dalvik_engine.cpp, 646,069 bytes — NOT in canonical object DB).
* **what changed**: `fetch_decode` FILLED_NEW_ARRAY (format 35c) extraction. Old: `arg_count =
  (bytecode_[pc_]>>4)&0x0F` (constant 2 for opcode 0x24; 5th register G never read). New: `arg_count
  = (instr0>>12)&0x0F`, C/D/E/F from cu2 nibbles, G from `(instr0>>8)&0xF` — comment cites
  "UNIFIED_011.2 FNA-FIX (§24 audit)" and EXP-037 BLOCKER-016.
* **canonical status**: **PRESENT AT HEAD VERBATIM** — `miniandroid/src/dex/dalvik_engine.cpp`
  line 6530+: identical `fna_regs[5]` block, same comments. The stash was later applied and
  committed; only the intermediate blob object is unique to A-10.
* **validation**: byte-level code comparison of the stash patch vs HEAD source (this pass).
* **action recommendation**: none (no integration). Preserve A-10 as provenance artifact.

## SRC-002 · UNIFIED_007 resource-pipeline untracked stash — **ALREADY_IN_CANONICAL**
* **archive**: A-10, stash commit `aae02cdc` "untracked files on main: 8f0a85b" (no parent —
  untracked-only stash).
* **what changed**: 12 SOURCE files captured while untracked: `arsc_parser.cpp/.h`,
  `axml_parser.cpp/.h`, `layout_inflater.cpp/.h`, `resource_runtime.cpp/.h`,
  `tests/tools/arsc_tool.cpp`, `axml_tool.cpp`, `resolve_debug.cpp`, `zip_reader.h`
  (incl. 645-line arsc_parser.cpp with AOSP-verified `complex_to_float`).
* **canonical status**: all 12 blobs verified IN canonical object DB (`cat-file -e` each).
  HEAD `android_shadows.cpp` line 8 includes `../resources/resource_runtime.h`; the real-inflation
  path (`[U007-INFLATE]`) is live at HEAD line 898.
* **action recommendation**: none.

## SRC-003 · UNIFIED_007 worktree stash — **SUPERSEDED**
* **archive**: A-10, stash commit `edac6a6d` "On main: UNIFIED_007 resource pipeline (recovered
  work)" (merge of 8f0a85b + index 043228a1 + untracked aae02cdc).
* **difference**: worktree-state diff (exp096 evidence PNG deletions + WIP of the same pipeline);
  the source content is exactly SRC-002.
* **action**: none.

## SRC-004 · WIP stash (runtime data) — **HISTORICAL_ONLY**
* **archive**: A-10, `d8726168` (+ its index `d2b6089d`).
* **difference**: touches only `miniandroid/runtime/data/org.telegram.messenger/shared_prefs/
  default.xml` (2 blobs `76e5975b91fe`, `47d33413eefb` — runtime prefs noise).
* **action**: none (not source).

## SRC-005 · Empty index stashes — **DUPLICATE**
* **archive**: A-10, `043228a1` + `0aab25aa` ("index on main: …").
* **difference**: index == HEAD at stash time → empty diffs. No content.
* **action**: none.

## SRC-006 · Superseded consistency commit — **SUPERSEDED**
* **archive**: A-10, branch `archive/011-superseded-consistency` → `313ed5cc` "UNIFIED_011 (§45):
  final consistency pass — HEAD 937f043, 59 commits, 9 ahead".
* **difference**: doc-state updates only (see SRC-007 doc variants). 937f043 itself IS in canonical.
* **action**: none.

## SRC-007 · The 17 unique A-10 blobs — itemized
| Blob | Path | Size | Classification | Evidence |
|------|------|-----:|----------------|----------|
| `195e88c810b6` | src/dex/dalvik_engine.cpp | 646,069 | **ALREADY_IN_CANONICAL** (FNA-FIX at HEAD:6530) | SRC-001 |
| `dfb6c58198a4` | src/framework/android_shadows.cpp | 69,700 | **ALREADY_IN_CANONICAL (superseded intermediate)** | see below |
| `6896b88e3f34` | Makefile | 6,503 | SUPERSEDED — U007 `FONTS_LIBS` + RESOURCES_SOURCES present at HEAD Makefile:15/28 (canonical even adds res_config.cpp) | diff reviewed |
| `6ba1c1b00277` | .gitignore | 1,006 | SUPERSEDED — canonical = same + `miniandroid/run/u0113_*/` line | diff reviewed |
| `46d6d3851b07` | status.json | 2,285 | SUPERSEDED doc snapshot (UNIFIED_011 vs 011.1 state) | diff reviewed |
| `9a5d236ffa4f` | START_HERE.md | 2,228 | SUPERSEDED doc snapshot | diff reviewed |
| `4d521892ee4e` | README.md | 4,852 | SUPERSEDED doc snapshot | diff reviewed |
| `f16d3c2c2e09` | MASTER_CHANGELOG_KNOWLEDGE_011.md | 10,914 | SUPERSEDED doc snapshot (1 line) | diff reviewed |
| `3aff1e07cc56` | MASTER_PROJECT_STATE_011.md | 8,719 | SUPERSEDED doc snapshot | diff reviewed |
| `9f251137ea29` | RELEASE_NOTES_UNIFIED_011.md | 3,361 | SUPERSEDED doc snapshot (1 line) | diff reviewed |
| `76e5975b91fe` | runtime/data/…/default.xml | 843 | HISTORICAL_ONLY runtime data | — |
| `47d33413eefb` | runtime/data/…/default.xml | 843 | HISTORICAL_ONLY runtime data | — |
| `3645af00230e` | robolectric target/…/createdFiles.lst | 33 | HISTORICAL_ONLY build artifact | hygiene |
| `90f9ca7b0ab5` | robolectric target/…/inputFiles.lst | 107 | HISTORICAL_ONLY build artifact | hygiene |
| `52b1fca233d7` | robolectric target/…/TEST-…xml | 16,015 | HISTORICAL_ONLY build artifact | hygiene |
| `98a81c3faab6` | robolectric target/…/oracle…txt | 302 | HISTORICAL_ONLY build artifact | hygiene |
| `82250ae3deed` | robolectric target/test-classes/….class | 7,587 | HISTORICAL_ONLY build artifact | hygiene |

**`dfb6c58198a4` deep-dive (50-line total diff vs HEAD, 2 hunks):** the stash version holds the
OLDER `getStackTrace` shadow (`return CallResult::handled_null();` — EXP-043 era) where HEAD holds
the CAMPAIGN-010-R14 recovered fix (`return CallResult::not_handled();` — real interpreter frames,
dooz livelock fix), and the OLDER weak-tree guard where HEAD holds the CAMPAIGN-013 "B5-class
inverted policy" (`substantive = root_id != 0` + legacy fallback logging). **HEAD is a strict
semantic superset; nothing in the stash is missing from canonical.**

## SRC-008 · 4 original annotated tag objects — **HISTORICAL_ONLY (metadata)**
* **archive**: A-10. Tag objects `a9ad7109 / 7a814d8a / ea5d4554 / 4b8a80e3` for names
  v0.11-unified-011 / v0.11.1-… / v0.11.2-… / v0.11.3-…, pointing at commits f45505d0 / 313ed5cc /
  937f043 / 78bad823 with the ORIGINAL pre-rebuild messages ("UNIFIED_011_CANONICAL — recovery
  release…" etc.).
* **canonical status**: canonical holds same tag NAMES (recreated objects) and all 4 target commits.
  Zero source delta. **No tag exists in any archive that canonical lacks by name** (verified for
  every archive: `tags_not_in_canonical = []`).

## SRC-009 · 3 stash-capture branches in A-10 — **HISTORICAL_ONLY refs**
* `archive/011-stash-runtime-noise` (d8726168), `archive/011-stash-unified007` (edac6a6d),
  `archive/011-superseded-consistency` (313ed5cc). These refs are WHY the stash objects survived.
  Content closed by SRC-001…SRC-006.

## SRC-010 · A-18 unique object: `pre-integration-github-baseline` tag — **HISTORICAL_ONLY (metadata)**
* **archive**: A-18 BACKUP_GITHUB_MASTER_FULL.bundle; tag object `100e36ee43c9` → bbe0ce3, message
  "Exact live GitHub master state before integration (bbe0ce3)".
* **canonical status**: points at bbe0ce3 (in canonical); the tag NAME is not in canonical's tag
  list. Optional (harmless) resurrection candidate — no source content involved.

## SRC-011…SRC-014 · Four zero-byte ZIPs — **BLOCKED (CORRUPT_EMPTY, recorded)**
* SRC-011 A-05 `MiniAndroid_FULL_VALIDATION_HANDOFF_6c9a91e.zip`; SRC-012 A-13
  `MiniAndroid_v0.14.0_GIT_HANDOFF.zip`; SRC-013/A-14 A-15+A-16 `temp_files/handoff.zip`,
  `handoff2.zip`. SHA256 of each = e3b0c44298fc… (empty). Never silently dropped; every downstream
  report since Pass-1 records the interruption that produced them. Their intended content is
  otherwise represented (v0.11.2 = 6c9a91e exists as A-09; v0.14.0 partial = 894eae2 exists as A-14).

## SRC-015 · Reflog-only commit b5d2140 (A-03/A-06 reflogs) — **ALREADY_IN_CANONICAL**
* Docs-only draft superseded by its own amend; its OBJECTS are inside the canonical object DB
  (archive-vs-canonical unique-object diff = 0 for A-03/A-06). Reflog counts: A-03 30, A-06 21.

## SRC-016 · Canonical's own unreachable stash commits — **ALREADY_IN_CANONICAL (metadata only)**
* `3895fe18` "index on integration/master-reconciliation: 272f216 …" and `b8dab034`
  "On integration/master-reconciliation: pass3-fixes-for-before-evidence" (2026-09-03 00:59) + 3
  private trees, left unreachable when the Pass-3 stash was cleared. Every BLOB reachable from those
  stash commits is reachable from HEAD (0 unique blobs — verified via `rev-list --objects` set
  difference). Only stash-commit/tree metadata is unreachable. Canonical fsck reports exactly these
  5 diagnostics; no dangling blobs.

## SRC-017 · 34 campaign-014 raw runtime logs (untracked in A-01/A-06…A-14 rebuilt ZIPs) — **HISTORICAL_ONLY**
* docs/campaign014_evidence/<app>/{crash.log, run.log, click/run.log, click/crash.log} — sizes
  169 B – 620 KB. Not committed anywhere (canonical's committed campaign014_evidence is the curated
  subset). Recommendation: keep out of canonical per hygiene policy (huge runtime logs); content
  remains retrievable from A-01/A-06 if ever needed.

## SRC-018 · 67 `miniandroid/run/*` runtime artifacts untracked in A-06 — **HISTORICAL_ONLY**
* Screenshots/traces at packaging time; not source; not committed; no action.

## SRC-019 · filebin knowledge/manifest docs (11 files) — **ACCOUNTED**
* `MASTER_RECONCILIATION_PASS3_REPORT.md` (11,317 B) — **byte-identical** to repo
  `PASS3_FINAL_REPORT.md` at HEAD.
* `MASTER_RECONCILIATION_FINAL_REPORT.md` (17,375 B) — Pass-2-era final report (historical knowledge;
  superseded by PASS3 docs; preserved on filebin).
* 8 SHA256 manifests / delivery records / PHASE9 git record — bookkeeping only, no source claims
  beyond what the ledgers already carry.

## SRC-020 · BACKUP_GITHUB_MASTER_FULL.bundle not mirrored on filebin — **INVENTORY NOTE**
* Local-only (152,704,964 B, SHA256 b0578280b39f…). Same bbe0ce3 history as A-19 plus the
  baseline tag object. Optional: upload to filebin for parity.

## SRC-021 · UNIFIED_000…011 + legacy coder-2 original container archives — **BLOCKED (not on disk)**
* The original UNIFIED_000–011 ZIPs and legacy coder-2 workspaces were consumed in earlier
  campaigns and no longer exist as containers. Compensating controls (verified this pass):
  (a) their unified product lineage is fully on disk (A-07…A-11 with embedded unified .git);
  (b) the uncommitted/stash-era content from the UNIFIED_002/007/011.1/011.2 era was located in
  A-10 and closed item-by-item (SRC-001…SRC-006); (c) every blob in every surviving archive is
  inside the canonical object DB. Any *unrecorded* fix that existed ONLY inside a destroyed
  UNIFIED container and was never committed/stashed into the surviving lineage is unrecoverable by
  definition — but the stash audit shows even transient work was captured, so no gap is evidenced.

---

## Summary counts
| Metric | Value |
|---|---|
| Ledger entries | 21 (SRC-001…SRC-021) |
| MISSING_FROM_CANONICAL | **0** |
| PARTIALLY_PRESENT | 0 |
| REJECTED_WITH_EVIDENCE | 0 |
| NEEDS_VALIDATION | 0 |
| ALREADY_IN_CANONICAL (incl. superseded intermediates) | SRC-001, SRC-002, SRC-015, SRC-016 (+2 blobs in SRC-007) |
| SUPERSEDED | SRC-003, SRC-006, 8 blobs (SRC-007) |
| DUPLICATE | SRC-005 |
| HISTORICAL_ONLY | SRC-004, SRC-008, SRC-009, SRC-010, SRC-017, SRC-018, SRC-019, SRC-020 |
| BLOCKED | SRC-011…SRC-014, SRC-021 |
| Items requiring a future integration decision | **0** (only optional: SRC-010 tag resurrection, SRC-020 filebin parity upload — both metadata-level) |
