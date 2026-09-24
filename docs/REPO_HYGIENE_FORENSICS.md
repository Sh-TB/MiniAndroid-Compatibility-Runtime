# REPOSITORY HYGIENE FORENSICS — S-HYGIENE WAVE (root cause + disposition + law)

Date: 2026-09-24 · Wave: Repository Hygiene + Artifact Lifecycle + Git Bloat
Forensics · HEAD at wave start: `b75ee39a` (main, clean, 1 ahead of origin) ·
Dispositions ledger: `docs/history/s78_quarantine_recovery/MANIFEST.json` ·
Backup safety: `docs/history/s78_quarantine_recovery/BACKUP_SAFETY.txt` ·
Machine registry: `docs/ARTIFACT_REGISTRY.json` · Gate:
`tools/check_repo_hygiene.py` · Law: `docs/ARTIFACT_LIFECYCLE.md`

## 1. `.git` 620 MB — EXACT ROOT CAUSE (measured, not assumed)

```text
.git total (before)                    621 MB
├── loose objects                      525.38 MiB   (7,711 objects)  ← ROOT CAUSE
│   ├── miniandroid_ws/...272f216c.zip  151.0 MB  (blob 4d29b3da, SHA256 2e93d27d11a9…)
│   ├── miniandroid_prof/build/miniandroid 75.7 MB (blob 9fa80a47 — compiled binary)
│   ├── gc_work/...GAME_CHANGER_02e72ae.zip 7.3 MB (blob 63d5b240)
│   ├── hc_provenance/*/screenshot.ppm  ~17.7 MB (3 × 5.9 MB raw captures)
│   └── ~7,700 further snapshot/cache/agent-state objects
├── pack files                          93 MB (all published history, 3 packs)
└── refs/logs/other                    < 3 MB
```

**Cause chain:** during S78 a container-recovery workspace was committed by
accident as `d51f1815` (UUID message, 2,931 files, **593 MB unique objects**:
backup ZIPs, corpus caches, agent state, toolchain fragment, compiled binary).
S78 quarantined it on local branch `backup/s78-accidental-snapshot` (never
pushed — GitHub pre-receive rejected the 150.98 MB ZIP > 100 MB hard limit).
Because the branch was never pushed, its objects stayed as **loose objects
that `git gc` never repacked or dropped** — accumulating to 525 MB. The
published main history itself was always only ~92 MB packed.

## 2. Top storage offenders (complete table)

| Path (only in snapshot d51f1815) | Size | Blob SHA | Why it entered Git | Required? | Referenced by canonical evidence? | Action |
|---|---:|---|---|---|---|---|
| `miniandroid_ws/MiniAndroid_CANONICAL_MASTER_RECONCILED_272f216c.zip` | 151.0 MB | `4d29b3da` | accidental whole-workspace commit | no | no — audited A-03 = FULLY_REPRESENTED | DISPOSED |
| `miniandroid_prof/build/miniandroid` | 75.7 MB | `9fa80a47` | compiled binary captured in snapshot | no (regenerable) | no | DISPOSED |
| `gc_work/MiniAndroid_GAME_CHANGER_02e72ae.zip` (+ SOURCE_ONLY twin) | 11.7 MB | `63d5b240` | workspace backup | no | no | DISPOSED |
| `hc_provenance/run{1,2,3}/screenshot.ppm` | 17.7 MB | — | raw captures | no (canonical evidence elsewhere) | no | DISPOSED |
| `apk_build/anuto/**` (466 files) | ~8 MB | — | inflated APK tree of open-source Anuto | no (§12 SOURCE-AVAILABLE) | no | DISPOSED |
| `corpus_cache/`, `miniandroid_ws/`, platform-34.zip | ~330 MB rest | — | caches/agent state/toolchain | no | no | DISPOSED |

**Redundancy proof:** 7,382 of 8,334 snapshot files were byte-identical to
blobs already in main history; the workspace ZIP itself is archive A-03 of the
prior `docs/research/source-forensics/SOURCE_ARCHIVE_MATRIX.md` audit (SHA256
`2e93d27d11a9…` re-verified from the blob), verdict FULLY_REPRESENTED
(ancestor commit, 0 unique objects).

## 3. S78 backup branch disposition = **Outcome A (safe deletion)**

* What the ZIP contains: a full S-era workspace snapshot whose repo content is
  an ancestor of canonical main; 142.8 MB of it is a copy of an old `.git`
  pack whose objects are all present in canonical history.
* Unique content: NONE (0 unique objects per prior audit; per-blob re-check of
  all 8,334 files this wave — every non-disposal file rescued first, see §4).
* Branch referenced anywhere: only in S78/S77-era reports as a *record* of its
  existence (records preserved; the branch itself blocks publication).
* The ZIP is the ONLY push blocker — but the branch violates the repo's own
  commit-evidence rules regardless (no backup dumps / toolchain blobs).
* History rewrite: NOT NEEDED — the branch is local-only; deletion + gc-prune
  removes the objects without touching any published commit.

Executed: `git branch -D backup/s78-accidental-snapshot` →
`git reflog expire --expire=now --all` → `git gc --prune=now --aggressive`.

## 4. Zero-information-loss rescue (before deletion)

Every blob unique to the snapshot was ledgered
(`docs/history/s78_quarantine_recovery/MANIFEST.json`):

| Disposition | Count | Bytes | Destination |
|---|---:|---:|---|
| already in main history | 7,382 | — | none needed |
| RESCUED in-repo (docs/ knowledge + root knowledge files) | 34 | 295 KB | `docs/history/s78_quarantine_recovery/**` |
| RESCUED disk-only (raw traces, superseded inventories, raw PPMs) | 158 | 64.5 MB | `external_backup/s78_quarantine/**` (gitignored) |
| DISPOSED with class reason (caches/binaries/backups/inflated APKs) | 760 | 521.1 MB | deleted (ledgered with SHA) |
| toolchain fragment recorded-not-rescued | 1 | — | re-obtainable via `scripts/build/bootstrap_toolchain.sh` |

Rescued-into-repo highlights: R-NEW-368/369/370/371 VERIFIED-FIXED law proofs,
S46 agent gameplay evidence, S47 evidence manifest, S51 forensics + agent JSONs,
F023/PLAYABILITY reports, 6 achievement PNGs (superseded but historical).

## 5. Result

```text
REPOSITORY HYGIENE RESULT
=========================
Before:
  .git                = 621 MB  (525 MB loose objects, 93 MB packs)
  tracked tree        = 89.6 MB (5,252 files)
  largest artifact    = 151.0 MB workspace ZIP (local branch, unpushed)
  largest tracked     = docs/foundation/dex_census/bouncy.json 5.4 MB
After:
  .git                =  98 MB  (0 loose objects, single repacked set)
  tracked tree        = 89.5 MB (5,251 files; −1: empty 0-byte log)
  removed from Git    = 523 MB of unreachable snapshot objects
  removed from tree   = duplicate root MessageSchema.java (dup of docs/upstream/),
                        empty run/s94/source_mining/phase_c_clones.log
  integrity           = git fsck --full CLEAN; HEAD tree SHA unchanged
                        (81b033a0…); zero history rewrite; origin untouched
```

**Honest clone note:** a fresh `git clone` was ~92 MB before and ~96 MB after —
the 621 MB was LOCAL-ONLY bloat (unpushed branch + loose residue). The wins are
local disk (−523 MB), gc/fsck/repack cost, removal of the push blocker, and
prevention of recurrence (gate + law below). No invented speedups.

## 6. Git history cleanup decision matrix

| Problem | Current impact | Historical impact | Safe to delete? | Needs history rewrite? | Action |
|---|---|---|---|---|---|
| S78 snapshot objects (zips/binary/caches) | none (unreachable) | none | YES (rescued+ledgered) | NO — unreachable; gc-prune suffices | DONE (branch deleted, gc) |
| old APKs / toolchains in history | none tracked | pre-v0.11 packs may hold small residues | n/a | NO — impact ≈ 0, rewrite destroys SHA stability | LEAVE |
| old logs | none raw (whitelist = curated evidence) | small | n/a | NO | LEAVE |
| duplicate evidence (GIF/frame copies) | 5.7 MB reclaimable | small | only where refs update safely | NO | DOCUMENTED (§7) |
| stale branches | backup branch deleted; origin/gh-pages = pages | — | branch: DONE | NO | DONE |
| deleted large blobs (via gc) | — | — | YES | NO | DONE |

**History rewrite verdict: NOT JUSTIFIED.** All heavy offenders were
unreachable; reachable history contains no forbidden-class blobs (hygiene gate
PASS). Rewriting would change every canonical SHA for ~0 MB gain — forbidden.

## 7. Artifact classification (machine registry: docs/ARTIFACT_REGISTRY.json)

| Class | Files | MB |
|---|---:|---:|
| CANONICAL_EVIDENCE | 2,009 | 54.50 |
| REFERENCE_SOURCE_PINNED (upstream/) | 1,705 | 16.03 |
| CANONICAL_SOURCE | 1,070 | 12.12 |
| CANONICAL_DOC | 173 | 4.15 |
| CANONICAL_FIXTURE | 166 | 0.58 |
| UNKNOWN (residual, inventoried) | 126 | 2.09 |
| **Total tracked** | **5,251** | **89.5** |

Policy gate (`tools/check_repo_hygiene.py`): **PASS — zero APK/AAB/so, zero
build dirs, zero raw logs outside curated whitelist (4 distilled/before-after
logs referenced by S60/S62 reports = evidence), zero archive blobs, zero
undocumented >5 MB files (10 canonical allowlisted), zero secret patterns.**

Duplicates (374 groups, 5.7 MB reclaimable): 3 canonical-GIF mirrors
(docs/evidence/canonical vs s80 harvest — byte-identical, both referenced by
SHA manifests → documented, not deleted), deterministic repeat-run manifests
(s73 ×4, visual_forensics ×3 = **determinism evidence**), s94 working-copy
mirrors (run/ = script inputs, docs/evidence/ = evidence snapshot — both
referenced), upstream jar-vs-extracted-tree mirrors (intentional). Real
duplicates found and deleted: 2 (root MessageSchema.java, empty log).
Blind dedup was rejected where references (SHA256SUMS/registries) would break.

## 8. Development speed (measured, conservative)

| Metric | Before | After | Delta |
|---|---|---|---|
| `.git` disk | 621 MB | 98 MB | **−84%** |
| fsck --full | (untested before) | clean, fast | — |
| gc --prune=now | n/a (would keep branch objects) | 89 s one-time | — |
| clone payload | ~92 MB | ~96 MB | ~0 (honest: local-only bloat) |
| tree checkout | 89.6 MB / 5,252 files | 89.5 MB / 5,251 | ~0 |
| artifact scan (classifier) | — | ~0.2 s, 5,251 files | new deterministic tool |

Architecture law recorded: CACHE → REUSE → PARALLELIZE → STREAM → only then
optimize code. The biggest repeated-work killers remain the source library
(source_lookup), the deterministic battery, and the corpus registries —
audited in docs/SOURCE_REUSE_ROI.md (S96), not duplicated here.

## 9. SOURCE → APK → RUNTIME → PIXEL provenance audit

Already existing (verified in tree):

* UPSTREAM SOURCE: `docs/GRAPHICS_SOURCE_REGISTRY.json` (127 pinned entries,
  48 laws, 23 reusable implementations) + `tools/source_lookup.py` (law →
  pinned upstream file, exit-0 verified in S95).
* APK/DEX identity: canonical registry (148 titles, SHA256 per APK) +
  `docs/foundation/dex_census/**` per-title DEX class census.
* RUNTIME: `miniandroid/src/diagnostics/trace_engine.*` (method/API traces,
  R-NEW law probes) + run-record JSONs per session.
* VIEWTREE/OBJECT STATE: ViewTree dump machinery in `android_shadows.*`,
  `shadow_registry.cpp`; frame manifests with per-frame SHAs
  (docs/evidence/s73_snake_autoplay/frames/manifest.json pattern).
* PIXEL: screenshot/GIF evidence with SHA (docs/evidence/canonical +
  SHA256SUMS), interactive state-change GIFs (12 canonical).
* EXPLAINABILITY CHAIN (working today for graphics): law → source_lookup →
  pinned upstream class → implementation → battery fixture → screenshot SHA.

Missing links (recorded as concrete tickets in docs/TICKET_REGISTRY.json —
GFX-* / TEXT-* / NET-001 already registered by S95-CTRL; this wave adds no
runtime work):

1. RESOURCE-ID → VECTOR-INFLATER link (resource provenance: which @drawable/id
   produced which render op) — partially exists in shadow registry; needs a
   per-title resource→view mapping artifact. Ticket-class: GFX provenance.
2. VIEW-BOUNDS → PIXEL-REGION link (render op → screenshot region) — needs
   deterministic region hashing (exists ad-hoc in s74_ops maxdiff evidence).
3. DEX-CENSUS → RUNTIME-TRACE join (which census class actually executed in a
   run) — trace_engine holds the data; no join artifact yet.
4. END-TO-END EXPLAINER (Bouncy-style: "VectorDrawable source → resource ID →
   setImageDrawable → raster → bounds → pixels → SHA") — composition of 1–3.

These stay TICKETS (documentation-level) per wave scope: no new runtime
functionality in the hygiene wave.

## 10. Corpus fan-out diagnostic (lightweight, registry-based)

148 titles → shared structure (from canonical registries, not re-measured):
48 evidenced graphics laws cover the recurring divergence classes of the whole
corpus; 23 reusable implementations + 127 pinned sources back them;
23 games carry real execution evidence; 12 canonical interactive GIFs;
E5-deterministic repeat proven for Snake Deluxe, Mini Tetris, MiniCraft,
Fish Rings. Fan-out conclusion stands: every new law must be written once and
checked against ALL affected titles (CONSTITUTION §170/§171) — never 148
custom fixes.

## 11. Tool-first ledger (this wave)

| Tool | Purpose | Status |
|---|---|---|
| git count-objects/rev-list/cat-file + python zipfile | forensics | stdlib, zero new deps |
| tools/artifact_classifier.py (NEW) | classify 5,251 files + duplicates + SHA | NEW, deterministic, ~0.2 s |
| tools/check_repo_hygiene.py (NEW) | permanent preflight/CI gate | NEW, stdlib |
| tools/source_lookup.py | law → pinned source | existing (S94) |
| tools/validate_control_system.py (160 checks) | control-system consistency | existing (S95) |
| docs/research/source-forensics/* | archive audit (A-01..A-20) | existing — REUSED (not repeated) |

No third-party dependency was added (dup tools like rclone/jdupes/git-filter-repo
were considered and NOT adopted: stdlib + git covered 100% of needs).
