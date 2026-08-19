# MiniAndroid Runtime — Agent State

**Current checkpoint:** `CHECKPOINT_L_LOGIN_UI_COMPLETE = PROVEN`
**Latest commit:** `4bc37dd` — EXP-065: Fix multi-DEX const-string bug
**GitHub issues:**
- https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/1 (EXP-064)
- https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/2 (EXP-065)

## Active experiment log

| EXP | Title | Status | Commit |
|---|---|---|---|
| EXP-061 | Headless GPU-Free Login Screen Rendering | ✅ DONE | (in 5f2f4c2) |
| EXP-062 | Wide opcode + array model + R class static values | ✅ DONE | (in 5f2f4c2) |
| EXP-063 | ARSC parser + resource resolver + R class values | ✅ DONE | 5f2f4c2 |
| EXP-064 | Real login image proven by pixels | ✅ DONE | 7f5448a |
| EXP-065 | Complete Login screen reconstruction (multi-DEX bug fix) | ✅ DONE | b83e8bc |

## Next high-value targets

- **Real XML layout attribute parsing** — currently the runtime doesn't parse `android:hint`, `android:text`, `android:src` from XML layout files. This means EditText hints like "Phone number" are never set. Fix: parse `res/layout/*.xml` files and apply attributes during View inflation.
- **Real drawable decoding** — implement BitmapDrawable (PNG/JPEG/WebP), VectorDrawable (XML), ColorDrawable. Currently ImageView placeholders are gray rectangles.
- **Real color resolution** — `Resources.getColor(int)` returns default black; should resolve from `<color>` resources.
- **Country code/country name lookup** — `setCountryButtonText()` is called but the country name requires locale-specific resolution.
- **Multi-DEX bug sweep** — the const-string bug likely also affects other opcodes that use merged `dex_report_->types[]` / `dex_report_->method_ids[]` instead of per-DEX resolution. Audit: `execute_const_class`, `execute_check_cast`, `execute_instance_of`, and any other 21c/22c-format opcodes.

## Known issues (non-blocking)

- `AnimatedPhoneNumberEditText.setHintText` still loops infinitely via `DynamicAnimation.cancel()` — but EXP-065 now stubs-and-captures the hint BEFORE bypassing the bytecode. The hint field on ViewNode is now populated.
- `AndroidUtilities.replaceTags` is still stubbed (string processing loop).
- Several `EmojiInputFilter` / `HelperInternal19` / `SkippingHelper19` / `AppCompatTextViewAutoSizeHelper` constructors are still stubbed (constructor loops).

