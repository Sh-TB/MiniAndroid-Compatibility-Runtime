# FORENSIC ALL REQUESTS LEDGER — human companion (issue #365)

The machine ledger is **`docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl`** (390 rows;
regenerate with `python3 scripts/forensic_ledger.py`). Every row carries the
#365 §18 fields: `request_id, parent_id, issue, source, date, request_text,
acceptance_criteria, claimed_status, verified_status, evidence_level,
commit_shas, test_refs, runtime_refs, screenshot_refs, regression_refs,
blockers, superseded_by, explanation`.

## Method

1. **Corpus reconstruction**: all 365 GitHub issues (state=all, zero PRs), all
   708 issue comments (all authored by the owner — i.e. they are requests/
   directives, not independent verification), all 597 commits, the `.agent`
   request files, worklog (5,932 lines), and 7 registries were fetched and
   cross-joined. Dates + commit ancestry were used to avoid double counting.
2. **Deduplication/aliasing**: per-title issues joined to registries by package
   and by `ISSUE_NUMBER`; MG/F-NEW/R-NEW/ROOT/GAMES/S-ids joined by ID tokens
   extracted from commit messages.
3. **Classification**: strict #365 §2 vocabulary; registry raw statuses were
   normalized (mapping documented in `scripts/forensic_ledger.py:
   norm_root_status`); synthetic-class evidence capped at TESTED/E2 per §23;
   checked-box claims downgraded to OBSERVED unless re-executed.
4. **Current-HEAD truth (§20)**: the four gates listed in
   `FORENSIC_REGRESSION_STATUS.jsonl` were re-run at HEAD during this campaign.

## Row families

| Range | Family | Rows |
|---|---|---|
| FR-001..008 | EXP era + evidence ledger | 8 |
| FR-009 | MASTER-ROADMAP v3 (superseded) | 1 |
| FR-010..023 | EXEC app issues | 13 |
| FR-024 | S81 corpus parent | 1 |
| FR-025..226 | 202-title compatibility reports | 202 |
| FR-227..233 | root-cause issues + S84 + MG parent | 7 |
| FR-234..333 | micro-gap tickets | 100 |
| FR-334..341 | GAMES waves | 8 |
| FR-342..352 | F-NEW-165..170 + S102-A..D | 11 |
| FR-353..363 | HTML5 / GAMES master / Telegram / knowledge transfer | 11 |
| FR-364, FR-365 | current master requests | 2 |
| FR-NI-* | non-issue requests (coder request 001, loading master execution, Telegram 190-goal parent + 18 checked goals, hygiene, README/UI, journey doc, registry-sync row) | 25 |

## §19 statistics (computed from the JSONL — reproducible)

| Status | Rows |
|---|---|
| VERIFIED | 30 |
| TESTED | 82 |
| OBSERVED | 105 |
| PARTIAL | 43 |
| PENDING | 122 |
| BLOCKED | 5 |
| SUPERSEDED | 2 |
| UNVERIFIED_CLAIM | 1 |
| REGRESSED | 0 |
| **Total** | **390** |

Evidence levels: E0=122 · E1=6 · E2=112 · E3=87 · E4=50 · E5=13.

Interpretation guardrails: PENDING is dominated by the never-executed 202-title
reports and the 172 unchecked Telegram goals — i.e. honest open roadmap, not
lost work. UNVERIFIED_CLAIM is deliberately tiny (1) because the audit found
the claims it audited were either evidenced (TESTED/OBSERVED) or already
recorded as open — with the specific exceptions catalogued in
`FORENSIC_UNVERIFIED_CLAIMS.md`.

## Companion documents

- `FORENSIC_CLAIMS_VS_EVIDENCE.md` — executive truth + statistics
- `FORENSIC_VERIFIED_WORK.md` — evidence-backed achievements
- `FORENSIC_UNVERIFIED_CLAIMS.md` — claims with missing evidence
- `FORENSIC_MISSING_EVIDENCE.md` — actionable gap inventory
- `FORENSIC_REQUEST_GRAPH.md/.jsonl` — 338 parent-child edges
- `FORENSIC_REGRESSION_STATUS.jsonl` — current-HEAD gate truth
- `FORENSIC_EVIDENCE_INDEX.jsonl` — 52 indexed evidence artifacts
