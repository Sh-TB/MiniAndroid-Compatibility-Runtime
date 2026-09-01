# SCREENSHOT_INDEX — UNIFIED_011.3 (§39)

Every screenshot evidence artifact produced/verified by this campaign, with SHA256
and interpretation. Files ≤100 KB policy; large run outputs stay external
(git-ignored), curated copies live under `docs/evidence/u011_3/`.

## Baselines (regression matrix, 3 runs each, all deterministic)

| App | Screenshot | SHA256 (first 16) | non-white px | Interpretation | Evidence file |
|---|---|---|---|---|---|
| Telegram v12 | first frame | `088ea640587ec0d2` | 41,233 | GOLDEN PRESERVED — identical to v0.11.1 lineage anchor (3/3 runs) | docs/evidence/u011_3/matrix_summary.json |
| SimpleStopwatch | first frame | `2a12587a0acf196c` | 916,815 | 011.2 anchor preserved (real icons + strings; 3/3) | matrix_summary.json |
| GMDice | first frame | `472c1d3c0ee12330` | 158,040 | real UI preserved (text row + Roll it! + dice bar; 3/3) | matrix_summary.json |
| microtimer / unote | first frame | `eb16ab5c68fa9b6c` | 23,472 | default shared screen (entry-chain/ARSC gap — honest L1) | matrix_summary.json |
| dooz / tictactoe | first frame | `31ddd4d5b8e6d18e` | 0 | blank (Compose runtime / libGDX — known BLOCKED) | matrix_summary.json |

## Interaction evidence (this campaign's §23 chain)

| Artifact | SHA256 (first 16) | Meaning |
|---|---|---|
| docs/evidence/u011_3/clicktest/ssw_before.png | (frame-1 baseline of the click run) | Start/Reset buttons + icon row (frame 1) |
| docs/evidence/u011_3/clicktest/ssw_onButtonStart_after.png | (second frame after REAL click) | **"Stop" / "Lap"** — app's true running state rendered through the full pipeline |
| docs/evidence/u011_3/oracle/ssw_start.json | — | changed_px=12,373 (0.597%), bbox (24,4)-(793,1919), bottom-third 12,051 px |
| docs/evidence/u011_3/oracle/ssw_start_diff.png | — | amplified pixel-diff visualization |
| docs/evidence/u011_3/clicktest/ssw_report.json | — | onButtonStart/onButtonReset: dispatched=true, 12,439 px each; settings/menu correctly not dispatched (no listeners) |
| docs/evidence/u011_3/clicktest/gmdice_report.json | — | roll click dispatched=true, listener=GameMasterDice, **changed_px=0** — honest: runtime-constructed views gap |
| docs/evidence/u011_3/oracle/gmdice_roll.json | — | before/after oracle for the roll click (181,512 px number from 011.2 RECLASSIFIED as render artifact) |

## Reclassified historical evidence

| Artifact | Status |
|---|---|
| docs/evidence/u011_2/clicktest/gmdice_after.png ("181,512 px") | retained as historical record; captioned in RECOVERED_11_1_TO_HEAD_DELTA.md §2 as a render-path artifact (near-blank frame) — NOT app-driven pixels |
| docs/evidence/u011_2/clicktest/ssw_onButtonStart_after.png ("918,207 px") | same reclassification |

## Real-app probe evidence (§19/§20)

| Artifact | Content |
|---|---|
| docs/evidence/u011_3/real_apps/whatsapp_probe_tail.txt | entry chain: AppShell onCreate → Main.onCreate → obfuscated LX/* helpers; typed catches firing; final stall in LX/0F7 (threading) |
| docs/evidence/u011_3/real_apps/signal_probe_progress.txt | 2.8M instructions into androidx camera/lifecycle init; LiveData ISE handled by the new machinery |

## Verification

SHA256SUMS for the curated evidence set are recorded in the handoff manifest
(`SHA256SUMS` file inside MiniAndroid_v0.11.3_GIT_HANDOFF.zip) and the ZIP's own
SHA256 in VERSION_HANDOFF_MANIFEST.md.
