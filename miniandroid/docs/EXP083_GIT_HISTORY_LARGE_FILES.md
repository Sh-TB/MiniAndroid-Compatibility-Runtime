# EXP-083 Phase 39.9 — Git History Large-File Audit

**Generated:** 2026-08-22T19:04:51.629957+00:00

This report identifies every historical blob >5 MB in the MiniAndroid
Git repository. It does NOT rewrite history; it only documents what exists
and proposes a separate, reviewable cleanup plan.

---

## Summary

**Total large blobs:** 14
**Total bytes in large blobs:** 346.60 MB

---

## Detailed Inventory

| Path | Blob SHA | Size | Status | Commits | First commit | Last commit |
|---|---|---:|---|---:|---|---|
| `miniandroid/download/exp038_telegram/Telegram.apk` | `b2d52d574170…` | 78.85 MB | TRACKED | 2 | `133ec32` EXP-038: BLOCKER-022 — activit | `98ec49e` EXP-039.1: BLOCKER-035 FIXED — |
| `miniandroid/reports/telegram_call_graph.json` | `992756bff457…` | 62.51 MB | UNTRACKED_ON_DISK | 3 | `9b9fe70` EXP-049 Phase 2-3: Static call | `75318f3` EXP-083: Run directory forensi |
| `miniandroid/download/exp037_real_apks/fdroid_index_v2.json` | `76819507df17…` | 53.28 MB | UNTRACKED_ON_DISK | 3 | `1604090` EXP-037 Phase B: Add search_to | `75318f3` EXP-083: Run directory forensi |
| `miniandroid/build_asan/miniandroid_asan` | `156ec795b5f9…` | 28.56 MB | UNTRACKED_ON_DISK | 2 | `d4fe363` EXP-079: Merge all track resul | `75318f3` EXP-083: Run directory forensi |
| `miniandroid/run/exp076/nl.hansdezwart.bgclock_2/view_tree.json` | `08e3d4a0271e…` | 22.36 MB | UNTRACKED_ON_DISK | 2 | `9957925` EXP-076: Anti-overfit campaign | `75318f3` EXP-083: Run directory forensi |
| `miniandroid/build/miniandroid_megabatch` | `48f8bca10be7…` | 21.93 MB | UNTRACKED_ON_DISK | 2 | `69d71d5` 631ba4c2-f242-449a-af6f-0b995d | `7f48e00` chore: remove build artifacts  |
| `miniandroid/run/exp076/Telegram/view_tree.json` | `6e22b9e1422c…` | 21.85 MB | UNTRACKED_ON_DISK | 2 | `9957925` EXP-076: Anti-overfit campaign | `75318f3` EXP-083: Run directory forensi |
| `miniandroid/build/runtime/application_runtime.o` | `886314b79e84…` | 12.24 MB | UNTRACKED_ON_DISK | 4 | `4d7417e` 8302bb7c-d0f4-4e3d-9099-718e8f | `7f48e00` chore: remove build artifacts  |
| `miniandroid/build/runtime/application_runtime.o` | `c965231ac2d3…` | 12.24 MB | UNTRACKED_ON_DISK | 4 | `4d7417e` 8302bb7c-d0f4-4e3d-9099-718e8f | `7f48e00` chore: remove build artifacts  |
| `miniandroid/build/exp007_012_megabatch_main.o` | `45618a4aaed5…` | 8.29 MB | UNTRACKED_ON_DISK | 3 | `69d71d5` 631ba4c2-f242-449a-af6f-0b995d | `7f48e00` chore: remove build artifacts  |
| `miniandroid/build/resources/resource_parser.o` | `fd672b53f8f6…` | 7.18 MB | UNTRACKED_ON_DISK | 4 | `4d7417e` 8302bb7c-d0f4-4e3d-9099-718e8f | `7f48e00` chore: remove build artifacts  |
| `miniandroid/build/dex/dex_interpreter_batch.o` | `b9efe5abdedc…` | 6.35 MB | UNTRACKED_ON_DISK | 4 | `4d7417e` 8302bb7c-d0f4-4e3d-9099-718e8f | `7f48e00` chore: remove build artifacts  |
| `miniandroid/experiments/EXP-026/test_execution/screenshot.ppm` | `07a78b71ed35…` | 5.93 MB | TRACKED | 2 | `185e833` EXP-026: REAL MINIANDROID RUNT | `979b044` 3184a788-db97-4334-8b3a-93757f |
| `miniandroid/build/dex/dex_interpreter.o` | `6982c082ba7e…` | 5.04 MB | DELETED | 2 | `4d7417e` 8302bb7c-d0f4-4e3d-9099-718e8f | `69d71d5` 631ba4c2-f242-449a-af6f-0b995d |


---

## Status Definitions

- **TRACKED** — File is currently in the working tree and tracked by Git.
  The blob is reachable from `HEAD`.
- **UNTRACKED_ON_DISK** — File exists on local disk but is no longer tracked
  (was `git rm --cached` in EXP-083 Phase 38). The blob is still reachable
  from history but not from `HEAD`.
- **DELETED** — File does not exist on disk. The blob is reachable only
  from older commits.

---

## Why These Blobs Still Exist

Git is content-addressable: a blob is unreachable when no commit references
its path+content, but the blob remains in `.git/objects` until `git gc --prune`
runs and the reflog expires it.

`git gc --aggressive --prune=now` (run during Phase 38) packs all reachable
objects but **does not** rewrite history. Blobs that were once committed
but later removed are still reachable from the commits that contained them.

To permanently remove a historical blob, you must use
`git filter-repo --path <path> --invert-paths`. This rewrites history
and changes every commit SHA downstream of the removal.

---

## Recommended Cleanup Plan (Manual, Reviewable, NOT Automatic)

Per §39.9 of the user's spec, **do NOT rewrite history automatically**.
The following is a reviewable plan:

### Step 1 — Backup
```bash
cd MiniAndroid-Compatibility-Runtime
git clone --mirror . ../miniandroid-backup.git
```

### Step 2 — Identify blobs to remove from history
Recommended candidates (in order of impact):

1. `miniandroid/download/exp038_telegram/Telegram.apk` (78.85 MB) — once
   externalized via LFS/Release, remove from history.
2. `miniandroid/reports/telegram_call_graph.json` (62.51 MB) — generated
   DEX call-graph, regenerable from `tools/dex_call_graph.py`.
3. `miniandroid/download/exp037_real_apks/fdroid_index_v2.json` (53.28 MB) —
   F-Droid index cache, regenerable.
4. `miniandroid/build_asan/miniandroid_asan` (28.56 MB) — ASAN binary,
   regenerable from CMake.
5. `miniandroid/run/exp076/nl.hansdezwart.bgclock_2/view_tree.json` (22.36 MB) —
   runtime dump, regenerable.
6. `miniandroid/build/miniandroid_megabatch` (21.93 MB) — build artifact.
7. `miniandroid/run/exp076/Telegram/view_tree.json` (21.85 MB) — runtime dump.
8. `miniandroid/build/runtime/application_runtime.o` (12.24 MB) — object file.
9. `miniandroid/build/exp007_012_megabatch_main.o` (8.29 MB) — object file.
10. `miniandroid/build/resources/resource_parser.o` (7.18 MB) — object file.
11. `miniandroid/build/dex/dex_interpreter_batch.o` (6.35 MB) — object file.
12. `miniandroid/experiments/EXP-026/test_execution/screenshot.ppm` (5.93 MB) — PPM screenshot.
13. `miniandroid/build/dex/dex_interpreter.o` (5.04 MB) — object file.

Total potential savings: ~325 MB from history.

### Step 3 — Run filter-repo (after backup)
```bash
pip install git-filter-repo

git filter-repo \
    --path miniandroid/download/exp038_telegram/Telegram.apk \
    --path miniandroid/reports/telegram_call_graph.json \
    --path miniandroid/download/exp037_real_apks/fdroid_index_v2.json \
    --path miniandroid/build_asan/miniandroid_asan \
    --path miniandroid/build/miniandroid_megabatch \
    --path-glob 'miniandroid/run/*/view_tree.json' \
    --path-glob 'miniandroid/build/**/*.o' \
    --path-glob 'miniandroid/experiments/*/screenshot.ppm' \
    --invert-paths
```

### Step 4 — Force-push (coordination required)
```bash
git push origin --force --all
git push origin --force --tags
```

### Step 5 — Coordinate with collaborators
Anyone who has cloned the repo must re-clone. Old clones will have stale
objects. Send a notification before force-pushing.

### Step 6 — Verify
```bash
git rev-list --objects --all |
  git cat-file --batch-check='%(objectname) %(objecttype) %(objectsize) %(rest)' |
  awk '$2=="blob" && $3 > 5242880 <built-in function print>'
```
Output should be empty (or much smaller).

---

## Why This Audit Did NOT Auto-Execute Step 3

The user's instructions in §39.9 explicitly state:

> Do NOT rewrite history automatically.
> First produce: docs/EXP083_GIT_HISTORY_LARGE_FILES.md
> If inappropriate historical binaries exist, prepare a separate,
> reviewable history-cleanup plan using git filter-repo.

This document is that plan. Execution requires:
1. Backup verification
2. Coordination with anyone who has cloned the repo
3. Manual confirmation that no current test depends on the historical blob
4. Explicit user authorization

