# MASTER_RECONCILIATION_011_1

**What was recovered, from where, and how it was verified** (§27). The
"what we have now" doc is `CODER_HANDOFF_011_1.md`; the per-claim map is
`docs/CROSS_CAMPAIGN_RECOVERY_011_1.md`; machine state is `status_011_1.json`.

## A. Recovery sources and yields

| # | Source | Yield | Verification |
|---|---|---|---|
| 1 | `/tmp/my-project/download/miniandroid_unified_campaign/UNIFIED_003.zip` | Campaign 003/004-era knowledge snapshot (289 members, 204 MD) | SHA256 match vs sidecar; diff: docs-only vs canonical |
| 2 | same, `UNIFIED_004.zip` | Campaign 004 knowledge (328 members, FILE_MANIFEST_004) | SHA match; docs-only |
| 3 | same, `UNIFIED_005.zip` | **audio engine + 3D tictactoe + stb_vorbis/minimp3 + EXP113/114/115 docs** (37 members) | SHA match; code diffed; lineage d6b4020 |
| 4 | same, `UNIFIED_006.zip` | font-shaping + Lottie prototypes (exp116/117), TASKS_CAMPAIGN005_MASTER | SHA match |
| 5 | same, `UNIFIED_007.zip` / `007_FINAL.zip` | resource-pipeline companions (text_shaper, view_renderer, real_layout, exp120/121/124), build scripts, logs (excluded by policy) | SHA match ×2 |
| 6 | same, `UNIFIED_008_FINAL.zip` | **src/audio (reduced), src/fonts/text_shaper, u007_job_server, fixtures, test_audio, 17 knowledge docs, u007 scripts, p1_mining dataset** | SHA match |
| 7 | same, `UNIFIED_009_FINAL.zip` | **res_config (ARSC config matching) + probe**, campaign009 16-doc knowledge set, APK matrices | SHA match; tar.gz extracted |
| 8 | same, `UNIFIED_010_FINAL.zip` | **Campaign 010 source: libpng renderer, dalvik stack traces, src/gles glue, stb, campaign009/010 knowledge, uc010 harnesses, 31-row registry** | SHA match; **full clean build + 8-APK matrix reproduced** |
| 9 | `/tmp/my-project/scripts/p1_mining/` (11 files) | Campaign 008 open-source mining dataset (119-candidate era: results.json, master_repos.txt, F-Droid index) | file census |
| 10 | git forensics on canonical repo | dangling stash/commit/tag objects identified and anchored in `archive/011-*` branches | `git fsck --full --no-reflogs`, reflog replay |
| 11 | `download/UNIFIED_011_backup/` bundle + 10 patches | Campaign 011 lineage already canonical; bundle re-verified | `git bundle verify` |
| 12 | `/tmp/my-project/tool-results/` read caches (10 files) | historical read snapshots — superseded by archives; retained only in forensics cache | none needed |

## B. Import decision record (§20 extract→diff→inspect→classify→selective import)

1. All 9 recovered source trees were diffed against canonical (`DIFFS/diff_UNIFIED_0XX.json`).
2. UNIFIED_010_FINAL identified as the **most-evolved verified source** (descends
   from 009 (4a2d39b) + 4 adoption commits; zero-regression evidence REGRESSION_010).
3. Standalone build of the 010 snapshot: SUCCESS; matrix run: byte-identical
   behavior to canonical on all 8 APKs (§19).
4. Merge rules applied: take 010 for evolved engine/renderer/arsc files; keep
   canonical Makefile clean-target + README + 011 guard; hand-merge
   android_shadows (R14 fall-through + guard); add res_config line to Makefile.
5. Campaign 005/006/007/008-only modules imported as **preserved code** at
   their original paths (not wired into default build — matches the 010
   reduced-tree decision, documented in CODE_REDUCTION_009/010).
6. Knowledge sets imported verbatim under `docs/knowledge/campaign00X/`
   (MASTER = current truth lives in 011.1 docs; HISTORICAL = originals kept).
7. Excluded: 15 APKs (007_FINAL), all logs >1MB, archive README/status
   snapshots, `test_media/`, evidence PNGs >100KB (none found in imports).

## C. Corrections to Campaign 011's own gradings (§6)

| Campaign 011 said | 011.1 found | Action |
|---|---|---|
| archives 003/004/006 NOT AVAILABLE | on disk in /tmp/my-project, SHA-valid | imported; gradings superseded (kept here for audit) |
| archives 005/008/009/010 conversation-level only | full source+evidence archives on disk | imported per map §4 |
| "libpng linked but not wired (R1 open)" | libpng IS the decoder+encoder in the 010 lineage; now in canonical default build | corrected; root cause = marker-scan path bug |
| "no GLES backend" | PortableGL glue exists and builds; golden-cube evidence verified | corrected to PARTIAL (dispatch hook open) |
| "no PortableGL / Yoga" | both present in 010 tree (bridge + adapter experiment) | corrected to ADOPTED(glue)/ADAPTER-READY |

## D. What remains UNAVAILABLE / UNVERIFIED (honest list)

- GitHub issues/PR metadata: API-limited in Campaign 011 → still NOT AVAILABLE.
- Push: no credentials → PUSH_PENDING (13 commits ahead of bbe0ce3 at 011.1 docs time).
- Campaign 003/004-era *source deltas* (EXP-103..110): archives are knowledge
  snapshots only; their code state was superseded by 005–010 lineages → no
  separate import possible (recorded, not invented).
- `UNIFIED_007_FINAL.zip` run logs: retained external-only (log policy).
- portablegl.h / libyogacore.a: not vendored (external upstream deps) —
  fetch commands documented in CODER_HANDOFF_011_1.md.
