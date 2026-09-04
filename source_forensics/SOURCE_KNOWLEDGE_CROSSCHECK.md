# SOURCE KNOWLEDGE CROSSCHECK
Date: 2026-09-03 · Chain verified per claim: **KNOWLEDGE CLAIM → ARCHIVE SOURCE → GIT HISTORY →
CURRENT SOURCE → CURRENT TEST → CURRENT RUNTIME EVIDENCE**

## 1. Ledger verification (KNOWLEDGE_LEDGER.csv @ HEAD — 50 rows)

```text
VERIFIED_IMPLEMENTED                22
VERIFIED_MISSING                    11  (9 fixed in Pass-3 K-34..K-42 + historical-missing rows kept for provenance)
VERIFIED_MISSING→fixed rows marked   9  (K-34 InputStream, K-35 XmlPullParser, K-36 AtomicReference,
                                        K-37 lit8 table, K-38 lit16 nibbles, K-39 new-array length,
                                        K-40 typed array elements, K-41 parseInt boundary, K-42 NaN/Infinity)
PARTIALLY VERIFIED                   1  (RESULT_014 Canvas matrix composition — open, documented in NOT_DONE)
REJECTED_WITH_EVIDENCE               2  (TOOL-CLAIM-4A39F1B; f5da664/"v0.12.0" — both with evidence chains)
SUPERSEDED_BY_LATER_FIX              1  (Pass-2 K-31 "AOSP-correct lit8" — corrected by K-37, provenance kept)
BLOCKED_BY_MISSING_ARTIFACT          5  (campaign-014 code, Telegram golden APK, droidify.apk, 2 zero-byte ZIPs)
DUPLICATE                            4  (gap-matrix dedups, provenance preserved)
NEEDS_RUNTIME_PROOF                  3  (Compose hook, GLES hook, geometry/fonts/audio boundaries)
```

Every `.cpp/.h/.md/.py/.json/.txt/.csv` path referenced by any ledger row was probed in the HEAD
tree: **0 missing** (`evidence/06_knowledge_hygiene.json → ledger_referenced_paths_missing_at_HEAD: []`).

## 2. Claim → implementation → verification chains re-verified at HEAD

| Claim | Archive/git source | Current source (HEAD f714420) | Current test | Runtime evidence |
|---|---|---|---|---|
| RESULT_001 long 64-bit (2^32+1 ≠ 1) | UNIFIED lineage | `dalvik_engine.{h,cpp}` 64-bit ops | `semantic_long_cmp_conv_test.cpp` (present) | 14/14 pass-3 record |
| RESULT_009 cmp-long −1/0/+1 | UNIFIED lineage | cmp-long 3-branch dispatch | same fixture | 3 cases pass |
| RESULT_010 numeric conversions (NaN/±Inf/trunc) | UNIFIED lineage | bits_l2d/conv_f2i/conv_f2l helpers | same fixture | 14/14 incl. 2^53 |
| 12x nibble decode | UNIFIED lineage | decoder distinct-register path | pass3 fixture 12x cases | reversed-nibble would fail |
| UNIFIED_011.2 FNA-FIX (35c arg_count/G-reg) | **A-10 stash 321794dc (unique blob 195e88c)** | **dalvik_engine.cpp:6530 verbatim** | pass3 + legacy suites | goldens byte-stable |
| UNIFIED_007 resource pipeline | **A-10 stash aae02cdc (12 source blobs)** | android_shadows.cpp:8 (`resource_runtime.h`), :898 (`U007-INFLATE`) | ARSC probe 3/3 (pass-3) | real-APK layouts |
| K-34 InputStream real bytes | Pass-3 commit ada6f4b | `available()` ×7 in src | pass3 ST group | 5/5 vs unzip oracle |
| K-35 XmlPullParser event machine | Pass-3 | `XmlPullParserException` ×5 | pass3 X group 7/7 | event-packing 224331 |
| K-36 AtomicReference identity CAS | Pass-3 | `compareAndSet` ×3 | pass3 AR group 7/7 | discriminator |
| K-37/K-38 opcode table | Pass-3 (supersedes Pass-2 K-31) | `div-int/lit8` ×3 anchors | PASS3_OPCODE_AUDIT.md (present) | 0 semantic shifts vs AOSP ref |
| K-41/K-42 parse boundaries | Pass-3 | `NumberFormatException` ×7, `Infinity` ×4 | pass3 PS group | boundary matrix |
| Packed/sparse-switch, div/rem÷0, neg/not | Pass-2 9d095f9 | dispatch + deferred throw | semantic_switch_parse_neg_test.cpp (present) | 25/25 + typed-catch 8/8 |

**Mismatch classes checked (all 7 from the audit spec):**
1. knowledge claim with no source implementation → **0** (all VERIFIED rows have anchors at HEAD);
2. source implementation with no knowledge record → **0** found (A-10's two unique variants map to
   documented UNIFIED_011.2/007 work; no undocumented behavior found in any archive);
3. Git change with no knowledge record → **2 metadata-level items found and now recorded**
   (SRC-008/SRC-010 original tag objects; SRC-016 canonical stash metadata) — no source content;
4. knowledge claim describing a different implementation → **0** (the one historical instance —
   Pass-2's K-31 lit8 claim — was already superseded by K-37 in Pass-3 with full provenance;
   ledger state SUPERSEDED_BY_LATER_FIX verified);
5. later source correction missing from knowledge → **0** (pass-3 fixes all in ledger + docs);
6. historical fix incorrectly marked implemented → **0** (REJECTED/BLOCKED states used where
   evidence was absent: f5da664 verdict, droidify, Telegram golden);
7. implementation existing but never independently verified → tracked as NEEDS_RUNTIME_PROOF
   (3 rows) + PARTIALLY VERIFIED (1 row) — correctly NOT marked implemented.

## 3. Archive-source ↔ knowledge cross-map

* **A-02 (campaign-013 reports bundle, 13 docs)**: all 13 files exist inside the canonical repo
  (crosschecked during Pass-3 archive scan; content = campaign-013 worklog/reconciliation docs).
* **filebin knowledge docs**: `MASTER_RECONCILIATION_PASS3_REPORT.md` = **byte-identical** to repo
  `PASS3_FINAL_REPORT.md` (11,317 B, SHA-verified download). `MASTER_RECONCILIATION_FINAL_REPORT.md`
  (17,375 B) = Pass-2-era report — historical knowledge, preserved remotely; its claims were
  superseded by Pass-3 documents, not lost.
* **Doc snapshots unique to A-10** (6 variants): diffs reviewed line-by-line — they differ ONLY in
  UNIFIED_011 vs UNIFIED_011.1 status numbers (commit counts, tag names, dates). **Zero unique
  technical knowledge.**
* **NOT_DONE.md @ HEAD** (11 open items) — consistent with ledger BLOCKED/NEEDS_RUNTIME_PROOF rows;
  nothing marked done in knowledge while missing in source, and vice versa.
* **VERIFIED_TESTS.md @ HEAD** — documents rebuild/re-run of every protecting test; fixtures all
  present at HEAD (see §2).

## 4. Result

```text
KNOWLEDGE/SOURCE MISMATCHES: 0 open
Metadata-only git artifacts without prior knowledge record: 2 (now recorded: SRC-008, SRC-010)
Claims verified end-to-end this pass (claim→source→git→HEAD→test→evidence): 13 rows in §2
Ledger rows fully consistent with HEAD tree: 50/50
```
