# GITHUB_EVIDENCE_INDEX — §20/§21 authoritative achievement→evidence map

Campaign: REUSE-FIRST FULL COMPATIBILITY + RESEARCH-TO-CODE → MAXIMUM REUSE /
FULL SOURCE AUDIT / COMPLETE APK EXECUTION (session 2026-09-05)
Parent repository (mandated): https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime

## Push / persistence state (§21 — exact, verified this session)

| Item | Value |
|---|---|
| Remote main (verified `git ls-remote`) | `7d00552506d07c479812ed625955d92fb9ee5c29` = local HEAD |
| Original 394-commit history | preserved at remote branch `archive/origin-main-ad95d928` = `ad95d92876a355a719d2a8959053f8a47c2b1e79` |
| Push method | documented recovery plan in `docs/evidence/PUSH_BLOCKED.json` executed: archive branch pushed first, then `--force-with-lease=refs/heads/main:ad95d928…` |
| PUSH_BLOCKED | **RESOLVED** (was 33 commits blocked across prior sessions; exact error archived in PUSH_BLOCKED.json) |
| Security sweep before push | `git grep` for PAT/ghp token patterns over all tracked files → CLEAN |

## GitHub evidence anchor

Issue: **https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/8**
("MiniAndroid campaign evidence — verified achievements (REUSE-FIRST campaign, 2026-09-05)")

## Authoritative map — achievement → commit → test → evidence file → issue/comment URL → status

Every comment URL below was READ BACK from the GitHub API (authenticated GET
`/repos/…/issues/8/comments`) this session — never claimed without read-back.

| # | Achievement | Commit | Test | Evidence file | Comment URL | Status |
|---|---|---|---|---|---|---|
| 1 | Campaign baseline & repository state (HEAD/remote/unpushed audit) | `4d822256`+`1b86da8a` | battery 11/11 | CURRENT_HEAD_BASELINE.md; docs/evidence/PUSH_BLOCKED.json | [#8 c-5551995211](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/8#issuecomment-5551995211) | POSTED+VERIFIED |
| 2 | Clean rebuild + one-command battery gate (11 stages) | `9e7c0e9b` | run_test_battery.sh ALL PASS | scripts/run_test_battery.sh; CURRENT_HEAD_BASELINE.md | [#8 c-5551995299](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/8#issuecomment-5551995299) | POSTED+VERIFIED |
| 3 | Real resource-backed Hello World — aapt2/ARSC/AXML/§36.E (26/26) | `a3c3aded` | validate_helloworld_golden.sh 26/26 | docs/evidence/GOLDEN_HELLOWORLD.md; reschain_report.txt | [#8 c-5551995394](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/8#issuecomment-5551995394) | POSTED+VERIFIED |
| 4 | Tic-Tac-Toe real UI — 9/9 clicks, X-WINS, deterministic replay | `de5f370e` | tictactoe_golden 8/8 | docs/evidence/tictactoe_golden/ | [#8 c-5551995472](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/8#issuecomment-5551995472) | POSTED+VERIFIED |
| 5 | WineDroid reuse — MUTF-8/ULEB128 ONE primitive (FIND-REUSE-001) + 007/011 discriminators | `2c8bf2da`+`9e7c0e9b` | mutf8 battery 10/10; pass3 bridge 57 | docs/research/WINEDROID_DEEP_STUDY.md; tests/mutf8_string_pool_test.cpp | [#8 c-5551995545](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/8#issuecomment-5551995545) | POSTED+VERIFIED |
| 6 | UTF-16LE→UTF-8 5→1 + manifest surrogate bug fixed (FIND-REUSE-002) | `e69bc496` | mutf8 T8–T12; corpus pixel-identity | docs/research/REUSE_REDUCTION_REPORT.md | [#8 c-5551995676](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/8#issuecomment-5551995676) | POSTED+VERIFIED |
| 7 | SLEB128 2→1, UB hardened (FIND-REUSE-003) | `e69bc496` | SLEB 10 vectors 10/10 | docs/research/REUSE_REDUCTION_REPORT.md | [#8 c-5551995765](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/8#issuecomment-5551995765) | POSTED+VERIFIED |
| 8 | ResStringPool 3→1 canonical decoder (FIND-REUSE-004) | `4d822256` | battery 11/11 after make clean | resources/string_pool.{h,cpp}; REUSE_REDUCTION_REPORT.md | [#8 c-5551995861](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/8#issuecomment-5551995861) | POSTED+VERIFIED |
| 9 | −294 production LOC code-minimization scoreboard (§28) | `e69bc496`+`4d822256` | git-verified per-commit LOC | docs/research/REUSE_REDUCTION_REPORT.md §28 | [#8 c-5551995932](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/8#issuecomment-5551995932) | POSTED+VERIFIED |
| 10 | Corpus pixel-identical validation (gmdice/simplestopwatch/microtimer) | `e69bc496`+`4d822256` | 3 consecutive pixel-identity rounds | CURRENT_HEAD_BASELINE.md §Corpus | [#8 c-5551996014](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/8#issuecomment-5551996014) | POSTED+VERIFIED |
| 11 | §26 research index (36 repos) + evidence summary | `4468e3b9`+`31789f6e` | append-only index audit | docs/research/GITHUB_RESEARCH_INDEX.md | [#8 c-5551996090](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/8#issuecomment-5551996090) | POSTED+VERIFIED |
| 12 | PUSH_BLOCKED resolved — 34 commits on remote, verified | `7d005525` | `git ls-remote` SHA match | docs/evidence/PUSH_BLOCKED.json | [#8 c-5552103280](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/8#issuecomment-5552103280) | POSTED+VERIFIED |
| 13 | FIND-REUSE-005: WineDroid validate_table law — hostile-header DEX hardening, 6 readers → 1 gate | `b6ba545d` | mutf8 battery 14/14 (T7–T10 hostile-header group) | docs/research/REUSE_TRANSFER_MATRIX.md (WD-003) | [#8 c-5552280402](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/8#issuecomment-5552280402) | POSTED+VERIFIED |
| 14 | §25 dead-code audit: −10,258 LOC unreferenced experiment chain | `41946f7c` | battery 11/11; corpus 3/3; gmdice A/B identical | docs/research/REUSE_TRANSFER_MATRIX.md (DEAD-001) | [#8 c-5552280497](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/8#issuecomment-5552280497) | POSTED+VERIFIED |
| 15 | FIND-GRAVITY-VERTICAL FIXED — AOSP main-axis gravity + axis-field equality law; golden re-baselined | `d19bdd05` | helloworld 26/26 (new SHA 87820741…); corpus diff 0.09 % one element | docs/evidence/GOLDEN_HELLOWORLD.md (§RESOLVED) | [#8 c-5552280597](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/8#issuecomment-5552280597) | POSTED+VERIFIED |

## Session append — 2026-09-05 (MAXIMUM REUSE / FULL SOURCE AUDIT session)

- aapt2 tool restoration from documented Google Maven URL
  (8.13.2-14304508) after external-tool loss was caught by the battery
  (helloworld_golden FAIL → root cause: missing tool, not code). Battery
  re-run → **ALL PASS (11 stages)** on clean build. Lesson recorded: the
  zero-skip gate detects MISSING TOOLING as harness failure, per §26 law.
- This file is now the authoritative achievement map (§0 rules 7–12):
  old "Comment drafts" section retired — drafts 1–3 were superseded by
  the 11 posted comments (superset, verbatim evidence preserved in the
  issue).

## Law going forward (§38)

After every major milestone: commit → push → `git ls-remote` verify →
comment on #8 → read back via API → append row here with the real URL.
COMMENT_BLOCKED returns only if authentication is genuinely absent.
