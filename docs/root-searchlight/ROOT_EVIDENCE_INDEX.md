# ROOT EVIDENCE INDEX — LIVE

Evidence precedence: LIVE EVIDENCE > LOCAL CODE > UPSTREAM SOURCE > CLAIM.
Every row must point at a real artifact in the repo (commit-pinned at HEAD `0383f19f`).

## 1. Battery / regression gate
- `scripts/test/run_test_battery.sh` — 91 stages ALL PASS at `0383f19f`
  (semantic battery + MUTF-8 + goldens + F-024/025/026/027/028/030/040/044/050 fixtures).
- 3-run byte-identical law fixtures: f024 (32b8a456…), f028 (…), f044 (32b8a456…), f040.

## 2. Golden deliverables (user-mandated sentinels)
- `docs/evidence/hello_color_golden/` — colorful Hello World (bitmap image +
  stroke-border boxes) rendered end-to-end; frame SHA 11e0056320d8546dbb…,
  1080x1920, per-element pixel counts (evidence.json). Merge-verified:
  `miniandroid/run/m9_merge_hc/screenshot.png` byte-identical at the merged tree.
- `miniandroid/run/m9_merge_dooz/` — dooz at merged tree: rc=0 SUCCESS,
  ComposeView children=0, 0/2073600 non-white (HONEST: blank), no exceptions;
  lifecycle reached onResume; [REC-MISS] Window.setDecorFitsSystemWindows observed.

## 3. Per-root law evidence (F-XXX ledger)
- `docs/research/ROOT_LAW_GLOBAL_AUDIT.md` — families A–Z reconciled; per-root rows with
  micro-proof + real-APK columns and commit pins.
- `docs/research/ROOT_IMPACT_MATRIX.md`, `docs/research/ROOT_LAW_COMPLETENESS_MATRIX.md`,
  `docs/research/ROOT_DISCOVERY_GUIDE.md`, `docs/research/ROOT_DISCOVERY_EVIDENCE.md` (F-044 worked example).
- `F023_ROOT_CAUSE.md` — the Compose host chain (9+1 laws, M3).
- `docs/compatibility/MASTER_CURRENT_GAP_MATRIX.md`, `docs/history/MASTER_CAMPAIGN4_FINAL_REPORT.md`.

## 4. Machine-readable
- `root_registry.json` (project root) — 286 roots, status/priority/evidence/next.

## 5. Forensic tooling (real-APK DEX ground truth)
- `scripts/forensic/minidump_dex.py`, `scripts/f023_disasm.py`, `scripts/exp059_disasm.py`,
  `scripts/m6_*` — precise DEX oracles used for every F-law diagnosis.

## 6. Evidence status vocabulary
RESEARCHED / IMPLEMENTED / TESTED / OBSERVED / VERIFIED / REGRESSION / FAILED /
FALSE_LEAD / BLOCKED / UNPROVEN — never mixed (tool-output ≠ root-proof).
