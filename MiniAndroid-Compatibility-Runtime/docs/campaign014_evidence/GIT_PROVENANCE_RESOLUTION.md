# GIT PROVENANCE — final resolution (2026-09-02)

| claim (old reports) | verified reality |
|---|---|
| `f5da664` = `v0.12.0` (Campaign 012 report) | **ABSENT everywhere**: not in local DAG, not in surviving ZIPs, `git ls-remote` shows remote only at `bbe0ce3/refs/heads/main`. Status: UNKNOWN (never materialized in any recoverable artifact). |
| Campaign 012 never executed separately | tag `campaign-012-baseline` = `ea81e00` = `v0.11.3-unified-011-3` = `v0.13.0-baseline` (three tags, one commit) |
| `CAMPAIGN FINAL-GAP-RECONCILIATION-011.4` | tag `v0.11.4-fix-01` (annotated) — delivered as its own ZIP |
| full history | lineage is **shallow at `a9434de`**; 121 commits recoverable above the boundary; below-boundary EXP-era history unrecoverable |

Evidence commands: `git fsck` (clean), `git rev-parse <tag>^{commit}` (all 8 resolve), `git ls-remote` (2026-09-02).
