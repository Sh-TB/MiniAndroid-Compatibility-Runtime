# REPOSITORY DEEP CLEANUP AUDIT — Sh-TB/MiniAndroid-Compatibility-Runtime

Baseline audited: `96878de83aa748155724f8b60b42095a807e7d30` (main, pushed 2026-11-27).
Audit date: 2026-11-27. Method: **every tracked path inventoried from the current
HEAD, never from old reports** (17,510 tracked files; each with size, SHA256 of the
worktree file, git blob ID, and last-modifying commit — `FULL_FILE_INVENTORY.csv`).

## 0. Headline numbers (measured this audit)

| metric | value |
|---|---|
| tracked files at HEAD | 17,510 |
| tracked bytes (checkout content) | ~339 MB → **~320 MB after this audit's executed set** |
| git pack size (`git count-objects -vH`) | **1.06 GiB** |
| executed checkout saving (this commit) | **19,142,103 bytes ≈ 19.1 MB** (E1 twin 3,330,229 B / 379 files + E2 noise faces 15,811,874 B / 5 files) |
| executed file removals | 384 (all SHA-recorded in `SHA256SUMS.txt` BEFORE removal) |
| history-size reduction executed | **0 bytes — prohibited without owner authorization** (rule 5) |
| top history-size class | committed `build_*` trees: 3 × 35 MB prod binaries + ~50 × 34 MB test exes ≈ **4.77 GB of blobs** (S-SLIM REPOSITORY_SIZE_AUDIT re-confirmed by this audit's blob walk) |

## 1. Phase A — complete inventory

Deliverables (this directory): `FULL_FILE_INVENTORY.csv` (17,510 rows:
path,size,sha256,blob,last_commit,last_date), `DIRECTORY_REPORT.csv`
(dir-level files+bytes), `LARGE_FILES_TOP500.csv`, `DUPLICATE_GROUPS.csv`
(byte-identical groups by SHA256 with wasted-bytes), `NOISE_FACE_ANALYSIS.csv`
(87 screenshots in the named targets classified by measured pixel metrics).

Checkout composition (tracked, largest dirs): evidence/ ≈106 MB on-disk tree
(tracked portion inventoried in DIRECTORY_REPORT.csv), miniandroid/ (source +
tracked evidence), docs/ ≈56 MB, upstream/ ≈33 MB, scripts/ ≈17 MB.

## 2. Phase B — the named targets, each audited (not assumed)

| target | tracked files | bytes | verdict |
|---|---|---|---|
| `evidence/s200/harvest/` | 28 | 7.3 MB | KEEP — structured evidence, zero noise faces (measured); owner-may-compress later |
| `evidence/s200/runs/` | 271 | 7.5 MB | 1 NOISE face (`s202_625_forced`) REMOVED under the law; rest KEEP |
| `evidence/s207/runs/` | 294 | 5.0 MB | 1 NOISE face (`s207_ttt0`) REMOVED; rest KEEP |
| `evidence/s195_audit/` | 248 | 8.2 MB | 1 NOISE face REMOVED (`gates/runs/spot_halma`); **user-named exhibit `cohort/runs/tictactoe_s195fix_r1/screenshot.png` RETAINED**; contributor ledgers are canonical |
| `evidence/s188_w13/` | 186 | 4.5 MB | 1 NOISE face (`app.halma`) REMOVED; run-store `notes.db` class ledgered |
| `evidence/s188_w16/` | 158 | 4.1 MB | 0 noise; run-store DBs ledgered (blur.db/timetome.db) |
| `evidence/s188_w18/` | 204 | 4.0 MB | 1 NOISE face (`halma_w18_r1`) REMOVED |
| `upstream/s43/ui_android/` | 380 | 3.4 MB | KEEP — the CANONICAL twin per the S-SLIM duplicate ledger |
| `upstream/s43/ui_android_src/` | 379 | 3.25 MB | **DELETE EXECUTED** — 379/379 byte-identical to the canonical twin (measured with `cmp`), original `ui-android-1.11.4-sources.jar` tracked beside it (regenerable by unzip), and the S-SLIM ledger's own verdict was "losers keep ui_android canonical" — the bulk untrack pass had simply missed this tree. Full 379-row SHA ledger written BEFORE removal. |
| `docs/history/` | 139 | 2.9 MB | KEEP — the campaign worklog record (rule 8) |
| `miniandroid/database/source_first/` | 8 | 6.8 MB | KEEP — canonical per-APK source-coverage inventories + gap_map (achievement records) |
| `evidence/s182_mosaic/` | 2 | 1.6 MB | KEEP BOTH — PNG+JPG are registered policy artifacts (ARTIFACT_REGISTRY + IMAGE_POLICY_BASELINE + POLICY_ALLOWLIST); the mosaic is the user-cited S182 achievement visual |

Duplicate upstream JARs: `s43/*.sources.jar` (5) + `s44/protobuf.jar` +
`cont11_train7` jars are the pinned upstream ORIGINALS — KEEP (they are the
regeneration source for the extracted trees, exactly the pair the S43 twin was
untracked against).

Run-store databases still tracked (notes.db ×5, tickmate.db, uhabits.db,
blur.db, timetome.db, highscores.db …): the same residue class the S-SLIM pass
untracked elsewhere — **ledgered as OWNER-DECISION** (small total; not executed
without approval to respect rule 8).

## 3. The NOISE-FACE LAW (user-directed: "قررار شد تو قوانینی برای اینا راه حل بدی")

**The colored-noise screenshots are a measured, named class**, not a vibe:
sampled at full resolution, the class presents ≈**0.91–1.07 MILLION unique
colors** (52% of all pixels distinct — every pixel effectively random), nonwhite
≈0.9996, no structured palette. This is the uninitialized-framebuffer render of
the pre-flip era (6 faces found: tictactoe_s195fix_r1, spot_halma,
s202_625_forced, s207_ttt0, app.halma_w13, halma_w18_r1 — 22.0 MB total).

**LAW (codified, detector committed as `scripts/audit_noise_faces.py`):**
1. A screenshot with `distinct_ratio ≥ 0.25` AND `nonwhite ≥ 0.5` at full
   resolution is a **NOISE face** — a failed-render artifact. It carries zero
   app information beyond its hash and MUST NOT enter `docs/evidence/canonical/`,
   the canonical registry visuals, or any achievement claim.
2. Canonical-visual admission requires a STRUCTURED classification
   (`distinct_ratio` far below the noise band, dominant palette present).
3. **Preservation:** per noise family, ONE exhibit is retained (the
   user-named `tictactoe_s195fix_r1`); every removed face's SHA256 + pixel
   metrics are recorded (`SHA256SUMS.txt` E2 rows + `NOISE_FACE_ANALYSIS.csv`)
   and the failure itself stays documented in each run's tracked
   `report.md` / `trace.jsonl`. This satisfies rule 8 (failure evidence
   preserved) while removing information-free bulk.

## 4. Phase C — the ledger

`DELETE_CANDIDATES.csv` (20 decision rows): every candidate carries exact size,
sha256 (or per-file ledger reference), classification, references, duplicate
status, regenerability, where the information is preserved, the exact action
(EXECUTED / KEEP / OWNER-DECISION / OWNER-AUTHORIZED-REWRITE-ONLY), checkout
saving, history saving, and risk. **No file was classified by filename alone.**

## 5. Phase D — source safety (zero production damage)

- Production source inventory verified against `core_sources.manifest` +
  `make check-source-parity` → **[PARITY-OK] 88 core sources** after the
  executed set.
- `SOURCE_DEPENDENCY_PROTECTION.csv` (95 rows): the 88 core sources, the
  registered test batteries (55 law + 4 core + 3 hostile), fonts/assets,
  golden fixtures, canonical registry + policy files — each with its
  protection basis. None of the executed deletions touches any protected path
  (the two executed classes contain ZERO source/test/fixture/registry files).
- The only tracked build error logs (`make_err_*`, `make_fg1`, 1.45 MB) are
  intentional receipts committed by the blk609 finalize procedure → KEEP.

## 6. Executed set summary

| action | files | bytes | risk |
|---|---|---|---|
| E1 untrack `upstream/s43/ui_android_src/` (byte-identical twin, policy verdict completion) | 379 | 3,330,229 | LOW |
| E2 remove 5 of 6 NOISE faces (user-directed law; exhibit retained; SHAs recorded) | 5 | 15,811,874 | LOW |
| **total** | **384** | **≈19.1 MB** | — |

## 7. History size — what was NOT done and why

Rule 5 prohibits history rewriting, force-pushing, or tag deletion without
explicit owner authorization; rule 6 forbids treating `.gitignore` as proof of
historical removal. The pack is **1.06 GiB**, dominated by committed `build_*`
trees (see `HISTORY_SIZE_ANALYSIS.md`). Untracking at HEAD does not shrink the
pack. The rewrite plan, its expected ~4.8+ GB saving, and its preconditions
(owner authorization + the S-SLIM external backup gate, currently user-blocked)
are documented — NOT executed.

## 8. Phase E — verification (all measured post-execution)

See `FINAL_CLEANUP_VERIFICATION.md`: parity 88/88, battery 62/62, production
binary unchanged, canonical APK spot hashes identical to the pre-cleanup
baseline. Fresh-clone buildability documented there.
