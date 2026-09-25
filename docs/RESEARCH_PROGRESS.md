# RESEARCH 500 — LIVING PROGRESS

Updated: S104 wave (post commit 4feaaeda). Mechanical numbers only.

```text
INPUT
------
claimed: 500    present: 136    duplicates linked: 7    truncated: 364    registered: 500

AUDIT
-----
researched: 21
reproduced: 28
confirmed: 12
observed: 19
solved: 31
partial: 1
out_of_scope: 20
false_lead: 4
truncated_input: 364

ROOT CAUSES
-----------
named roots: 11 (R-001..R-009 + R-NP umbrella + R-OUT host-only family)
largest shared root: R-001 REFLECTION-FIELD-IDENTITY — 18 tickets L5 (FIX-001/004)
newest shared root: R-009 SWITCH-KEY-WIDENING — 2 tickets (FIX-005, S104)

FIX IMPACT
----------
fixes implemented: 5 (FIX-001..004 S103, FIX-005 S104)
tickets SOLVED by shared fixes: 30 (REGRESSION_TESTED L5) + 1 PARTIAL

CORPUS IMPACT (measured)
------------------------
solitaire com.vayunmathur.games.solitaire: errors 12 -> 0 (FIX-005), 3/3 SHA-identical
61-title census distribution: unchanged (14 INTERACTIVE / 2 RENDERED-L2+ / 38 PARTIAL / 7 FAIL) — zero regressions
battery: 105/105 ALL PASS (re-verified after FIX-005)
```

## NEXT ACTION

1. Re-run dooz family on FIX-005 to close P084's lambda-specific slice (PARTIAL -> SOLVED).
2. R-004 CLASS-IDENTITY dual-identity instanceof (22/59 fan-out, S103-queued).
3. R-005 DECOR-LINKAGE sub-decor attach (6-title family).

