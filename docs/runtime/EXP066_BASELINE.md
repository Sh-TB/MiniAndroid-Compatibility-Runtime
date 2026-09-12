# EXP-066 — Forensic Baseline

Captured at commit `2c33dc4` (HEAD of EXP-065).

## Baseline metrics (EXP-065 state, BEFORE EXP-066 fixes)

| Metric | Value |
|---|---|
| Git commit | `2c33dc4` |
| APK SHA256 | `193ad551e2cbb745387f26370369f9cd0cf0353ecbc318398ada087ac2bf945e` |
| APK size | 82,680,854 bytes |
| DEX files | 5 (classes.dex, classes2.dex, classes3.dex, classes4.dex, classes5.dex) |
| Execution duration | ~24 s |
| Instructions executed | 2,047,392 |
| Text-bearing ViewNodes | 46 |
| Hint-bearing ViewNodes | 0 |
| PhoneView nodes (main) | 1 (id=2728) |
| LoginActivity nodes (non-lambda) | 84 |
| `login_ui.png` SHA256 | `9be984fd4559643e9150f231267b2b8b36eb943e81f6d98380dd29d53904fb6b` |
| PNG dimensions | 1080 × 1920 |
| OCR match rate | 1.0 (1 of 1 expected string) |
| Multi-DEX bugs fixed | 1 (const-string, EXP-065) |
| Multi-DEX regression corpus | none |

## Known gaps at baseline

- `OutlineTextContainerView.setText()` text was lost — the DEX bytecode stores the text in a heap field (`mText`), but the ViewShadow never sees it. This means the phone field label "Phone number" and country field label "Country" were NOT captured on the ViewNode.
- `const-class`, `check-cast`, `instance-of` opcodes still used the merged `dex_report_->types[]` table — multi-DEX bugs that hadn't manifested yet but were latent.
- No multi-DEX regression corpus existed to prove the per-DEX resolution is essential.

## Status

`CHECKPOINT_L_LOGIN_UI` — **PROVEN at baseline** (from EXP-065), but with known gaps in label text capture and multi-DEX opcode coverage.
