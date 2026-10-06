# External Root Knowledge Base — MANIFEST

This file is the stable on-repo pointer for the CONT-6 external root
knowledge base (Issue #377 artifact-access contract). The KB is a
**discovery/searchlight artifact** — it is NEVER merged into
`root_registry.json` as a whole and never promoted source-only.

## Snapshot history (never delete rows; append per future snapshot)

| Snapshot        | SHA-256 (archive zip)                                            | Records | VERIFIED-NEW | Audited HEAD | Local artifact |
|-----------------|------------------------------------------------------------------|---------|--------------|--------------|----------------|
| 2026-10-05 FINAL v3 (contract row from Issue #377) | `d717e9c745609fdf3ca11eb5d60649910089c9e2ca1d2ad942c22f4712ad7931` | 5976 | 5434 | `f8d4088b` | **ABSENT-THIS-CONTAINER** |
| 2026-10-06 CONT-7 W3 verification run | `d717e9c745609fdf3ca11eb5d60649910089c9e2ca1d2ad942c22f4712ad7931` (contract row; byte-verification NOT possible) | 5976 (contract) | 5434 (contract) | `f8d4088b` (contract) | ABSENT-THIS-CONTAINER |

## 2026-10-06 verification status (CONT-7 WAVE 3 / CONT-6 execution)

* **Snapshot consumed this run: NONE.** The archive
  `MiniAndroid_Root_Audit_Archive (1).zip`
  (SHA-256 `d717e9c745609fdf3ca11eb5d60649910089c9e2ca1d2ad942c22f4712ad7931`,
  2,171,810 bytes) is **not present in the current container** (post-reset
  loss; only the Issue #377 contract text survives). Per the Issue's
  snapshot protocol the coder must print the exact snapshot SHA consumed —
  the honest print is: **no archive bytes were readable, no per-record
  classification (Phase 1) or clustering (Phase 2) of the 5,976 rows was
  performed this run.** No fabricated counts are reported anywhere.
* What WAS verified this run (from the contract text itself, with
  reasoning, see `evidence/cont6/CONT6_FINAL_TABLE.md`):
  internal-consistency reasoning about the audit's label arithmetic and
  the "5,434 records != 5,434 roots" cluster claim; the six-game
  REAL_APP_CONTENT claim was **independently re-validated at current HEAD
  with real runtime runs** (Phase 4) — see the six-game verdict file.
* The archive must be **re-supplied** (re-attached to Issue #377 or
  dropped into this directory) before Phases 1/2/3 (forensic
  reconciliation, semantic clustering, cluster-prioritized fan-out
  selection) can run against bytes. This wave ran the runtime side
  (Phase 4 + Phase 5 on locally proven roots) instead of skipping
  CONT-6 entirely.

## Hard rules (from Issue #377, honored by every future run)

1. Never paste the 6.5 MB JSONL into the Issue; keep the archive as an
   artifact at this path with this manifest.
2. Never merge the 5,434 findings into the runtime registry merely
   because they exist in the KB.
3. Future snapshots replace only the KB artifact + manifest; the Issue
   remains the stable audit contract; keep old snapshot hashes above.
4. Per-run printout: exact snapshot SHA consumed (or honest ABSENT).
5. Only C/D-class (missing-sub-law / genuinely-new) candidates may enter
   `root_registry.json`, after full registry search + evidence-history
   search + current-HEAD check + semantic-duplicate check, with external
   provenance AND separate runtime proof.
