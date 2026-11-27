# HISTORY SIZE ANALYSIS — git pack 1.06 GiB, measured 2026-11-27 at HEAD `96878de83`

## 1. Measured facts (`git count-objects -vH`)

| metric | value |
|---|---|
| loose objects | 5,710 |
| pack size | **1.06 GiB** |
| tracked tree at HEAD | ~339 MB (17,510 files) |

The pack is ~3× the checkout: most history bytes are objects that no longer
exist at HEAD — exactly the classes the S-SLIM REPOSITORY_SIZE_AUDIT measured
(6.77 GB of history blobs before its index-level slimming; the pack retains
them, which is why rule 6 of this audit forbids treating `.gitignore` as
proof of historical removal).

## 2. The dominant blob classes (this audit's own `rev-list --objects --all` walk)

| class | examples (top blobs measured) | ≈ class bytes |
|---|---|---|
| committed prod binaries | `miniandroid/build_w24b/miniandroid` (35.3 MB), `build_fast/miniandroid` (35.3 MB), `build_p2a/miniandroid` (34.7 MB) | ~105 MB |
| committed test executables | `build_fast/tests/*` — s234_w26_engine_laws_test 34.3 MB, s235_lane_laws_test 34.2 MB, s236_port_laws_test 34.2 MB, g04_hostile_test 34.2 MB, … ~50 exes ≈ 34 MB each | ≈ 1.7 GB+ |
| all build_* trees combined | the 4.77 GB class named by the S-SLIM audit | **≈ 4.77 GB (raw blob sum; pack-compressed lower)** |
| APK/residue | historic tracked APKs, run exports | remainder |

## 3. What untracking does and does not do

This audit's executed set (379-file byte-identical twin + 5 noise faces ≈
15.3 MB checkout) does **not** shrink the pack: the blobs stay reachable from
history. Checkout size and clone/download size are separate deliverables —
checkout shrinks now; pack shrinks only via rewrite.

## 4. The rewrite option — NOT executed (rule 5)

The only way to actually shrink the 1.06 GiB pack is a history rewrite
(`git filter-repo`-class) dropping the committed `build_*` trees and other
raw-exhaust blobs. The S-SLIM campaign's Scenario-B analysis (2,710 commits
changed in the full variant / 105 in the conservative variant, all 10 release
tags re-SHA'd) established both the plan and the gates:

**Preconditions (all still required):**
1. Explicit owner authorization for a rewrite + force-push (rule 5 — absent).
2. The external backup gate: a verified push of the FULL pre-rewrite history
   to a second remote. The S-SLIM Phase-4 `pre-slim-20261123` recovery tag was
   cited by the slimming commit message but **does not exist on the remote**
   (`git ls-remote` re-verified this audit: 14 tags, no pre-slim) — and the
   external-backup gate itself remains user-blocked. **NO-GO stands.**

Expected saving if ever approved: the 4.77 GB build-tree class dominates; a
conservative drop of `miniandroid/build_*/` blobs alone takes the pack from
1.06 GiB toward the ~300-400 MB range (pack-compressed estimate, to be
re-measured post-rewrite — never asserted).

## 5. Honest summary

- Checkout content: reduced now, by evidence-backed zero-risk deletions only.
- Pack: unchanged by design; the path and its gates are documented; the gate
  is blocked on the owner, not on engineering.
