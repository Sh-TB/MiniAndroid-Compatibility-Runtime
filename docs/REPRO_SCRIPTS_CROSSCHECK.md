# REPRO SCRIPTS CROSS-CHECK (continuation §12 / CONT-T12)

1:1 cross-check of the six reproduction scripts required by campaign issue **#361**
("[TELEGRAM] Knowledge transfer 5/7 — the tools: full source of all six reproduction
scripts + the forensic probe kit", 2026-09-29) against the current repository tree.

Date of check: 2026-10-03 (working tree, no commit made).
Pre-registered audit requirement: `docs/FORENSIC_MISSING_EVIDENCE.md` §M10
("file-by-file verification that the six scripts quoted in #361 exist in `scripts/`
under the same names; issue-body copies are canonical until then") and
`docs/FORENSIC_UNVERIFIED_CLAIMS.md` §U7 (status PARTIAL).

## Verdict at a glance

**All SIX requested script names were recoverable from repo sources.
ZERO of the six exist in the repository. ZERO were ever committed
(0 git-history path appearances each). No renames or replacements found.**
The issue-body source copies quoted in #361 remain the only canonical record,
exactly as `FORENSIC_MISSING_EVIDENCE.md` §M10 anticipated.

## Where the six names were recovered from (search record)

| Source searched | Result |
|---|---|
| `worklog.md` (624 KB) | `rg '(?i)(six reproduc\|reproduc[a-z]* script\|repro script)'` → **0 matches**; `rg '(?i)(tg_run\|proof_pack\|dump_official\|s117_disas\|s118_samples\|s117_gates)'` → **0 matches**. The scripts are never mentioned in the worklog. |
| `docs/FINAL_COMPATIBILITY_CAMPAIGN.md` | No repro-script list, no six names (grep `repro\|six\|s117\|s118\|s119` → unrelated golden-reproduction rows only). |
| `docs/MASTER_WORKLIST.md` | No repro-script list, no six names (grep for the names → 0 matches; only "#356-#363 ↔ M-07" reconciliation row at L9534). |
| `docs/ARTIFACT_LIFECYCLE.md` | No script-name list (generic lifecycle laws only). |
| `docs/FORENSIC_MISSING_EVIDENCE.md` | §M10 "Six reproduction scripts 1:1 cross-check" — defines this audit; names not listed there. |
| `docs/FORENSIC_UNVERIFIED_CLAIMS.md` | §U7: "#361 claims 'full source of all six reproduction scripts' in the issue body … a 1:1 mapping of the six quoted scripts was not verified file-by-file … treat the issue-body copies as the canonical record." |
| `docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl` | FR-361 row: request_text "[TELEGRAM] Knowledge transfer 5/7 — the tools: full source of all six reproduction scripts + the forensic probe kit". |
| `docs/REPO_HYGIENE_FORENSICS.md` | No six-script list (grep `repro\|script` → 2 unrelated lines). |
| `docs/AUDIT_REQUIREMENT_COVERAGE.jsonl` | Script list present but for a different work item (load-audit: `load_audit_proof.sh`, `loading_probe_runner.sh`, `storage_tree_proof.sh`, `working_vs_failing_probe.sh`) — **not** the #361 six. |
| `forensic_data/issues_all.json` (365 issues fetched & preserved in-repo) | **HIT — canonical record.** Issue #361 body (41,916 chars) quotes the complete source of exactly six scripts under `### \`scripts/<name>\`` headers. Corroborated by sibling issues #356 (all six names), #357, #358, #359, #360, #363 (`s117_tg_run` + others). |

### The six requested names (verbatim from the #361 issue body)

1. `scripts/s117_tg_run.sh` — "the stable Telegram run protocol"
2. `scripts/s117_gates.py` — "the three regression gates"
3. `scripts/s117_dump_official.py` — "DEX ground-truth dump of the official APK"
4. `scripts/s117_disas.py` — "DEX path disassembly"
5. `scripts/s118_samples.py` — "sample-image generation from run data"
6. `scripts/s119_proof_pack.py` — "the live proof pack (fresh run + annotated map)"

(`scripts/dalvik_walker.py` is referenced in the same issue but explicitly described as
"already in the repository" — an auxiliary instrument, not one of the six.)

## Cross-check table (STATUS — RESULT — EVIDENCE per row)

| # | Requested name | Exact repo path | Executable (Y/N) | Current behavior (from canonical issue-body source copy) | Renamed/replaced? | Evidence (STATUS — RESULT — EVIDENCE) |
|---|---|---|---|---|---|---|
| 1 | `s117_tg_run.sh` | `scripts/s117_tg_run.sh` | **N/A — file absent** | Bash wrapper: deterministically execs `miniandroid/build/miniandroid run` on `upload/tg/telegram_official.apk` or `upload/tg/forkgram.apk` with a per-target fixed data-root, 1080x1920 screen, 120 s budget, output dir as argv (comment header: "S117 G8 — deterministic Telegram run protocol (pinned for all waves)"). | **No.** No replacement anywhere; nothing in `scripts/` implements the official/forkgram protocol wrapper. | **MISSING — RESULT: not in repo, never committed.** EVIDENCE: `ls -la scripts/s117_tg_run.sh` → "No such file or directory"; `git log --all -- scripts/s117_tg_run.sh` → empty (0 path appearances repo-history-wide); untracked-dir scan (tmp/, run/, upload/, evidence/, miniandroid/, canonical/, registry/, audit/, fixtures/, games/, examples/, tool-results/) → 0 hits. Source copy: `forensic_data/issues_all.json` issue #361 body. |
| 2 | `s117_gates.py` | `scripts/s117_gates.py` | **N/A — file absent** | Python gate runner: runs the engine on breakout / ballbreak / dooz APKs and compares each screenshot SHA-16 against pinned S114/S111 anchor baselines ("verify the fresh HEAD rebuild reproduces the … anchor baselines before any engine change"), printing a JSON report of rc / sha16 / errors / status per gate. | **No.** `scripts/s112_gates.py` exists but is an earlier, different-session gate script (not a rename of this one). | **MISSING — RESULT: not in repo, never committed.** EVIDENCE: `ls -la` → "No such file or directory"; `git log --all --` → 0 path appearances; repo-wide basename scan → 0 hits. Source copy: issue #361 body. |
| 3 | `s117_dump_official.py` | `scripts/s117_dump_official.py` | **N/A — file absent** | Multi-DEX method dumper for the OFFICIAL Telegram APK (`upload/tg/telegram_official.apk`): for given `Lclass;` + method names, dumps matching methods from every `classes*.dex` with raw Dalvik disassembly (opcode + registers + string/field/method operands). | **No.** `scripts/s115_tg_dexdump.py` is a similar-purpose but earlier, different-session tool targeting `forkgram.apk` — not a rename/replacement. | **MISSING — RESULT: not in repo, never committed.** EVIDENCE: `ls -la` → "No such file or directory"; `git log --all --` → 0 path appearances; repo-wide basename scan → 0 hits. Source copy: issue #361 body. |
| 4 | `s117_disas.py` | `scripts/s117_disas.py` | **N/A — file absent** | Full-opcode Dalvik disassembler window for the official Telegram APK: `s117_disas.py <Lclass;> <method> [start_pc] [end_pc]` with an empirically calibrated opcode-width table (the "ground-truth instrument" behind the chain's forensic claims, e.g. 842/844 exact paths walked on MessagesStorage). | **No.** `scripts/s117_disasm_createview.py` (tracked, committed) shares the `s117_disas…` prefix but is a different, narrower tool (disassembles one `createView` site in forkgram.apk) — a near-name collision, NOT a rename. | **MISSING — RESULT: not in repo, never committed.** EVIDENCE: `ls -la` → "No such file or directory"; `git log --all --` → 0 path appearances; repo-wide basename scan → 0 hits (only prefix-collision `s117_disasm_createview.py`). Source copy: issue #361 body. |
| 5 | `s118_samples.py` | `scripts/s118_samples.py` | **N/A — file absent** | Sample-image generator for the Telegram state + knowledge-transfer pack: from run data produces (1) the latest official-Telegram render frame, (2) an annotated view-tree geometry map from `view_tree.json` showing the login UI with real text/positions/colors, (3) an S117-placeholder-vs-S118 side-by-side, plus a gate-proof montage; outputs under `download/s118_samples/`. | **No.** `scripts/s118_post_comments.py` exists but is an issue-comment poster (different session/purpose) — prefix collision only, NOT a rename. | **MISSING — RESULT: not in repo, never committed.** EVIDENCE: `ls -la` → "No such file or directory"; `git log --all --` → 0 path appearances; repo-wide basename scan → 0 hits. Source copy: issue #361 body. |
| 6 | `s119_proof_pack.py` | `scripts/s119_proof_pack.py` | **N/A — file absent** | "Live proof pack" builder: takes a fresh official-Telegram run's `screenshot.png` / `view_tree.json` / `run.log` and emits evidence images (`01_fresh_frame_today.png`, `02_geomap_annotated.png` with ink-event proof, `03_what_engine_paints.png` 2-up raw-vs-annotated) under `download/telegram_proof/`. | **No.** `scripts/s119_calibrate*.py` / `scripts/s119_package.py` exist but are different-session packaging/calibration tools — prefix collisions only, NOT renames. | **MISSING — RESULT: not in repo, never committed.** EVIDENCE: `ls -la` → "No such file or directory"; `git log --all --` → 0 path appearances; repo-wide basename scan → 0 hits. Source copy: issue #361 body. |

## Executable-bit remediation

Nothing to remediate: none of the six files exists, so no `chmod +x` was performed
and no file mode was changed. (Task instruction "if a script lost its executable bit"
is vacuously satisfied — there is no file to lose a bit.)

## Why this result is consistent with the repo's own records

- `FORENSIC_UNVERIFIED_CLAIMS.md` §U7 already classified the claim as PARTIAL: "The repo
  carries many `scripts/s1*.sh` artifacts, but a 1:1 mapping of the six quoted scripts
  was not verified file-by-file in this pass; treat the issue-body copies as the
  canonical record until cross-checked." This cross-check confirms the strong form:
  the six scripts were **never committed at all** (0 git-history path appearances each,
  including `--all`), so no later rename could have occurred either.
- `FORENSIC_MISSING_EVIDENCE.md` §M10 lists exactly this file-by-file verification as
  missing evidence; the issue-body copies (preserved verbatim in
  `forensic_data/issues_all.json`, issue #361, fetched 2026-10-02 per worklog
  FORENSIC-365 entry "issues #1-365 metadata + 708 comments … fetched (forensic_data/)")
  remain the canonical record.
- The scripts were authored during the Telegram knowledge-transfer conversation chain
  (issues #356–#363, sessions S117→S119 per issue #356) inside an external sandbox;
  `FORENSIC_ALL_REQUESTS_LEDGER.jsonl` FR-357..363 notes the journey markdown itself was
  also never committed ("TELEGRAM_JOURNEY_S117_S119.md never committed (dead preview
  link)" — worklog FORENSIC-365 KEY FINDINGS). The six scripts share that fate.

## Name-collision caution (do not confuse with the requested six)

The repo's own S117–S119 *worklog session* numbering produced unrelated, committed
scripts with colliding prefixes: `scripts/s117_complete_graphics.py`,
`scripts/s117_disasm_createview.py`, `scripts/s118_post_comments.py`,
`scripts/s119_calibrate.py`, `scripts/s119_calibrate2.py`, `scripts/s119_calibrate3.py`,
`scripts/s119_package.py` (plus earlier Telegram tooling `scripts/s115_tg_dexdump.py`,
`scripts/s112_gates.py`). None of these reproduces a requested #361 script under a
different name; they are listed here only to prevent a future reader from mistaking
them for the six.

## Required follow-up (for the owner)

To close §M10 / FR-361 §U7: commit the six scripts from the issue-body copies (or a
fresh authoritative copy) under the exact names above in `scripts/`, set the
executable bit, and re-run this cross-check. This document deliberately does NOT
recreate the scripts (no files were created other than this report, per task scope).

— Generated by CONT-T12 cross-check agent. No commit made.
