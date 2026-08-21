# MiniAndroid Runtime — Agent State

**Current checkpoint:** `CHECKPOINT_L_LOGIN_UI = PROVEN` (improved in EXP-066)
**Latest commit:** `7180c2f` — EXP-066: Multi-DEX semantic audit + OutlineTextContainerView text capture
**GitHub issues:**
- https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/1 (EXP-064)
- https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/2 (EXP-065)
- https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/3 (EXP-066)

## Active experiment log

| EXP | Title | Status | Commit |
|---|---|---|---|
| EXP-061 | Headless GPU-Free Login Screen Rendering | ✅ DONE | (in 5f2f4c2) |
| EXP-062 | Wide opcode + array model + R class static values | ✅ DONE | (in 5f2f4c2) |
| EXP-063 | ARSC parser + resource resolver + R class values | ✅ DONE | 5f2f4c2 |
| EXP-064 | Real login image proven by pixels | ✅ DONE | 7f5448a |
| EXP-065 | Complete Login screen reconstruction (multi-DEX const-string bug fix) | ✅ DONE | b83e8bc |
| EXP-066 | Multi-DEX semantic audit + OutlineTextContainerView text capture | ✅ DONE | 7180c2f |

## Multi-DEX audit status (EXP-066)

| Opcode | Index type | Status |
|---|---|---|
| const-string (0x1a) | string_idx | ✅ FIXED (EXP-065) |
| const-string/jumbo (0x1b) | string_idx | ✅ FIXED (EXP-065) |
| const-class (0x1c) | type_idx | ✅ FIXED (EXP-066) |
| new-instance (0x22) | type_idx | ✅ FIXED (EXP-058) |
| new-array (0x23) | type_idx | ✅ FIXED (EXP-066, trace evidence) |
| check-cast (0x1f) | type_idx | ✅ FIXED (EXP-066) |
| instance-of (0x20) | type_idx | ✅ FIXED (EXP-066) |
| invoke-virtual/super/direct/static/interface (0x6e-0x78) | method_idx | ✅ ALREADY CORRECT (EXP-037) |
| iget/iput/sget/sput (0x52-0x6d) | field_idx | ✅ ALREADY CORRECT (EXP-046) |
| **Total remaining UNSAFE** | | **0** |

## Next high-value targets

- **Real drawable decoding** — implement BitmapDrawable (PNG/JPEG/WebP), VectorDrawable (XML), ColorDrawable. Currently ImageView placeholders are gray rectangles. Login-related drawables available: `login_phone1`, `login_arrow1`, `intro_*` series.
- **Real color resolution** — `Resources.getColor(int)` returns default black; should resolve from `<color>` resources. 165 color resources available in `resource_values.json`.
- **Country code/country name lookup** — `setCountryButtonText()` is called but the country name requires locale-specific resolution.
- **Real XML layout attribute parsing** — for EditTexts that load hints via `android:hint="@string/..."` (Telegram uses programmatic `OutlineTextContainerView.setText` instead, which is now captured).

## Known issues (non-blocking)

- `AnimatedPhoneNumberEditText.setHintText` still loops infinitely via `DynamicAnimation.cancel()` — stubbed-and-captured in EXP-065.
- `AndroidUtilities.replaceTags` is still stubbed (string processing loop).
- Several `EmojiInputFilter` / `HelperInternal19` / `SkippingHelper19` / `AppCompatTextViewAutoSizeHelper` constructors are still stubbed (constructor loops).
- ImageView drawables are gray placeholders (no bitmap decoding yet).
- `Resources.getColor` returns default black (no color resource resolution yet).

