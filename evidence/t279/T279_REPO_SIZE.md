# T279 — Repository Size Findings (2026-11-28; NO history rewrite performed)

## Measured facts (this clone, HEAD aa3541195 post-push)

| metric | value |
|---|---|
| `git count-objects -v` size-pack | **1,121,011 KB ≈ 1.09 GiB** (5735 loose objects, 144 MB) |
| `.git` directory | 1.3 GB |
| tracked files | 17,507 (S-SLIM final; largest tracked file is SOURCE: `miniandroid/src/dex/dalvik_engine.cpp` 5.28 MB) |
| working tree checkout (tracked bytes) | ~260 MB |
| GitHub API `size` | 1,046,451 KB (matches the 1.0 GiB report) |

The dominant history cost class was measured and documented by the
already-committed audits (S-SLIM `evidence/audit/REPOSITORY_SIZE_AUDIT.md`,
deep-cleanup `evidence/audit/deep_cleanup/`): **total blob bytes across all
history = 6.77 GB, of which 4.77 GB are `build_*` tree payloads** — three
~33.7 MB production binaries (build_w24b, build_fast, build_p2a) plus ~50
test executables of ~32.5 MB each under `build_fast/tests/` committed by an
auto-add session; this is recurrence #2 of the S153 incident class.

## What T279 did (and did not do)

- NO history rewrite, NO force-push, NO tag deletion, NO `git-filter-repo`
  against the real remote (the standing owner-gate holds).
- The generated-tree LAWS stay enforced at the root (`.gitignore` 481-line
  policy: `build*/`, `run_*/` outputs, `tools/dl/`, ccache trees stay local).
- T279's own outputs obey the size discipline: evidence/t279 promoted to Git
  is ~760 KB (72 compact 480px PNGs + CSV + JSON + audit md); run stores and
  the 120 MB binary stay untracked local.

## Owner-gated rewrite plan (prepared, NOT executed)

The safe path, when authorization is granted:

1. `git clone --mirror` the remote → full backup; record all refs
   (`git show-ref`), original HEAD, branch+tag list; SHA256 the bundle
   (`git bundle create backup.bundle --all` + `sha256sum`).
2. Restore the missing safety tag: `pre-slim-20261123` does NOT exist
   remotely (ls-external re-verified by the deep-cleanup audit) — create it
   on the backup before anything else.
3. Run `git filter-repo --strip-blobs-bigger-than 20M --invert-paths --path
   build_w24b --path build_fast --path build_p2a …` on a DISPOSABLE test
   clone only; keep the ~50 test-executable path list from
   `HISTORY_SIZE_ANALYSIS.md` exact.
4. Protected-path proof first: `SOURCE_DEPENDENCY_PROTECTION.csv` +
   `FULL_FILE_INVENTORY.csv` (17,510 paths, sha256 per file) prove every
   source/test/script/header/resource/law file and every canonical evidence
   path survives the filter untouched; `git diff --stat old..new` must be
   EMPTY for all protected paths.
5. Expected result (measured basis): pack 1.06-1.09 GiB → ~0.4-0.6 GiB
   (removing ~4.77 GB pre-compression blob payload ≈ 550-650 MB compressed
   per the S-SLIM blob accounting).
6. Verification gates before any real remote touch: fresh clone → clean
   build (`make -j2 all`) → regression battery → tag/branch parity check →
   `git fsck` → byte-identical source tree hashes vs backup.
7. Only then request the final force-push authorization with the backup
   bundle + its SHA256 published in the cleanup issue.

## Legitimate artifacts preserved (never filtered)

- Release assets (GitHub Releases, v0.0.6.x) — outside Git history anyway.
- `docs/evidence/canonical/*` (canonical screenshots + registry),
  `evidence/audit/*`, `evidence/s182_*`, `evidence/t279/*` (tracked),
  `miniandroid/evidence/*` — all tracked evidence paths stay.
- APKs are already zero in history (S153 purge + §20 zero-APK law).

## Ongoing hygiene (already in force)

- GitHub Releases for official binaries; GitHub Actions artifacts for
  temporary test outputs; ENOSPC is NEVER a test failure (S230/S235 laws);
  generated binaries cannot re-enter history (gitignore law, verified by
  `git status` clean on this session's builds).
