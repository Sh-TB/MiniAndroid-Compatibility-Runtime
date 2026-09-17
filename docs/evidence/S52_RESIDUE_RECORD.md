# S52 Residue Removal Record (tree-only; git history retains everything)

Campaign: S52 professionalization (evidence policy hard-gate).
Rule: every removed file is recoverable from git history at the recorded path;
SHA256 recorded below; small reproducible summaries stay in the tree.
All removals are plain commits — NO history rewrite performed in S52.

## Class 1 — Raw trace/log artifacts (policy §1: no raw runtime output in git)

| Path | Size | SHA256-16 |
|---|---|---|
| docs/evidence/campaign3_chessclock_real_screenshot/screenshot.ppm | 6,075 KB | (see SHA256SUMS) |
| docs/evidence/campaign014/**/api_trace.json (33 files) | 7,688 KB total | (see SHA256SUMS) |
| docs/evidence/s22_f076_f077/r2_pre_fix_trace.txt | 373 KB | (see SHA256SUMS) |
| docs/evidence/s22_f076_f077/r7_post_fix_trace.txt | 305 KB | (see SHA256SUMS) |

Rationale: raw API-call traces and raw raster dumps = forbidden artifact class
from S52 onward. The campaign014/campaign3 REPORTS that referenced them remain;
their conclusions are preserved in report form. `miniandroid/golden/expected_api_trace.json`
is a test ORACLE fixture (not a trace dump) and was intentionally KEPT.
Full SHA256 of every removed file: `docs/evidence/S52_RESIDUE_SHA256SUMS.txt`.

## Class 2 — Extracted-APK residue (policy §11: no extracted APK trees in source tree)

| Path | Files | Rationale |
|---|---|---|
| corpus_cache/dooz23_extracted/** | 93 | Full META-INF + resources tree extracted from dooz_23.apk. Provenance: extracted once for dooz23 DI/composition research (S24-era). The APK itself is at the external cache (`io.github.yamin8000.dooz_23.apk`, SHA256 84c9e46b1de7e86d...); extraction is reproducible. Library version facts survive in `docs/runtime/knowledge/` and the AAR/META-INF version list is re-derivable via the ASC/androguard toolchain. |

`corpus_cache/` itself remains as the (now empty) external-corpus cache anchor
named by APK_REGISTRY.json's zero-APK policy.

## Class 3 — Web-scrape raw caches (policy §1: cache/dump class)

| Path | Size |
|---|---|
| docs/runtime/research/raw/androguard_github.json | 367 KB |
| docs/runtime/research/raw/android_bytecode_doc.json | 419 KB |
| docs/runtime/research/raw/dalivm_github.json | 456 KB |

Rationale: raw scraped JSON caches used once as research INPUT; the distilled
research conclusions live in docs/runtime/knowledge/ and docs/research/.
Re-scrape commands are in the research docs that cited them.

## Totals

- Files removed from tree: 130 (93 residue tree + 34 traces + 1 ppm + 2 s22 traces + 3 raw = 133; minus none) — see commit.
- Tree bytes freed: ~17.5 MB.
- History: unchanged (no rewrite); every file remains reachable in pre-S52 commits.
- Recoverable: `git log --diff-filter=D --oneline -- <path>` → `git checkout <pre-commit> -- <path>`.
