# EXP-069 — Forensic Baseline

Captured at commit `a148730` (HEAD of EXP-068).

## Baseline metrics

| Metric | Value |
|---|---|
| Git commit | `a148730` |
| APK SHA256 | `193ad551e2cbb745387f26370369f9cd0cf0353ecbc318398ada087ac2bf945e` |
| ViewNode count | 1385 |
| Text-bearing ViewNodes | 49 |
| Image-bearing ViewNodes | 9 |
| EditText count (semantic) | 14 |
| TextView count (semantic) | 103 |
| Button count (semantic) | 0 |
| ViewGroup count (semantic) | 112 |
| Floating Next button ID | 3869 |
| `login_ui.png` SHA256 | `39ca3cd7c2d03582384202feb87d8f091a6e2c7d6958d1b0cfb11ce3d44c0169` |

## Known gaps

- No input dispatch system (can't inject text into EditText)
- No click dispatch system (can't trigger OnClickListener callback)
- No TextWatcher callback execution
- No controlled network boundary (ConnectionsManager.sendRequest is stubbed)
- No page state transition model
- SMS View not reached
- Button count = 0 (Telegram uses custom Views, not android.widget.Button)

## Status

`CHECKPOINT_L_LOGIN_UI = PROVEN` (maintained). EXP-069 aims to reach `CHECKPOINT_M` (interactive Login → SMS transition).
