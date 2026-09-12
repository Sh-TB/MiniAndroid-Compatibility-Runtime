# Repository Structure Migration (2026-09-12)

## Why

Before this migration the repository root carried 43 tracked files — 38 of them
markdown campaign reports, handoffs and ledgers — next to nine top-level
directories with overlapping roles (`demo/` vs `docs/demo/`, `evidence/` vs
`docs/evidence/` vs `docs/campaign014_evidence/`, `source_forensics/`,
`recovery/`, `golden/`). Runtime knowledge was spread across `miniandroid/docs/`
(313 files), `miniandroid/experiments/`, and two worklogs. The tree was honest
but unreadable; this migration gives every file exactly one canonical home
without deleting knowledge and without touching runtime behavior.

## Method

1. **Forensic inventory first** (WAVE 0): full tracked-file census — 1,752
   files: 536 md, 300 png, 297 json, 199 py, 126 cpp; per-directory counts;
   inbound-reference counting for every file to be moved.
2. **Taxonomy design** from the real inventory (not the other way around).
3. **`git mv` for every move** — rename detection kept history (664 renames).
4. **Reference repair in the same commit** so no intermediate state is broken.
5. **Validation** after migration: build, battery, goldens byte-identical
   (see the validation section below).

## Root reduction

| Metric | Before | After |
|---|---|---|
| Tracked files at repository root | 43 | 4 |
| Root markdown files | 38 | 1 (README.md) |
| Top-level directories | 10 (+2 container) | 7 (`docs`, `miniandroid`, `scripts`, `tools`, `examples`, `.agent`) |
| Top-level markdown knowledge dirs | scattered (root + `docs/` flat + `miniandroid/docs` + `miniandroid/experiments`) | one `docs/` tree with 16 role-owned subdirs |

## BEFORE root structure

```text
/                                  # 43 tracked files, 10 dirs
├── 38 markdown reports/ledgers/handoffs (AGENT_DISCOVERIES, FIXES_013,
│   MASTER_*, PASS3_*, START_HERE, worklog.md, …)
├── KNOWLEDGE_LEDGER.csv, SHA256SUMS_v0.11.3-unified-011-3.txt
├── README.md, LICENSE, .gitignore, root_registry.json
├── demo/            (demo APK source project — mixed with docs/demo/ proof)
├── docs/            (30 flat md/json + evidence/ + campaign014_evidence/ …)
├── evidence/        (3 timestamped S19 smoke dirs)
├── golden/          (legacy exp004/005 expectations, no live reader)
├── miniandroid/     (runtime project — 29 loose files at its root incl. a
│                     9.85 MB committed ELF binary `core`)
├── recovery/        (recovery forensics)
├── scripts/         (50 flat files: build/test/verify/release/forensic mixed)
├── source_forensics/(37 files)
└── tools/           (verify toolkit)
```

## AFTER root structure

```text
/
├── README.md                  # front page (10 sections, condensed)
├── LICENSE
├── .gitignore
├── root_registry.json         # canonical forensic registry (read by tools/)
├── docs/                      # ALL knowledge — see docs/README.md index
│   ├── README.md              # navigation index
│   ├── architecture/          # runtime architecture notes
│   ├── decisions/             # ADR home (indexes existing decision records)
│   ├── development/           # policies + onboarding (DO_NOT_REINVENT, STUB_DEBT, START_HERE)
│   ├── build/                 # toolchain/build docs
│   ├── testing/               # baselines, verified-test records
│   ├── compatibility/         # app/API matrices (incl. MASTER_CURRENT_GAP_MATRIX)
│   ├── research/              # root-law ledgers + source-forensics/ subtree
│   ├── evidence/              # canonical machine-verifiable evidence
│   │   ├── campaign014/       #   (was docs/campaign014_evidence/)
│   │   └── s19_smoke/         #   (was evidence/2026*)
│   ├── demos/                 # demo presentation (was docs/demo/)
│   ├── releases/              # release notes + STATUS snapshots
│   ├── maintenance/           # worklog, NOT_DONE, CLOSURE_QUEUE, recovery/
│   ├── history/               # archived campaigns, pass3, runtime-project, experiments
│   ├── runtime/               # runtime project knowledge (was miniandroid/docs/)
│   ├── agent-index/ · root-searchlight/ · tooling/ · assets/
├── miniandroid/               # runtime project (clean root: code + build + registry)
├── scripts/                   # orchestration: build/ test/ verify/ release/ forensic/ maintenance/
├── tools/                     # reusable utilities (verify/, doctor.sh)
└── examples/demo-app/         # demo APK source project (was demo/)
```

## Mapping table (old → new, by group)

### Root files → docs/

| Old path | New path | Reason |
|---|---|---|
| `README.md` | `README.md` (rewritten) | front page only |
| `AGENT_DISCOVERIES.md` … `SOURCE_CHANGES.md` (12 general-campaign docs) | `docs/history/` | archived campaign reports |
| `*_013.md` (11 campaign-013 docs) | `docs/history/campaign-013/` | campaign family kept together |
| `PASS3_*.md` (3) | `docs/history/pass3/` | audit trilogy |
| `RELEASE_NOTES_v0.0.{1,2}.md` | `docs/releases/` | release notes home |
| `CURRENT_HEAD_BASELINE.md`, `MASTER3_BASELINE_MATRIX.md`, `VERIFIED_TESTS.md` | `docs/testing/` | test methodology/baselines |
| `MASTER_CURRENT_GAP_MATRIX.md`, `docs/APP_COMPATIBILITY_REGISTRY.*`, `docs/ANDROID_BOOTSTRAP_MATRIX.*`, `docs/APK_LOADING_IMPACT_MATRIX.md`, `docs/COMPATIBILITY_CLOSURE_MATRIX.md`, `docs/EXECUTION_MATRIX.md`, `docs/RESOURCE_MATRIX.md`, `docs/MASTER_RECONCILIATION_APK_EVIDENCE.md` | `docs/compatibility/` | compatibility matrices |
| `docs/ROOT_LAW_*.md` (4), `docs/ROOT_IMPACT_MATRIX.md`, `docs/ROOT_DISCOVERY_*.md` (3), `docs/AGENT_FINDING_AUDIT.md` | `docs/research/` | root-law research ledgers |
| `HELPER_SOURCE_LIST.md` | `docs/build/` | toolchain doc |
| `START_HERE.md` | `docs/development/` | onboarding |
| `NOT_DONE.md`, `docs/CLOSURE_QUEUE.md`, `worklog.md` | `docs/maintenance/` | maintenance/queue/ledger |
| `SCREENSHOT_INDEX*.md`, `SHA256SUMS_v0.11.3-unified-011-3.txt` | `docs/evidence/` | evidence indexes/manifests |
| `KNOWLEDGE_LEDGER.csv`, `KNOWLEDGE_RECONCILIATION.md`, `MASTER_PROJECT_KNOWLEDGE.md`, `ROOT_WORKLOG.md`, `RECOVERED_*.md`, `FINAL_*.md`, `MAIN_CODER_INTEGRATION.md` | `docs/history/` | historical snapshots |
| `golden/expected_*.json` (3) | `docs/history/golden-exp004/` | legacy exp004/005 outputs; no live reader (C++ writes them relative to CWD; committed copies archived) |

### Directories

| Old path | New path | Reason |
|---|---|---|
| `demo/` | `examples/demo-app/` | WAVE-5 law: example APK **source** projects live in `examples/` |
| `docs/demo/` | `docs/demos/` | demo **presentation** lives in `docs/demos/` |
| `evidence/20260911-*` (3 dirs) | `docs/evidence/s19_smoke/` | one evidence tree |
| `docs/campaign014_evidence/` | `docs/evidence/campaign014/` | one evidence tree |
| `source_forensics/` | `docs/research/source-forensics/` | research + forensic evidence, contract preserved |
| `recovery/` | `docs/maintenance/recovery/` | historical recovery records |
| `miniandroid/docs/` (313 files) | `docs/runtime/` | runtime knowledge centralized; internal contract preserved wholesale |
| `miniandroid/experiments/` | `docs/history/experiments/` | archived experiment records |
| `miniandroid/research/` (2 notes) | `docs/architecture/` | architecture notes |
| `miniandroid/{CODER_HANDOFF_011_1,MASTER_*,OPEN_SOURCE_MASTER,RELEASE_NOTES_011_1,RELEASE_NOTES_UNIFIED_011,START_HERE}.md`, `miniandroid/status*.json` | `docs/history/runtime-project/` | runtime handoffs/state snapshots |
| `miniandroid/DO_NOT_REINVENT.md`, `miniandroid/STUB_DEBT.md` | `docs/development/` | live development policies |
| `miniandroid/TEST_MATRIX.md` | `docs/testing/` | test matrix |
| `miniandroid/{build_exp019,build_exp042,run_exp092_3run,run_exp093_3run,run_telegram_test}.sh` | `miniandroid/scripts/` | project orchestration scripts |
| `scripts/*.sh|py` (47 flat files) | `scripts/{build,test,verify,release,forensic,maintenance}/` | WAVE-4 law: orchestration subcategorized |

### Scripts taxonomy (WAVE 4)

| Dir | Role | Contents |
|---|---|---|
| `scripts/build/` | toolchain + APK/fixture builders | `bootstrap_toolchain.sh`, `build_fixture_apk.sh`, `gen_bitmap_font.py`, `gen_hello_color_art.py` |
| `scripts/test/` | regression gate + corpus acquisition | `run_test_battery.sh`, `fetch_corpus.py`, `fetch_master_campaign.py`, `g09_*` (4) |
| `scripts/verify/` | golden comparators + per-fixture pixel goldens | 6 restored comparators, `f0XX_pixel_golden.py` (10), `m3_style_geometry_check.py` |
| `scripts/release/` | release packaging + validation | `package_release.sh`, `release_clean_extract_test.sh`, `validate_release_content.py`, `release/` |
| `scripts/forensic/` | one-shot DEX/AXML probes | `andro_disasm.py`, `axml_attr_dump.py`, `dex_*` (2), `minidump_dex.py`, `m3_*` (5), `s19/s20/s21` probes (7) |
| `scripts/maintenance/` | repo maintenance utilities | `make_demo_proof.py`, `check_links.py`, `post_m3_comments.py`, `comment_urls.json`, `monitor_m9_dooz.sh`, `master_phase0.py` |

## Files removed from tip (history retains them)

| Path | Reason |
|---|---|
| `miniandroid/core` (9.85 MB ELF) | generated build artifact — violated the repo's own release-hygiene law ("generated binaries are NEVER committed"); rebuilt by `make`; now gitignored. Full history untouched (no rewrite). |

## Files kept in place (deliberate)

- `root_registry.json` — canonical machine-read registry (tools/verify/verify.py, tools/doctor.sh).
- `golden/` at root — REMOVED (archived); `miniandroid/golden/` — kept (live harness expectations).
- `miniandroid/run/` — functional run-output convention of the battery (raw run records); curated evidence lives in `docs/evidence/` (contract documented in `docs/agent-index/REPO_MAP.md`).
- `miniandroid/test_apks/` (29 .dex) — test corpus fixtures for the harness.
- `.agent/` — agent protocol state (hidden).
- Historical point-in-time records kept **verbatim** (paths inside them describe the state they recorded): `docs/evidence/SHA256SUMS_v0.11.3-unified-011-3.txt`, `docs/history/KNOWLEDGE_LEDGER.csv`, `docs/research/source-forensics/**`, auto-generated run reports under `docs/evidence/campaign014/` and `miniandroid/run/`, `docs/maintenance/worklog.md` (append-only session ledger).

## Restored content

Six battery comparator scripts existed only in the pre-push sandbox lineage
(`archive/local-main-d358a0c9-stale`); the battery references them via `$TOOLS`
but the published tip did not contain them, making EXT-01/EXT-02/G04-oracle/
G06/G07/G08 stages dependent on a directory outside the repository. They are
now restored under `scripts/verify/` and the battery resolves them in-repo
first (legacy sandbox fallback kept).

## Reference repair statistics

- Bulk path-reference rewrite: 156 tracked files updated (two-tier: literal
  `<prefix>/<name>`, then guarded bare-name).
- Hand repairs: `scripts/test/run_test_battery.sh` (TOOLS/REPOSCRIPTS resolution
  + 27 call-site paths), `examples/demo-app/{build_demo_apk,validate_demo_proof}.sh`
  (repo-root depth + APK path), `scripts/release/package_release.sh`,
  `miniandroid/scripts/run_telegram_test.sh`, `miniandroid/README.md` (7 relative
  links), `docs/releases/RELEASE_NOTES_v0.0.2.md`, `docs/demos/EVIDENCE.md`,
  `docs/build/HELPER_SOURCE_LIST.md`, `docs/development/START_HERE.md`,
  `docs/agent-index/REPO_MAP.md`.
- Link checker: `scripts/maintenance/check_links.py` (kept as a maintenance tool).
- Remaining "broken" links are **pre-existing generation artifacts**, not
  refactor regressions: absolute sandbox paths inside auto-generated evidence
  reports (`/home/z/my-project/miniandroid_ws/...`), CWD-relative image links in
  `miniandroid/run/**/report.md`, and archived upstream blob copies in
  `docs/research/source-forensics/evidence/A10_unique_blobs/`.
- One collateral corruption introduced and reverted during the bulk pass:
  `miniandroid/golden/expected_view_tree.json` references inside
  `docs/testing/MASTER3_BASELINE_MATRIX.md` and the SHA manifest were
  accidentally rewritten to the archived copy's path; restored verbatim
  (SHA re-verified: `50120e00…`).

## Validation (post-migration)

See commit message and the validation section of the session worklog:
clean build, full regression battery, Hello Color / ChessClock / TicTacToe /
HelloWorld goldens byte-identical, demo proof validator PASS, markdown link
check, `git status` clean. No runtime source file was modified
(`git diff <pre-migration-HEAD> -- miniandroid/src` is empty except the
removed generated binary).
