# LEDGER VALIDATION REPORT (machine-generated)

Validator: `scripts/validate_ledger.py` (independent strict re-parse, csv module).
Ledger: `miniandroid/evidence/audit/ACHIEVEMENT_LEDGER.csv`

| Check | Result |
|---|---|
| Total data rows | 63 |
| Unique claim IDs | 63 |
| Duplicate IDs | 0 |
| Missing IDs / orphan splits | 0 |
| Sum of verdict counts | 63 |
| Sum == rows | YES |
| Rows with non-canonical verdicts | 0 |
| Rows with multiple/compound verdicts | 0 |
| Rows flagged multiple-claims (heuristic) | 0 |
| Rows without evidence | 0 |
| Rows without integration status | 0 |
| Rows with non-canonical integration status | 0 |
| Rows with non-canonical evidence level | 0 |
| Tracker-state rows claiming runtime | 0 |
| Live-defect/feature confusion candidates | 0 |
| Structural CSV issues | 0 |

## Verdict counts (programmatic)

| Verdict | Rows |
|---|---|
| CONFIRMED | 33 |
| REJECTED | 11 |
| PARTIALLY CONFIRMED | 6 |
| BLOCKED | 8 |
| PENDING | 4 |
| SUPERSEDED | 1 |
| **TOTAL** | **63** |

## Evidence level counts

| Level | Rows |
|---|---|
| BINARY-INSPECTED | 1 |
| BUILD-GRAPH-MEASURED | 7 |
| BUILD-MEASURED | 11 |
| ENV-BLOCKED | 10 |
| INTEGRATION-TESTED | 5 |
| RUNTIME-EXECUTED | 2 |
| SOURCE-INSPECTED | 23 |
| TRACKER-STATE | 3 |
| UNIT-TESTED | 1 |

## Integration status counts

| Status | Rows |
|---|---|
| DOCUMENTED-ONLY | 8 |
| INTEGRATED | 18 |
| INTEGRATED-PER-TRACKER | 2 |
| N/A | 6 |
| NOT-INTEGRATED | 11 |
| OPEN-DEFECT | 4 |
| PARTIALLY-INTEGRATED | 5 |
| REJECTED-EXPERIMENT | 8 |
| SUPERSEDED-BY-SPLIT | 1 |

**OVERALL: PASS** — rows==verdict-sum==63, all verdicts canonical, all rows carry evidence + integration status.

Split provenance (v1 50 rows -> v2): AUD-10→10a/10b, AUD-15→15a/15b, AUD-25→25a/25b, AUD-36→36a/36b, AUD-37→37a/37b, AUD-38→38a/38b. v1 backup: /tmp/ledger_v1_backup.csv (session-local).