# MiniAndroid — Central Index

One entry point to navigate the repository by CONCEPT (not by session number).
Machine-readable twin: [`docs/INDEX.json`](docs/INDEX.json).

## What am I looking for?

| I want… | Go to |
|---|---|
| **Every real APK execution, per app (canonical)** | [`EXECUTION_ACHIEVEMENTS.md`](EXECUTION_ACHIEVEMENTS.md) |
| **Knowledge/research file inventory + pipeline map (canonical)** | [`KNOWLEDGE_INDEX.md`](KNOWLEDGE_INDEX.md) |
| **The reconciled roadmap + P0 frontier (canonical)** | [`ROADMAP.md`](ROADMAP.md) |
| The project overview & verified capabilities | [`../README.md`](../README.md) |
| Architecture / how the runtime works | [`docs/architecture/`](architecture/) · [`docs/runtime/architecture.md`](runtime/architecture.md) |
| The one regression-battery command | `bash scripts/test/run_test_battery.sh` → “BATTERY GATE: ALL PASS” |
| Which battery stages exist & their status | [`docs/testing/BATTERY_INDEX.json`](testing/BATTERY_INDEX.json) |
| Every known root cause & its status | [`../root_registry.json`](../root_registry.json) (349 roots) |
| The upstream semantic contract behind a fix | [`docs/upstream/INDEX.md`](upstream/INDEX.md) |
| Per-issue forensic evidence (compact) | [`docs/evidence/`](evidence/) · solved: [`docs/evidence/solved/`](evidence/solved/) |
| Where raw campaign exhaust went | [`docs/evidence/ARCHIVE_MANIFEST.json`](evidence/ARCHIVE_MANIFEST.json) (external archive, SHA-pinned) |
| Release notes & artifacts | [`docs/releases/`](releases/) · current: `RELEASE_v0.0.6-Leghorn.md` |
| Release manifest (versions/SHAs) | [`docs/releases/RELEASE_MANIFEST.json`](releases/RELEASE_MANIFEST.json) |
| Session history / worklog | [`docs/maintenance/worklog.md`](maintenance/worklog.md) |
| Building (incl. Windows cross-build) | [`docs/build/`](build/) · `miniandroid/scripts/build_windows.sh` |
| Release packaging & guards | `scripts/release/` (`package_release.sh`, `check_release_artifacts.sh`, `validate_release_content.py`, `release_clean_extract_test.sh`) |
| Fixture toolchain bootstrap | `scripts/build/bootstrap_toolchain.sh` |
| Fetched upstream source evidence (pinned per session) | `upstream/` (kotlinx-collections, compose, s43/s44 sources — 961 files, ~15 MB; provenance for the upstream-law index) |

## Issue index (by concept)

| Concept | Root IDs (status) | Evidence |
|---|---|---|
| Compose placement/draw cascade | R-NEW-329/332/333 (VERIFIED-FIXED / closed) | s33/s34 session records |
| Compose attach & traversal ordering | R-NEW-344/349 (VERIFIED-FIXED) | S42/S43 records |
| Collections copy/iterator contracts | R-NEW-360 + F-101 (VERIFIED-FIXED) | s45_session_record §3 |
| View.post main-queue law | R-NEW-359 (VERIFIED-FIXED) | s45_session_record §2 |
| SharedPreferences package-dir law | **R-NEW-367 (VERIFIED-FIXED, S48)** | RELEASE_v0.0.6-Leghorn |
| ScatterMap probe arithmetic (dooz) | R-NEW-335/361 (**OBSERVED-FAIL — primary frontier**) | s45_session_record §4 |
| Fragment host attach family | R-NEW-331 (OBSERVED-FAIL) | S27 evidence |
| Desugared streams (Telegram) | R-NEW-303 (OBSERVED-FAIL) | mc4_telegram evidence |
| Navigation back-stack graph entries | R-NEW-323 (OBSERVED-FAIL) | S24/S25 evidence |

## Status vocabulary (canonical)

`OBSERVED-FAIL · ROOT-CAUSED-FIXED · VERIFIED-FIXED · VERIFIED-CORRECT ·
IMPLEMENTED · PARTIAL · PARTIAL-FIX · RESEARCHED-NOT-IMPLEMENTED · UNPROVEN ·
NOT-APPLICABLE · SUPERSEDED-BY-EVIDENCE`

## Evidence policy (short form)

Raw campaign exhaust (stderr/stdout dumps, per-instruction traces, raw
framebuffers, forensic session dirs) is **archived externally** with per-file
SHA-256 provenance in `docs/evidence/ARCHIVE_MANIFEST.json`; compact evidence
(reports, execution summaries, screenshots, goldens) in `docs/evidence/` is
the source of truth. Git history retains every archived blob — nothing is
silently destroyed, and nothing raw returns to the operational tree
(`.gitignore` enforces).
