# FINAL_STATE — canonical end-of-integration state (2026-09-02)

Branch: `integration/master-reconciliation` — final HEAD recorded in
MAIN_CODER_INTEGRATION.md. GitHub master untouched (`bbe0ce3`).
Status: **PUSH_BLOCKED_PENDING_USER_REVIEW**.

## What this state is

- Working tree = v0.13.0 lineage + campaign-014 evidence branch + master-reconciliation
  work: full 353-commit history re-unified from the GitHub master (was shallow),
  Dalvik semantic core verified + fixed with a discriminating fixture, zero
  regression against all goldens, README rewritten, knowledge indexed.
- Runtime: deterministic Telegram-journey-class execution; SimpleStopwatch golden
  pixel-exact (`2a12587a`); gmdice/unote/dooz/microtimer running with byte-stable
  outputs; ARSC/AXML real resource pipeline; 95+ shadow classes; PNG/JPEG/WebP/Lottie.

## Metric snapshot (BEFORE → AFTER this integration)

| Metric | BEFORE (v0.13.0 tree) | AFTER (this branch) |
|---|---|---|
| Semantic long/cmp/conv fixture | — (did not exist) | **14/14 PASS** |
| Semantic correctness: long arith >2^32 | WRONG (32-bit wrap) | CORRECT (64-bit) |
| cmp-long INT64 operands | returned 0 | −1/0/+1 per spec |
| cmpl/cmpg NaN | 0 | −1 / +1 per spec |
| int-to-byte/char/short, float↔int/long | tag-only (wrong) | real conversions |
| simplestopwatch golden | 2a12587a | **2a12587a (unchanged)** |
| gmdice / microtimer / unote / dooz screenshots | 4fd3ce0e / eb16ab5c / d6b854c4 / 31ddd4d5 | **identical** |
| unified0112 / 0113 / F5 / handler / simple fixtures | 5/5, 8/8, 5/5, 23/23, 4/4 | **same, all pass** |
| Repository knowledge | shallow history, scattered | 353 commits unified + MASTER_PROJECT_KNOWLEDGE.md |
| f5da664/v0.12.0 question | open contradiction | closed with evidence (UNKNOWN/absent) |

## Intact guarantees

- GitHub master (`bbe0ce3`) untouched; no push performed; no history rewrite.
- Restore points: `BACKUP_GITHUB_MASTER_bbe0ce3.bundle` (+SHA256), local rescue branch.
- ZERO APK files committed; external-cache policy enforced.
