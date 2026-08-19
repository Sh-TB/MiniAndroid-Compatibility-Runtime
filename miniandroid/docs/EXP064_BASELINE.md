# EXP-064 — Forensic Baseline (captured BEFORE any EXP-064 changes)

Captured at commit `5f2f4c29997e1fe7563c47a133ae132376101ce4` (HEAD of EXP-063).

## Baseline Metrics

| Metric | Value |
|---|---|
| Git commit | `5f2f4c2` |
| APK SHA256 | `193ad551e2cbb745387f26370369f9cd0cf0353ecbc318398ada087ac2bf945e` |
| Execution duration | 23,964.70 ms |
| Instructions executed | 2,047,392 |
| Unique methods | 1,029 |
| Unique classes | 41078 (DEX) / ~1400 (instantiated) |
| Memory RSS | not measured (under 500 MB target) |
| HALT count | 1 (`Infinite loop at PC=0x40 in AndroidUtilities.readRes`) |
| Resource strings resolved | 39 (in view_tree.json `text` field) |
| Views with text | 39 (same as above) |
| TextView setText calls | not separately instrumented |
| ViewNodes containing text | 39 |
| drawText operations | 0 (renderer embeds text via Pillow `ImageDraw.text`, no separate drawText) |
| Output PNG path | `run/exp063_final3/login_screen.png` |
| PNG dimensions | 1080 × 1920 |
| PNG SHA256 | `17944d4fcf7715775b4dfed290eab66f49ce120a3890896942745bcb505e0cdc` |
| View-node total | 1385 |
| Nodes rendered into PNG | 22 (only the chosen `LoginActivity$2` root subtree) |
| Text strings visible in PNG | **0 — the 39 text strings are present in `view_tree.json`, but the renderer does not propagate them to pixels** |

## What the baseline PNG actually contains

The PNG produced by `tools/exp061_render.py` is a **diagnostic visualization**, not a UI screenshot:

- Each rendered ViewNode is drawn as a colored rectangle whose fill color is derived from the View class name.
- A small grey label is drawn in the lower part of every rectangle showing the **short class name** (e.g. `LoginActivity$3`, `LinearLayout`, `CustomPhoneKeyboardView$NumberButtonView`).
- The `text` field of each node IS read (line 247–252 of `exp061_render.py`) but only the first 60 chars are written, and only inside a rectangle that already received a class-name label and a colored background — visually the class labels dominate.
- Only **22 of 1385** nodes are rendered, because `layout_pass()` picks ONE root (the View with the most descendants — `LoginActivity$2`, the ViewPager container) and only lays out descendants of that root. **`LoginActivity$PhoneView` (id=2728) has `parent_id=0` and is therefore not part of that subtree**, so the actual phone-entry UI is never laid out.

## Why the baseline PNG does NOT show login text

Three independent defects:

1. **Wrong root selection.** `layout_pass()` uses descendant-count as a proxy for "the real content root." For Telegram's LoginActivity this picks the ViewPager (`LoginActivity$2`) which contains ALL slides as siblings — so the visible image ends up being a stack of all 8 slide views (PhoneView, SmsView, RegisterView, PasswordView, RecoverView, ResetWaitView, NewPasswordView, …) overlaid.
2. **No visibility filtering.** Telegram pre-creates every slide View but only ONE is `currentViewNum`-selected at a time. The baseline renderer does not consult visibility / `currentViewNum` at all.
3. **Class-name-as-label.** Even when a TextView with real text is rendered, the renderer draws the class label in addition to (and visually similar to) the text, so the image reads as a debug overlay, not a UI screen.

## Baseline artifacts preserved

All artifacts copied to `run/exp064_baseline/`:

| File | Bytes | Purpose |
|---|---|---|
| `view_tree.json` | 531,758 | Full ViewNode dump (1385 nodes, 39 with text) |
| `login_screen.png` | 21,965 | Diagnostic image (the failing baseline) |
| `login_screen_debug.png` | 21,989 | Same image with red bounding boxes |
| `render_provenance.json` | 4,478 | Rendered-view list and metadata |
| `shadow_report.json` | 3,967 | Shadow system state at end of run |
| `stdout.log` | 4,730 | Runtime stdout |

## Text-pipeline spot check (Phase 1 preview)

Strong resource-derived strings that ARE present in `view_tree.json`:

| text | ViewNode id | View class |
|---|---|---|
| `"Start Messaging"` | 2460 | `IntroActivity$4` |
| `"Please confirm your country code and enter your phone number."` | 2734 | `LinkSpanDrawable$LinksTextView` (under `LoginActivity$PhoneView`) |
| `"Check your Telegram messages"` | 2877 | `TextView` (under `LoginActivity$LoginActivitySmsView`) |
| `"Enter code"` | 2941 / 3057 | `TextView` (under SmsView) |
| `"Phone verification"` | 3004 | `TextView` (under SmsView) |
| `"Profile info"` | 3139 | `TextView` (under LoginActivityRegisterView) |
| `"Your password"` | 3216 | `TextView` (under PasswordView) |
| `"Forgot password?"` | 3247 | `TextView` (under PasswordView) |
| `"Reset account"` | 3426 / 3430 | `TextView` (under ResetWaitView) |
| `"Set a new password"` | 3435 | `TextView` (under NewPasswordView) |

The **PhoneView** subtree is the right visible root for a fresh-install login screen (it is the slide that holds the "Please confirm your country code and enter your phone number." text plus the phone number entry field). That is the slide we will render in EXP-064.

## Status

`CHECKPOINT_L_LOGIN_UI` — **NOT PROVEN.** Image does not contain any readable Login text.

EXP-064 begins from this baseline.
