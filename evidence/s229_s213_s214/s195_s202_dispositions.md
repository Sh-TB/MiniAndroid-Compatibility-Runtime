# S213-D — disposition audit: evidence/s195_audit/ + tictactoe_s195fix_r1/ + evidence/s202_625_forced/

Measured 2026-11-13 at the S229 wave working tree (#587 S213-D). No deletion performed;
per the S214 frozen-area law `evidence/s195_audit/` accepts no new files and content may
migrate only with this disposition ledger + consumer checks.

## 1. `evidence/s202_625_forced/` — NOT PRESENT

`git log --all --full-history -- "evidence/s202_625_forced/*"` is empty: the path has
**no commit history on main**. Honest finding: the named path exists only as an
owner-local working directory (or predates this repo's tracked history); there is
nothing tracked to audit or classify. Recorded as NOT_PRESENT with this note.

## 2. `evidence/s195_audit/` — 252 tracked files (frozen)

Breakdown: 144 JSON + 33 JSONL + 36 MD + 11 patch + 6 JPG + 3 PNG + 3 db + 3 -shm/-wal
+ 3 lck + store-tree residue under `cohort/runs/store_*` (captured app data: caches,
`.lck` lock files, `profileInstalled` markers — these are part of the recorded store
trees, i.e. evidence of the recorded runs, not repository residue).

| class | members | disposition |
|---|---|---|
| compact reproducibility metadata | 144 JSON, 33 JSONL, 36 MD (traces, summaries, reports) | KEEP — this is the minimal proof set |
| patches (reconstructed S196–S198 chain) | 11 `.patch` (incl. 1 TRUNCATED, labelled) | KEEP — provenance of the reconstruction; TRUNCATED member is self-labelled |
| canonical per-run faces | 6 JPG (`cohort/face_*_s195_r1.jpg`) | KEEP — already compact JPEG, the S213 preferred format |
| raw visual output | 3 PNG screenshots (gmdice_s195_r1 2.9 MB-class, tictactoe_s195fix_r1 3.36 MB, spot_halma) | MIGRATE_CANDIDATE at the #386 migration wave: replace by optimizer JPEG derivatives (demonstrated below), keep the PNG only if a pixel-exact claim needs it |
| captured app-data stores | `store_*/` trees incl. sqlite db/-shm/-wal, .lck | KEEP inside the frozen store trees (recorded run state; not repo residue) |

## 3. `evidence/s195_audit/cohort/runs/tictactoe_s195fix_r1/` — 5 files

| file | bytes | disposition |
|---|---:|---|
| `report.md` | 2,170 | KEEP (compact claim record) |
| `trace_summary.json` | 21,978 | KEEP (machine summary) |
| `trace.jsonl` | 12,839 | KEEP (full trace, compact) |
| `lifecycle_trace.json` | 994 | KEEP |
| `screenshot.png` | 3,360,833 | **MIGRATE_CANDIDATE**: photographic 1080x1920 PNG; optimizer demonstration produced a 99,178 B JPEG (q75, 540x960, RMS-Δ 0.634, 33.89x smaller) at `evidence/s229_s213_s214/conversion_demo/` with the full SHA-256 mapping in `conversion_demo/tictactoe_conversion.json`. The frozen-area original stays untouched until the migration wave swaps it per this ledger. |

## 4. Per-run folder policy (enforced going forward)

Run metadata (APK SHA, runtime commit, command, environment, run ID, claim, hashes,
status) belongs in ONE compact machine-readable summary per run — the
`trace_summary.json` + `report.md` pair here already models that shape. Promote only the
minimal visual asset (one JPEG face). Raw frames default to ignored
`.cache/<suite>/<run-id>/`; promotion into tracked evidence is an explicit review step
(now enforced by `tools/policy_validator.py`: frozen-area snapshot drift + image policy +
scratch-residue rules reject any new per-run dumping ground).
