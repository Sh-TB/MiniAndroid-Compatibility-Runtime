# GITHUB_EVIDENCE_INDEX — §20/§21 evidence and persistence record

Campaign: REUSE-FIRST FULL COMPATIBILITY + RESEARCH-TO-CODE
Date: 2026-09-05 · Parent repository (mandated):
https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime

## Push / persistence state (§21 — exact, no claims without proof)

| Item | Value |
|---|---|
| Local HEAD (final this campaign) | see `git rev-parse HEAD` — commits listed below |
| Remote main at campaign start | `ad95d92876a355a719d2a8959053f8a47c2b1e79` |
| Remote history relationship | **UNRELATED** to local history (`git merge-base` empty): remote = original 394-commit project history (project at repo root); local = workspace superproject rebuilt in this environment (project under `MiniAndroid-Compatibility-Runtime/`), 23 commits at start + this campaign's commits |
| Push attempts | `git push origin main` → **FAILED** |
| Exact error | `fatal: could not read Username for 'https://github.com': No such device or address` |
| Credential check | no credential helper; gh CLI absent; `~/.ssh` absent; no token env vars; no `~/.netrc`, `~/.config/gh`, `.env` |
| Status | **PUSH_BLOCKED** — machine-readable record: `docs/evidence/PUSH_BLOCKED.json` (includes next-session recovery instructions) |
| Preservation measures | (1) all work committed locally; (2) local branch `archive/origin-main-ad95d928` → `ad95d928` keeps the 394-commit original line reachable for a future push; (3) remote-only file `miniandroid/run/exp096_evidence/metrics.json` recovered into the local tree (commit `3c39f1fa`); (4) PUSH_BLOCKED.json documents the subtree-split push plan |
| GitHub comments | **COMMENT_BLOCKED** — same missing-credential cause; no authenticated API path. Pre-drafted comment texts: see "Comment drafts" below. Never claim a comment exists when its URL is absent. |

## Achievement → commit → evidence table

| Achievement | Commit | Evidence artifact | GitHub URL | Comment URL |
|---|---|---|---|---|
| Remote-only EXP096 metrics.json recovered + PUSH_BLOCKED record + archive ref | `3c39f1fa` | docs/evidence/PUSH_BLOCKED.json | pending push | COMMENT_BLOCKED |
| FIND-REUSE-001: ONE MUTF-8/ULEB128 primitive (3 copies → 1), non-ASCII string corruption FIXED | `2c8bf2da` | miniandroid/src/dex/mutf8.{h,cpp}; tests/mutf8_string_pool_test.cpp 7/7; pre-fix reproducer output in AGENT_FINDINGS_VALIDATION.md | pending push | COMMENT_BLOCKED |
| WineDroid 007/011 discriminators + one-command battery gate (§12) | `9e7c0e9b` | semantic_pass3_bridge_test 57-case group WD/SW; scripts/run_test_battery.sh 10-stage ALL PASS | pending push | COMMENT_BLOCKED |
| §24 evidence docs (GOLDEN_HELLOWORLD / TICTACTOE_STATUS / CURRENT_COMPATIBILITY_MATRIX) | this campaign's docs commit | docs/evidence/*.md | pending push | COMMENT_BLOCKED |
| §24 research docs (WINEDROID_DEEP_STUDY / REFERENCE_PROJECT_MATRIX / TRANSFER_MATRIX / AGENT_FINDINGS_VALIDATION / REUSE_REDUCTION_REPORT / GITHUB_EVIDENCE_INDEX) | this campaign's docs commit | docs/research/*.md | pending push | COMMENT_BLOCKED |
| Resource-backed Hello World — REAL aapt2 APK (binary manifest + resources.arsc + binary AXML), §36.E discriminator permanent (strings in ARSC, ABSENT from DEX), golden gate 18→26 checks | `a3c3aded` | docs/evidence/GOLDEN_HELLOWORLD.md; reschain_report.txt; screenshot a61f5b22…; APK 3cf76fb7…; battery 11/11 | pending push | COMMENT_BLOCKED |
| FIND-REUSE-002/003: UTF-16LE→UTF-8 5 copies→1 (manifest surrogate BUG fixed) + SLEB128 2→1 (UB hardened); battery caught 2 defects in the new canonical code pre-landing | `e69bc496` | tests/mutf8_string_pool_test.cpp 10/10; corpus pixels byte-identical (gmdice, simplestopwatch) | pending push | COMMENT_BLOCKED |
| FIND-REUSE-004: ONE ResStringPool decoder (ARSC+AXML+manifest 3 copies→1; AOSP offsets-table law; BLOCKER-006 class dead; decode_string_length orphaned+removed) | `4d822256` | resources/string_pool.{h,cpp}; battery 11/11 after make clean; corpus pixel-identity ×3 | pending push | COMMENT_BLOCKED |
| §26 research index + §35 final report + §2 WineDroid mechanism table + §11/§28 metrics | `4468e3b9` | docs/research/GITHUB_RESEARCH_INDEX.md (36 rows); docs/CAMPAIGN_FINAL_REPORT_REUSE_FIRST_PROGRESS.md | pending push | COMMENT_BLOCKED |
| helloworld_golden + EXT-AOSP-001/002 (prior campaign, revalidated ×2 this campaign) | `738ac50` (remote: not yet — part of unrelated-history backlog) | docs/evidence/helloworld_golden/*, screenshot SHA 93b42621… | pending push | COMMENT_BLOCKED |
| tictactoe_golden end-to-end (prior campaign, revalidated ×2) | `de5f370e` | docs/evidence/tictactoe_golden/*, frames byte-identical | pending push | COMMENT_BLOCKED |

## Comment drafts (post after push succeeds; do NOT post without a real commit URL)

1. **FIND-REUSE-001 (DEX string pool)** — "Fixed real MUTF-8 corruption:
   string_data_item utf16_size (code units) was treated as a byte count,
   truncating every non-ASCII string; encoded NUL undecoded; ULEB128 had
   no 5-byte cap (UB on hostile input). Replaced 3 duplicated readers
   with one primitive (src/dex/mutf8), adapted from WineDroid
   WINEDROID-004/005 (Apache-2.0, behavioral reference). Regression
   battery 7/7; full gate 96 semantic + 18 + 8 golden checks green;
   golden screenshots byte-identical. Commit: <SHA>."
2. **WineDroid laws pinned as tests** — "WineDroid mechanisms 007
   (absent-arg determinism) and 011 (switch payload-is-data) are now
   executable discriminators in the semantic battery (96/96). One-command
   gate added: scripts/run_test_battery.sh (10 stages, zero-skip)."
3. **Revalidation record** — "Hello World golden (18/18, screenshot SHA
   93b42621…) and Tic-Tac-Toe golden (9/9 clicks → 'X WINS', 10 frames
   deterministic) revalidated at the campaign HEAD from clean builds."

## §38 double success criteria

- (A) Knowledge transfer completed: WineDroid 004/005 implemented,
  007/011 pinned, queue documented; matrix consolidated; URL law honored
  (2 honest UNAVAILABLE/UNVERIFIED entries).
- (B) At least one real APK LOAD→EXECUTE→UI→RENDER→SCREENSHOT with
  Tic-Tac-Toe interaction explicitly tested: **both goldens revalidated
  deterministic at current HEAD.**
