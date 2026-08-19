# MiniAndroid Runtime — Agent State

**Current checkpoint:** `CHECKPOINT_L_LOGIN_UI = PROVEN`
**Latest commit:** `7f5448a` — EXP-064: REAL LOGIN IMAGE PROVEN BY PIXELS
**GitHub issue:** https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/1

## Active experiment log

| EXP | Title | Status | Commit |
|---|---|---|---|
| EXP-061 | Headless GPU-Free Login Screen Rendering | ✅ DONE | (in 5f2f4c2) |
| EXP-062 | Wide opcode + array model + R class static values | ✅ DONE | (in 5f2f4c2) |
| EXP-063 | ARSC parser + resource resolver + R class values | ✅ DONE | 5f2f4c2 |
| EXP-064 | Real login image proven by pixels | ✅ DONE | 7f5448a |

## Next high-value targets

- Run-time fix for `dump_view_tree()` to record `children` for ALL parents (currently IntroActivity id=2387 has no `children` field, breaking renderer regression on IntroActivity).
- ARSC parser entry-index lookup bug in `tools/exp063_arsc_parser.py` (CLI tool returns wrong values; runtime uses `resource_values.json` instead, so not blocking).
- Layout: implement real `android:orientation` parsing from XML layout attributes for LinearLayout (currently inferred from class name).
- Real drawable rendering (currently ImageView placeholders are gray rectangles).
- Color resource resolution (currently `Resources.getColor(int)` returns default black).

## Known issues (non-blocking)

- v3 register "issue" from EXP-063 worklog was a red herring — the trace was inspecting a non-resource-ID local register. No actual bug; resource pipeline works correctly.
- Androguard's `get_string_resources()` returns empty XML wrapper for Telegram's default-locale strings (locale-overlay system). MiniAndroid's own `tools/exp063_arsc_parser.py` resolves them correctly.
- `dump_view_tree()` skips `children` array for some top-level root nodes (IntroActivity id=2387). To render IntroActivity, use `--slide-root 2460` (the IntroActivity$4 TextView with "Start Messaging").
