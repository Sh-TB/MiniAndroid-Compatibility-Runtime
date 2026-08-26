# TELEGRAM SCREEN INVENTORY — Source-Backed Element Map

Per campaign §14: for each screen reached, every important visual component maps
SOURCE → RESOURCE/ASSET → RUNTIME OBJECT → FRAMEBUFFER.

Current APK: Telegram.apk (v12.10.1, org.telegram.messenger.web, commit 62b56a07)
Source: third_party/telegram-android/TMessagesProj/src/main/java/

---

## Screen: LoginActivity — SMS Code Entry (VIEW_CODE_SMS, currentViewNum=2)

Source: `org/telegram/ui/LoginActivity.java` — `LoginActivitySmsView`
(inner class of LoginActivity, extends SlideView extends LinearLayout, VERTICAL).

### Layout structure (per source `LoginActivitySmsView.<init>` ~line 3554-3830)

| # | Element | Source | Runtime object | Geometry (px, density=1) | Visual state |
|---|---------|--------|-----------------|---------------------------|--------------|
| 1 | Root SmsView | `SlideView extends LinearLayout` (VERTICAL) | ViewNode (active instance via setParams) | (0,0) 1080×1920 | white bg (fragment default) |
| 2 | Icon area | `FrameLayout` + `RLottieImageView` (64×64, margin-top 16) | nodes 3668/3674 | (540,46) 64×64 | MISSING_ASSET — RLottie drawable not decoded (lottie JSON in assets/) |
| 3 | Title "Enter code" | `titleTextView`, `R.string.SentSmsCodeTitle`, createLinear(WRAP,WRAP,CENTER_HORIZONTAL\|TOP,0,18,0,0) | node 3667 | (506,100) 67×36 | **VISIBLE_AND_RENDERED** ✓ |
| 4 | Description | `confirmTextView`, `formatString("SentSmsCode",…,addNbsp(number))`, createLinear(WRAP,WRAP,CENTER\|TOP,side,17,side,0) | node 3666 | (311,153) 458×36 (wraps) | **VISIBLE_AND_RENDERED** ✓ — full text with phone "+1 5551234567" (NBSP) |
| 5 | Code input row | `codeFieldContainer` = `CodeFieldContainer` (LinearLayout HORIZONTAL, 5× `CodeNumberField` extends EditTextBoldCursor), createLinear(WRAP,42,CENTER_HORIZONTAL,0,32,0,0) | node 3678 + 5 children | (540→704,221) 34×42 each | **VISIBLE_AND_RENDERED** ✓ — 5 bordered boxes (CM-020); code entry text pending |
| 6 | Loading text | `LoadingTextView` (missed-call timer) | node 3682 | (540,281) | empty (correct — no missed-call state) |
| 7 | Bottom bar | `FrameLayout` + SmsView$4 (LinearLayout) + "Didn't get the code?" (`R.string.DidNotGetTheCode`) + "999+" (`LinkSpanDrawable$LinksTextView`) | nodes 3729-3727 | (540,285) | **VISIBLE_AND_RENDERED** ✓ |

### Strings (all resolve via CM-016/CM-017/CM-018 pipeline)

| String | Resource key | Resolved from | State |
|--------|-------------|---------------|-------|
| "Enter code" | SentSmsCodeTitle (0xf10ee) | ARSC string table | ✓ rendered |
| "We've sent an SMS with an activation code to your phone **%1$s**." | SentSmsCode (D8 ordinal 3) | formatString intercept by KEY + Object[] varargs (filled-new-array + aput-object) + addNbsp + replaceTags | ✓ rendered with phone |
| "Didn't get the code?" | DidNotGetTheCode (0xf0612) | ARSC | ✓ rendered |
| "999+" | — (runtime text) | setText | ✓ rendered |

### Data flow proven (CM-018)

```
PhoneView codeField="1" phoneField="5551234567"
  → onNextPressed: phoneNumber = "+" + "1" + " " + "5551234567" = "+1 5551234567"
  → Bundle.putString("phone", "+1 5551234567")
  → auth.sendCode (mocked TL_auth_sentCode type=Sms)
  → setPage(2) → currentViewNum=2 → SmsView.setParams(bundle)
  → args.getString("phone") = "+1 5551234567"
  → PhoneFormat.format (init incomplete → returns orig — see SFS notes)
  → addNbsp: replace(' ', U+00A0)
  → formatString("SentSmsCode", 3, ["+1\u00A05551234567"])
  → replaceTags: strips "**" markers
  → confirmTextView.setText → ViewNode.text → renderer word-wrap + gravity
  → framebuffer pixels
```

### Remaining gaps for this screen (per §16 classification)

| Component | Classification | Needed fix |
|-----------|---------------|------------|
| RLottie icon (blue circle animation) | MISSING_ASSET + ANIMATION_FAILURE | RLottie integration (§26) — lottie JSON in assets/ |
| Code field focus/cursor styling | VISIBLE_BUT_NOT_RENDERED | EditText focus state rendering |
| Code entry digits | MISSING_RUNTIME_NODE | CodeNumberField text input dispatch |
| SMS screen background tint (light gray #F5F6F7 in newer themes) | NOT_SET | verify from source — v12 uses white |
| Icon blue circle behind lottie | MISSING_DRAWABLE | gradient drawable pipeline |
| Keyboard | N/A | headless runtime — out of scope |

---

## Screen: LoginActivity — Phone Input (VIEW_PHONE, currentViewNum=0) — PASSED THROUGH

Proven in prior EXPs (EXP-088..092): real phone input, real Next click,
onNextPressed, auth.sendCode, confirm dialog ("Is this the correct number?"
"+1 5551234567", "Edit" — nodes 4786-4788 observed in logs).

## Screen: LaunchActivity / IntroActivity — PASSED THROUGH

Proven in prior EXPs (application lifecycle, IntroActivity fragment).

---

## Font

BitmapFont: 95 ASCII glyphs auto-generated from DejaVuSansMono
(scripts/gen_bitmap_font.py → bitmap_font_data.h). Renders all ASCII text.
NBSP (U+00A0) renders as UTF-8 multi-byte — glyph falls back to space.

## Metrics (3-run proof, EXP-095)

- 42639→43379 non-bg pixels, stable across 3 runs (SHA identical)
- 18 render nodes, 10/10 semantic checks pass
- y-range 105-352 (content top-third; density=1 keeps margins compact —
  real device density 2.75 would spread ~2.75x)
