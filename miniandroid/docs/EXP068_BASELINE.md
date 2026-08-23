# EXP-068 — Forensic Baseline

Captured at commit `be4dfbd` (HEAD of EXP-067).

## Baseline metrics

| Metric | Value |
|---|---|
| Git commit | `be4dfbd` |
| APK SHA256 | `193ad551e2cbb745387f26370369f9cd0cf0353ecbc318398ada087ac2bf945e` |
| ViewNode count | 1385 |
| Text-bearing ViewNodes | 49 |
| Image-bearing ViewNodes | 9 |
| Drawable-backed ImageViews | 5 |
| PhoneView child count | 4 |
| `login_ui.png` SHA256 | `17d1d4068cdb788fcb65831ad4e26a00d850090c86c6e350bc6bc72bbc8b6278` |

## Known gaps (from EXP-067 backlog)

1. Layout is heuristic, not Android-correct (no MATCH_PARENT/WRAP_CONTENT/weight/margins)
2. View inheritance is pattern-based, not semantic superclass resolution
3. Generic LayoutInflater not wired to setContentView
4. AnimatedPhoneNumberEditText treated by name pattern, not superclass
5. Floating Next button missing
6. Hint propagation incomplete (OBJECT_REF String not resolved)
7. No input dispatch system
8. No click dispatch system
9. PhoneView → Next → onNextPressed not proven
10. No controlled mock network backend
11. SMS View not reached
12. Exception engine incomplete

## Status

`CHECKPOINT_L_LOGIN_UI = PROVEN` (maintained from EXP-067). EXP-068 aims to reach `CHECKPOINT_M` (interactive Login → SMS transition).
