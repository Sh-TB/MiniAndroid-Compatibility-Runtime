# MAIN_CODER_INTEGRATION — master-request execution record (2026-09-02)

## PASS 2 ADDENDUM — reconciliation completion (2026-09-03)

Second master-request pass, executed on top of Pass 1 (HEAD was 0fd1ad6).
Still **PUSH_BLOCKED_PENDING_USER_REVIEW** — remote main untouched at bbe0ce3
(re-verified via git ls-remote at pass start; bbe0ce3 remains an ancestor).

| item | value |
|---|---|
| Pass-2 base | 0fd1ad6 (Pass-1 integration HEAD) |
| Remaining valid missing fixes found | K-18 switch dispatch, K-19/K-20 parse+substring/concat bridge, K-29 div/rem÷0, K-32 neg/not family (audit escalated: never implemented), K-31 lit8 opcode table shifted vs AOSP (NEW discovery, K-06 bug class) |
| Implementing commit | 9d095f9 (code + discriminating fixture + before/after evidence) |
| Evidence | tests/semantic_switch_parse_neg_test.cpp **0/25 → 25/25** (run/semantic_reconciliation2/before_fix_FAIL.txt / after_fix_PASS.txt) |
| Regression gate | **ZERO** — simplestopwatch 2a12587a BASELINE_MATCH (×3 determinism), gmdice/microtimer/unote/dooz byte-identical, old fixtures 59/59; dooz runtime 0.9 s → 69.9 s with identical final SHA (K-33 — more Compose bytecode now executes) |
| Real-APK impact | chessclock + headingcalculator left the shared default screen (eb16ab5c) and now render app-specific UI (SeekBar / resource-backed ListView); bgclock renders its themed window; simplekeyboard/openlauncher unchanged (still default); droidify.apk = truncated download (data-loss family, not code); run/master_reconciliation_apks/ |
| Docs commit | cc5ca8e (K-18/19/20/29 → VERIFIED+FIXED; K-31/K-32/K-33 added; NOT_DONE resolved items struck; VERIFIED_TESTS 25/25 row) |
| Handoff | MiniAndroid_CANONICAL_MASTER_RECONCILED_<HEAD>.zip (full non-shallow .git, clean tree, extraction-verified: fsck + build + fixtures rerun) |
| Push status | **NO PUSH performed** — fast-forward path documented and still valid |

## Original Pass-1 record (2026-09-02)

Final state: **PUSH_BLOCKED_PENDING_USER_REVIEW**
Repository: https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime (MASTER — user's own project; NOT a fork; no upstream exists)

## Identity block

| item | value |
|---|---|
| GitHub master HEAD before integration | `bbe0ce3` (EXP-098/CM-027, branch `main`, 0 tags) |
| Original local HEAD (candidate) | `894eae2` = tag `v0.14.0-partial` (branch `campaign-014`, on top of `2ede367` = `v0.13.0`) |
| Integration branch | `integration/master-reconciliation` |
| Integration final commit | **this commit** — parent `0212a5d` (docs) ← `6fda28d` (semantic fix) ← `894eae2` (candidate) |
| Commits reconciled | candidate lineage `bbe0ce3 → … 121 commits → 894eae2` + 2 integration commits; full history 353 commits (re-unified from master — was shallow at `a9434de`) |
| Files reconciled (code) | `miniandroid/src/dex/dalvik_engine.cpp` |
| Files reconciled (docs) | `README.md` (full rewrite), `MASTER_PROJECT_KNOWLEDGE.md`, `FINAL_STATE.md`, `NOT_DONE.md`, `VERIFIED_TESTS.md`, `AGENT_DISCOVERIES.md`, `MAIN_CODER_INTEGRATION.md` |
| Comments added | knowledge-preserving IMPORTANT comments at: ARITH_LONG / ARITH_WIDE_2ADDR / CMP_LONG / CMP_FLOATING / CONV_SRC_* / bits_l2d helpers (each states the old bug + fixture) |
| Findings verified | K-01..K-30 in MASTER_PROJECT_KNOWLEDGE.md (incl. RESULT_001/003/007/009/010/012/013/014/016 verdicts) |
| Findings fixed this pass | K-01 long arith 64-bit · K-02 cmp-long 64-bit · K-03 NaN ordering + double width · K-04 real conversions · K-05 12x register extraction |
| Findings rejected | exp018 "parse* NATIVE_CPP implemented" (K-19); campaign-012 "f5da664 = v0.12.0" provenance (K-27) |
| Findings still unknown/open | Compose composition boundary (K-24), GLES dispatch hook (K-25), campaign-014 lost code (K-28), Canvas matrix exhaustiveness (K-23) |
| Tests executed | matrix ×2 (pre/post fix) + 6 fixtures + ARSC probe — see VERIFIED_TESTS.md |
| Tests passed | semantic 14/14 · unified0112 5/5 · unified0113 8/8 · F5 return-wide 5/5 · handler 23/23 · simple 4/4 · ARSC probe 3/3 layouts |
| Tests failed | telegram_v12 (golden APK data lost — NOT a code regression), stopwatch (known-corrupt APK), tictactoe (0-byte corpus APK) |
| Regressions | **ZERO** — simplestopwatch `2a12587a` BASELINE_MATCH preserved; gmdice/microtimer/unote/dooz byte-identical pre/post fix |
| Backup locations | `BACKUP_GITHUB_MASTER_bbe0ce3.bundle` (146 MB) + `GITHUB_MASTER_BACKUP_SHA256.txt` in the delivery folder; local rescue tag `pre-integration-local-rescue` = `894eae2` |
| Exact integration HEAD | **this commit** — verify: `git rev-parse HEAD` on branch `integration/master-reconciliation` (parent `0212a5d`) |

## Why the semantic fix was justified (§4 pipeline, condensed)

AGENT/campaign-012 claims said cmp-long/long-arith/conversions were fixed →
source inspection showed the int32-union shortcut STILL in the live dispatch →
runtime-path analysis proved `execute_method → execute_method_internal →
fetch_decode_execute` is the real-APK path → reproduction: new fixture FAILED
12/14 on the old code → classification VERIFIED (bug present) → fix applied →
independent validation 14/14 PASS + zero regression matrix → integrated.

## Restore procedures (§18)

```bash
# A) restore the exact pre-integration GITHUB master state
git clone BACKUP_GITHUB_MASTER_bbe0ce3.bundle restored_master && cd restored_master
git rev-parse HEAD          # bbe0ce3067401211af35402483b96baae69220df
# (or simply: the live GitHub main is untouched — no push happened)

# B) restore the exact pre-integration LOCAL candidate state
git fetch <integration-repo> tag pre-integration-local-rescue
git checkout pre-integration-local-rescue     # = 894eae2 (v0.14.0-partial lineage)

# C) continue from the integration branch
git checkout integration/master-reconciliation  # HEAD = this integration's final commit (parent 0212a5d)
```

## Push procedure — ONLY after explicit user approval (§3/§20)

```bash
git remote add github https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime.git
git push github integration/master-reconciliation:integration/master-reconciliation
# fast-forward main ONLY if the user explicitly approves:
#   git push github integration/master-reconciliation:main   # fast-forward, NO force
```
No force-push, no reset, no history rewrite — `bbe0ce3` is an ancestor of
`0212a5d`, so main can advance by fast-forward alone.

## Review package (§19)

`MiniAndroid_MASTER_INTEGRATION_REVIEW.zip` — source + full `.git` (353 commits,
all tags/branches) + this documentation set. NO APKs. SHA256 alongside.
