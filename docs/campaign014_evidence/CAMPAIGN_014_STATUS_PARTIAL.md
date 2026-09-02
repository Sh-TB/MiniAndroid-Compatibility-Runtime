# CAMPAIGN 014 STATUS: PARTIAL

## Delivery identity
- BASE_COMMIT: `2ede367cc499b7c17e536062df200d347e6cbfbc` (tag `v0.13.0`, branch `campaign-013`)
- BRANCH: `campaign-014` (created from base)
- CAMPAIGN_END_COMMIT: this commit (tag `v0.14.0-partial`)
- FINAL_TAG: `v0.14.0-partial` (NOT `v0.14.0` — the campaign's §17 targets were not met; naming is honest)

## Why PARTIAL
Campaign 014 was executed in a prior session. An environment restart wiped the working
repository at `/home/z/my-project/miniandroid_ws/` before final packaging. Surviving:
- `MiniAndroid_v0.14.0_GIT_HANDOFF.zip` = **0 bytes** (interrupted mid-packaging — discarded as corrupt)
- `/tmp/my-project/miniandroid_ws/triage014/after/` = runtime triage artifacts for 16 apps (curated into `docs/campaign014_evidence/`)
- The campaign-014 **code commits did not survive** anywhere: workspace wiped, remote
  (`github.com/Sh-TB/MiniAndroid-Compatibility-Runtime`) still at base `bbe0ce3` (verified via
  `git ls-remote` on 2026-09-02). Therefore the runtime in this ZIP equals v0.13.0 code.
- The `after` triage artifacts were produced by a modified build whose source is LOST;
  they are archived as evidence of the interrupted session, not as a reproducible state.

## PROVENANCE (resolves §1 of the Campaign 014 directive)
- `PROVENANCE_STATUS: PARTIAL` — lineage `bbe0ce3(base) → a9434de(shallow boundary) → … 121 commits → v0.14.0-partial` is fully verified
  (fsck clean, 8 tags resolve, clean-extract tests passed). History below `a9434de` (pre-recovery EXP-campaign era) is unrecoverable from any surviving artifact.
- **`f5da664` / `v0.12.0`: UNKNOWN — confirmed absent** from: local DAG (both surviving packs), all surviving ZIPs, and the GitHub remote (`git ls-remote` returns only `bbe0ce3 / refs/heads/main`). No artifact bearing that hash exists. Campaign 012 was never executed as a distinct version; its real milestone is tag `campaign-012-baseline = ea81e00` (same commit as `v0.11.3-unified-011-3` and `v0.13.0-baseline`).
- Per §1: the actual Git DAG is the single source of truth; no continuity has been fabricated.

## Metric board (honest, evidence-limited)
- REAL_UI / REAL_INTERACTION / MULTI_FRAME: Campaign-013 numbers (v0.13.0 scoreboard) remain the last reproducible state; campaign-014 'after' artifacts suggest further progress but are non-reproducible (source lost) and are therefore NOT claimed.
- All §17 targets (REAL_INTERACTION ≥8, MULTI_FRAME ≥5, …): NOT MET / NOT PROVEN in this partial state.

## Handoff verification
- Every version ZIP embeds the same unified `.git` (full recoverable lineage incl. all tags + `campaign-014` branch); the working tree of each ZIP is checked out at its named version.

## Next step
Re-run Campaign 014 from the v0.13.0 baseline to produce a true `v0.14.0`.
