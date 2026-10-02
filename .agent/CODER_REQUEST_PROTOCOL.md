# Permanent Coder Request Protocol

This document defines the mandatory process for every major Coder request.

## 1. One request = one GitHub Issue
Before giving a major task to a Coder, create a dedicated GitHub Issue. Give the user:
- the Issue link;
- the exact copy/paste-ready Coder prompt;
- the instruction that the same Issue is the authoritative execution record.

## 2. Coder must return to the same Issue
After implementation/testing, the Coder MUST return to the original Issue and fill a completion ledger in a new/update comment.

The ledger must cover every numbered requirement and contain:
- STATUS: IMPLEMENTED / TESTED / OBSERVED / PARTIAL / BLOCKED / PENDING / SUPERSEDED
- one-line result;
- evidence location (commit, test, trace, screenshot SHA, file, log, etc.);
- blocker/unresolved item when applicable.

"Done", "fixed", "tests passed", or "complete" alone is never a valid completion report.

## 3. Multiple Coders share one Issue
Any later Coder/agent must first read the Issue and previous completion comments, continue unfinished rows, and update the same evidence chain. Work must not disappear into disconnected requests.

## 4. Independent reviewer verification is mandatory
When the Coder reports completion, the reviewer MUST independently read:
1. original Issue;
2. all relevant comments;
3. completion ledger;
4. referenced commits/files/evidence;
5. repository HEAD/state;
6. runtime evidence where required.

The reviewer must distinguish:
- Coder claim;
- evidence actually present;
- reviewer-verified result.

Only the third is accepted as completion.

## 5. No premature completion
An Issue remains open while any applicable requirement is missing, unverified, PARTIAL, BLOCKED, PENDING, or contradicted by runtime evidence.

## 6. Evidence standard
Prefer:
SOURCE → SEMANTIC LAW → TEST → RUNTIME TRACE → STATE CHANGE → ACTUAL CONSUMER → SCREENSHOT/OUTPUT → 3-RUN REPRODUCIBILITY → CORPUS REGRESSION

Do not accept exit code 0, APK loaded, DEX parsed, file/PNG existence, or an agent report as sufficient runtime proof.

## 7. Carry-forward
Every new major request must inspect previous request ledgers and carry relevant unfinished work forward.

## 8. User-facing delivery
For every major request, the reviewer should provide the user:
- GitHub Issue link;
- copy/paste-ready Coder prompt;
- explicit completion-ledger instruction;
- after the Coder finishes, an independent review result.

This protocol is permanent unless a newer repository-wide law explicitly replaces it.
