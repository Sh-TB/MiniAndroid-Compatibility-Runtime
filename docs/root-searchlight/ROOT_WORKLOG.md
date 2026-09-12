# ROOT WORKLOG — LIVE

Rule: this file indexes waves; the full evidence-grade session log lives in
`docs/maintenance/worklog.md` (repo root). No failure or false lead is ever deleted (§14).

## WAVE 0 — Searchlight establishment (this baseline)

- HEAD: `0383f19f` — the M9 line (F-053..F-057) reconciled with the M6/M7/M8
  line (F-040..F-050) at merge commit 0383f19f; battery 91/91 ALL PASS;
  hello_color golden byte-identical (11e0056320d8546d).
- 278-root radar mapped: see ROOT_WORKLIST.md. 8 new roots registered
  (R-NEW-279..286) from M9 causal analysis + live merged-tree runs.
- Evidence index: see ROOT_EVIDENCE_INDEX.md.
- Failure ledger + decision ledger established (no history rewritten).

## Session-end accounting template (brief §30)

Every wave must close with:
inspected / verified / fixed / partial / failed / false-leads / new-roots /
high-impact-unresolved / current frontier / next highest-value root.

## CURRENT ACCOUNTING

- Roots inspected & classified: 286 (278 radar + 8 new)
- VERIFIED-FIXED: 5 (F-041, F-044→R-NEW-257, F-050-family→R-NEW-242, F-053→R-NEW-220/218, F-029→R-NEW-016)
- VERIFIED-CORRECT: 45 | PARTIAL: 100 | OBSERVED-FAIL: 6 | UNPROVEN: 73
- RESEARCHED-NOT-IMPLEMENTED: 16 | NOT-APPLICABLE: 41
- False leads recorded: 2 (see FAILURE_LEDGER) | New roots: 8
- Current frontier: R-NEW-246 first-frame completeness (P0)
- Next highest-value root: R-NEW-279 lifecycle callback registry (suspected
  dooz composition blocker) → then R-NEW-285 Job-active cancellation.

## Waves (index)
- S17..S18: see repo docs/maintenance/worklog.md entries S17-AUDIT-1 .. S18 (F-058..F-069, registry 295).
- S19: F-070 closed (R-NEW-294); tooling debt fixed (304321ed).
- S20: F-071/F-072/F-073 closed (R-NEW-295..297); dooz onCreate exception-free.
- S21: F-074 (engine-level superclass walk) + F-075 (polymorphic zero) closed
  (R-NEW-298/299); the "callback removed-not-run" gate retired as upstream-legal;
  full evidence in docs/evidence/s21_f074_f075/ + docs/evidence/S21_F074_F075_REPORT.md.
