# EXP-065 — Forensic Baseline

Captured at commit `7b4d23d` (HEAD of EXP-064).

## Baseline metrics (EXP-064 state, BEFORE EXP-065 fixes)

| Metric | Value |
|---|---|
| Git commit | `7b4d23d` |
| APK SHA256 | `193ad551e2cbb745387f26370369f9cd0cf0353ecbc318398ada087ac2bf945e` |
| Execution duration | ~24 s |
| Instructions executed | 2,047,392 |
| Text-bearing ViewNodes | 39 |
| **`FIELD_PREFERRED_AUDIO_LANGUAGES` visible in PNG?** | **YES (BUG)** |
| Plus text on view 2791 | `"FIELD_PREFERRED_AUDIO_LANGUAGES"` (wrong; should be `"+"`) |
| Hint field on ViewNode | NOT CAPTURED (no `hint` field in JSON) |
| `setHintText` stubbed? | YES (entire method stubbed, no hint captured) |
| `login_ui.png` SHA256 | `54c12b710249dbdbe8be955a97fb2cb0c612393ea38b65d855a3e99c7958f8e4` |
| OCR match rate | 0.5 (1 of 2 strings — `FIELD_PREFERRED_...` was leaking) |

## Diagnosis

The EXP-064 image OCR-validated the main header text, but ALSO showed `FIELD_PREFERRED_AUDIO_LANGUAGES` as visible UI content. Forensic investigation revealed:

1. **Source**: `FIELD_PREFERRED_AUDIO_LANGUAGES` is an Android `MediaMetadata` constant. It lives in `classes.dex`'s DEX string table at `string_idx=5975`.

2. **Trigger**: `LoginActivity$PhoneView.<init>` in `classes4.dex` executes `const-string v11, "+"` at PC=475. The string_idx for `"+"` in classes4.dex is **5975** (verified by direct DEX parsing).

3. **Bug**: `execute_const_string` looked up `dex_report_->strings[5975]` — but `dex_report_->strings` is the MERGED concatenation of all 5 DEX files' string tables. classes.dex (the first DEX) has 56,182 strings, so its string at index 5975 (`FIELD_PREFERRED_AUDIO_LANGUAGES`) is what the merged table reports — NOT classes4.dex's string at index 5975 (`"+"`).

4. **Result**: The const-string opcode stored `"FIELD_PREFERRED_AUDIO_LANGUAGES"` into register v11. Then `invoke-virtual TextView.setText(v11)` set view 2791's text to that wrong string.

5. **PNG impact**: The renderer drew `"FIELD_PREFERRED_AUDIO_LANGUAGES"` as visible UI content in `login_ui.png`.

## Fix plan (EXP-065)

- Add `resolve_string_for_dex(string_idx, dex_index)` that reads the string directly from `per_dex_raw_data_[dex_index]` (the per-DEX raw bytes), bypassing the merged strings table.
- Update `execute_const_string` and the `const-string/jumbo` opcode handler to use this function.
- This is the same pattern already used for `resolve_method_name_for_dex` and `resolve_type_for_dex`.

## Status

`CHECKPOINT_L_LOGIN_UI_COMPLETE` — **NOT PROVEN at baseline.** Image contains a leaked debug constant.
