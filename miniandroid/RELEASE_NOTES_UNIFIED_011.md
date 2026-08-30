# RELEASE NOTES — UNIFIED_011_CANONICAL (tag `v0.11-unified-011`)

Date: 2026-08-30 · Base commit: `288ff6f` (+ docs) · Scope: canonical recovery
release — no feature development (CAMPAIGN 011 charter).

## Highlights

1. **UNIFIED_007 real resource pipeline recovered, verified, and committed**
   (`23900f8`) — real APK layout inflation: resource id → `resources.arsc` →
   `res/layout/*.xml` (AXML) → ViewShadow tree with measured geometry.
   - GMDice renders its **real UI** ("Push buttons to roll!", "Roll it!"):
     `6425c0f6…`, 158,040 non-white px (was the generic default screen).
   - Simple Stopwatch renders **real controls** (Start/Reset/digit/bottom row):
     `ef334f7c…`, 930,980 px.
2. **Zero-regression guard** — inflations that would render blank are rejected
   and the legacy default screen is kept (headingcalc, unote: byte-identical
   to the historical baseline `c200c521…`).
3. **Telegram v12.10.1 canonical baseline holds**: 3/3 runs identical
   (`06fb40da…`), exact match with the UNIFIED_002 record.
4. **Repository hygiene (ZERO-APK + evidence policy)**
   - 0 tracked APK/AAB; external cache + `scripts/download_test_apks.{sh,py}`
     with SHA256 verification (registry: `tests/corpus/apks.json`, 16 entries).
   - `.gitignore` added (build/, caches, run bulk, secrets patterns).
   - `make clean` no longer deletes tracked evidence under `run/`.
   - Curated evidence with provenance: `docs/evidence/u011/`.
5. **Documentation set for full handoff** — README rewritten;
   `MASTER_PROJECT_STATE_011.md`, `MASTER_CHANGELOG_KNOWLEDGE_011.md`,
   `MASTER_HANDOFF_011.md`, `OPEN_SOURCE_MASTER.md`, `DO_NOT_REINVENT.md`,
   `TEST_MATRIX.md`, `APK_REGISTRY.json`, `status.json`.

## Verification performed this session

- Clean-clone build (g++ 14.2) **SUCCESS**; full matrix re-run in the clean
  clone → all screenshots byte-identical to the dev build.
- A/B against a HEAD-only baseline binary for gmdice/headingcalc/microtimer/
  tictactoe/dooz/simplestopwatch: no regressions; improvements confined to
  the inflation path.
- GitHub remote checked live: `origin/main = bbe0ce3`; repo metadata recorded.

## Known blockers (carried, honestly)

- Compose/Dooz + tictactoe blank screens (pre-existing; analysis in docs).
- `@string/` layout refs unresolved (guard-protected; top next action).
- Obfuscated resource names unsupported.
- libpng linked but PNG decode still custom (CAMPAIGN 010 R1 open).
- No GLES backend (PortableGL candidate researched, not integrated).
- Push pending: 6 commits + tag await credentials.

## Build instructions

See `README.md §Quick start` (system deps + rlottie) — reproduced in
`MASTER_HANDOFF_011.md`. Fresh-clone build verified this session.

## Checksums

- Handoff package: `UNIFIED_011_CANONICAL_HANDOFF.zip` →
  SHA-256 in `UNIFIED_011_CANONICAL_HANDOFF_SHA256.txt` (delivered next to the zip).
- Evidence SHA256SUMS: `docs/evidence/u011/SHA256SUMS_U011.txt`.

## SHA256 of key evidence

| artifact | SHA-256 (first 16) |
|---|---|
| telegram_v12 screenshot ×3 | `06fb40da16b1f473` |
| gmdice real UI | `6425c0f639acaf03` |
| simplestopwatch real UI | `ef334f7ceaab204b` |
| legacy default screen | `c200c521628bb8a8` |
| blank (compose-family) | `c035e9ba62a884ec` |

APK digests live only in `APK_REGISTRY.json` / `tests/corpus/apks.json`.
