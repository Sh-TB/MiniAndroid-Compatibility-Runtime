# MiniAndroid Documentation

This is the official entry point for all project documentation. The repository
root stays minimal: code lives in `miniandroid/`, orchestration in `scripts/`,
reusable utilities in `tools/`, and **all knowledge lives here, in `docs/`**.

| Directory | Role |
|---|---|
| [`architecture/`](architecture/) | Runtime architecture notes (Dalvik comparison, architecture decisions) |
| [`development/`](development/) | Developer policies and onboarding (`DO_NOT_REINVENT`, `STUB_DEBT`, `START_HERE`) |
| [`build/`](build/) | Toolchain and build documentation (`HELPER_SOURCE_LIST` — every tool, version, license) |
| [`testing/`](testing/) | Test methodology, baselines, verified-test records |
| [`compatibility/`](compatibility/) | App-compatibility matrices, API coverage, execution matrices |
| [`research/`](research/) | Root-law research ledgers, discovery guides, source forensics |
| [`evidence/`](evidence/) | Machine-verifiable forensic evidence (provenance, SHA manifests, per-case records) |
| [`demos/`](demos/) | Demo presentation: proof GIF, contact sheets, evidence manifests |
| [`releases/`](releases/) | Release notes (v0.0.1 → v0.0.5-Silkie) and status snapshots |
| [`decisions/`](decisions/) | Architectural decision records |
| [`maintenance/`](maintenance/) | Repository maintenance, migration records, work queue, session worklog |
| [`history/`](history/) | Archived campaign reports, superseded investigations, historical snapshots |
| [`runtime/`](runtime/) | The runtime project's own knowledge base (EXP reports, knowledge, research) |
| [`agent-index/`](agent-index/) | Machine-readable navigation caches (symbol index, test graph, hotspots) |
| [`root-searchlight/`](root-searchlight/) | Root-evidence searchlight records and ledgers |
| [`tooling/`](tooling/) | Tooling baseline record |
| [`assets/`](assets/) | Front-page images and derived-image provenance |

## Start here

- New to the project: [`development/START_HERE.md`](development/START_HERE.md)
- What exists and why (policies): [`development/DO_NOT_REINVENT.md`](development/DO_NOT_REINVENT.md)
- How "proven" is defined: [README — Verification & evidence](../README.md#verification--evidence)
- Current honest state: [`releases/STATUS_MC4_2026-09-12.md`](releases/STATUS_MC4_2026-09-12.md)

## Evidence quick access

| Case | Path |
|---|---|
| Hello Color (real-APK rendering proof) | [`evidence/hello_color_golden/`](evidence/hello_color_golden/) |
| TicTacToe interactive golden | [`evidence/tictactoe_golden/`](evidence/tictactoe_golden/) |
| ChessClock real screenshot | [`evidence/campaign3_chessclock_real_screenshot/`](evidence/campaign3_chessclock_real_screenshot/) |
| Telegram v12.10.1 frontier | [`evidence/mc4_telegram/`](evidence/mc4_telegram/) |
| Campaign-014 corpus sweep | [`evidence/campaign014/`](evidence/campaign014/) |
| S19 smoke records | [`evidence/s19_smoke/`](evidence/s19_smoke/) |
| Demo proof (GIF + manifests) | [`demos/`](demos/) |

## Registry

Every root fix/tracker (F-xxx, R-NEW-xxx, P0–P3, OBSERVED-FAIL /
IMPLEMENTED / VERIFIED-FIXED) has exactly one home: [`root_registry.json`](../root_registry.json)
at the repository root, read by [`tools/verify/verify.py`](../tools/verify/verify.py)
and [`tools/doctor.sh`](../tools/doctor.sh).

## Related

- Runtime project README: [`miniandroid/README.md`](../miniandroid/README.md)
- Regression battery: `scripts/test/run_test_battery.sh`
- Verification toolkit: `tools/verify/`
