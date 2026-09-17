# S51 — History Purge Plan (PHASE 9)

Authorization: explicit owner directive "remove all old pushes" (تمامی پوش‌های قدیمی حذف شود),
2026-09-17. Companion forensics: `docs/forensics/HISTORICAL_BLOAT_REPORT.md`.

## Objective

Remove ~940 MiB of junk blobs from main history and decommission the 4 archive branches
(~1.4 GiB era containing LLVM toolchain, Telegram.apk, fdroid index, ASan binary, call
graphs), so the canonical repository is small, auditable, and free of raw-log history.

## What is rewritten / deleted

| Item | Action | Detail |
|---|---|---|
| main | history rewrite | strip 83 exact paths (`tool-results/strip_paths.txt` classification in bloat report), 279 commits + S51 prep commit rewritten |
| tags v0.0.1, v0.0.2, v0.0.2-alpha, v0.0.3-Chantecler, v0.0.4-Chantecler, v0.0.5-Silkie, v0.0.6-Leghorn | remap | filter-repo rewrites tag objects onto purged chain; names preserved; GitHub releases keep tag names |
| archive/local-main-12cf043f, archive/local-main-167c27fb, archive/local-main-d358a0c9-stale, archive/origin-main-ad95d928 | DELETE | local + origin (old pushes; hold LLVM/APK/fragment history; superseded by main + docs) |
| Working tree | UNCHANGED | post-purge HEAD tree hash must equal pre-purge `8b74cb093e06f624cae45c9205dd43bb05570a34` |

## Tooling

- git-filter-repo a40bce548d2c (`python3 -m pip install git-filter-repo`), invoked as
  `git filter-repo --force --invert-paths --paths-from-file <list>`
- The strip list contains EXACT historical paths only (83). Collision gate before execution:
  `strip_paths ∩ git ls-files = ∅` (verified, see bloat report).

## Backup & rollback

- Pre-purge bundle: `backup-s51/pre-purge-main-tags.bundle` (487,858,487 bytes).
- Rollback: `git clone backup-s51/pre-purge-main-tags.bundle <dir>` then reset remote refs
  from it. The bundle is local-only, never committed; remove `backup-s51/` from disk only
  after fresh-clone verification of the purged remote.

## Execution order (no step skipped)

1. Commit S51 prep (bloat report + plan + inventory + audit script + worklog + .gitignore
   for `backup-s51/`, `tool-results/`).
2. Delete local `archive/*` branches so filter-repo does not preserve their objects.
3. Record pre-purge tree hash; run filter-repo; re-add origin URL (filter-repo detaches it;
   URL contains no credential — auth is ephemeral per-invocation credential helper).
4. Verify locally: tree-hash equality, big-blob audit of rewritten main (expect only the
   KEEP-set), commit count = 280, secret guard `--tree` PASS, `git fsck` clean.
5. Push: `git push --force origin main` + `git push --force origin <each rewritten tag>` +
   `git push origin --delete archive/local-main-12cf043f archive/local-main-167c27fb
   archive/local-main-d358a0c9-stale archive/origin-main-ad95d928`.
6. Remote verification: `git ls-remote` shows only purged refs; fresh clone of origin/main;
   re-run blob audit + secret guard inside the fresh clone; record final sizes.
7. Post-push secret re-scan (PHASE 0 rule) on the fresh clone.

## Honest status vocabulary for the report

- `REMOTE VERIFIED` = fresh-clone check of purged refs passed.
- `REMOTE HISTORY VERIFIED` = old blob SHAs unreachable from any remote ref (`ls-remote` +
  fresh clone audit).
- `PENDING GITHUB GC` = GitHub-side size counter may still include unreachable old objects
  until GitHub's internal garbage collection; no ref references them.

## Non-goals

- No commit-message rewriting (messages are compact forensic records; purged artifact paths
  mentioned in old messages remain valid historical narrative).
- No release/asset deletion on GitHub (small, API-side; v0.0.6 SHA256SUMS defect stays
  recorded BLOCKED per S49).
- No current-tree content changes in this step (tree-hash invariant).
