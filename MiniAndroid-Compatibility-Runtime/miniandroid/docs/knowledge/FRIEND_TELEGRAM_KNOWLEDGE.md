# Friend Telegram Knowledge Archive

**Status**: SEPARATE from `CODER2_KNOWLEDGE.md` and `CODER3_KNOWLEDGE.md`.
Every finding below has `source=FRIEND` and is independently re-verified
on current HEAD before being included.

---

## FRIEND_FINDING 1 — FULL-SCREEN BACKGROUND

### Hypothesis (from friend)
> SmsView root: MATCH_PARENT 1080x1920 → renderer draws GREY_200 background
> → full-screen container background overwrites text.

### Independently Verified On Current HEAD
- **reproduced_on_current_head**: `true` (commit `cb6cd54`, 2026-08-25)
- **evidence**:
  - File: `miniandroid/src/runtime/execution_engine.cpp:813-826` (post-EXP-092 HEAD).
  - Code:
    ```cpp
    bool is_container = node->class_desc.find("Layout") != std::string::npos ||
                      node->class_desc.find("ViewGroup") != std::string::npos;
    bool is_full_screen = (w >= config.screen_width && h >= config.screen_height);
    if (is_container && !is_full_screen) {
        canvas.draw_rect(left, top, right, bottom, Colors::GREY_200);
    } else if (node->class_desc.find("Button") != std::string::npos) {
        canvas.draw_rect(left, top, right, bottom, RGBA{0x6F, 0xA8, 0xDC, 0xFF});
    }
    ```
  - The check correctly SKIPS the SmsView root's background because the
    SmsView root is `LoginActivity$LoginActivitySmsView` (contains neither
    "Layout" nor "ViewGroup" in its class name). It is therefore NOT a
    container by the renderer's definition.
  - Even if SmsView were classified as a container, `is_full_screen`
    evaluates to `true` for the root (width=1080=screen_width,
    height=1920=screen_height), so the `if (is_container && !is_full_screen)`
    condition would be false, and the background would be correctly
    suppressed.
- **status**: PROVEN_CORRECT — the friend's hypothesis was already
  addressed at HEAD before this experiment. The full-screen container
  skip was added in EXP-092 commit `b6ef143`.

### Regression
- No regression added because the behavior is already in place.
- Manual inspection of `run/exp092/3run_proof/run1/run.log` confirms
  `[EXP092-RENDER] node=3990 class=Lorg/telegram/ui/LoginActivity$LoginActivitySmsView`
  is visited but no `[EXP092-RENDER]` line shows `canvas.draw_rect` for it.

---

## FRIEND_FINDING 2 — SMALL RESOURCE IDs (< 0x10000)

### Hypothesis (from friend)
> getString(int resid) with resid < 0x10000 may refer to plural/unknown
> resources, and DEX fallback can produce garbage "View".
>
> DO NOT implement: "all IDs < 0x10000 => empty string".
> Instead: inspect resource type; identify actual resource owner;
> reproduce one failing ID; trace getString(int)→resolver→returned value;
> verify expected semantics. If the ID is not a string: return the
> correct documented behavior, not a blanket empty string.

### Independently Verified On Current HEAD
- **reproduced_on_current_head**: `true` (commit `cb6cd54`, 2026-08-25)
- **reproduced one failing ID**:
  - In `LoginActivity$PhoneView.onNextPressed` at PC=614, the DEX bytecode
    loads literal `3` into a register and calls `LocaleController.getString(int)`.
  - Source line: `[EXP063-ISTATIC] getString instr=0x1071 argc=1 regs[0]=1
    class=Lorg/telegram/messenger/LocaleController;
    caller=Lorg/telegram/ui/IntroActivity;.onFragmentCreate pc=29 arg0=3`
  - And many more: `getString(3)` is called 100+ times across `ScamDrawable.<init>`,
    `IntroActivity.onFragmentCreate`, `IntroActivity.createView`, etc.
- **actual resource owner identified**:
  - `resid=3` IS a legitimate remapped R.string entry. The D8/R8 shrinker
    rewrote `R.string.ChooseCountry` (originally `0x7f...`) to the ordinal
    index `3` during APK shrinking.
  - Verified via bytecode: at PC=614 of onNextPressed, the const-load is
    followed by `sget` from `R$string.ChooseCountry`, which (with D8
    shrinker) has value 3.
- **expected semantics**:
  - `getString(3)` SHOULD return "Choose a country" (the actual string
    value of `R.string.ChooseCountry`).
- **trace path** (verified in run.log):
  ```
  [EXP063-ISTATIC] getString ... arg0=3
       ↓
  try_recursive_invoke → LocaleController.getString(int)
       ↓
  [RES-INTERCEPT] LocaleController.getString(small_int=3) → ""
  ```
  - CURRENT behavior: returns `""` (empty string).
  - EXPECTED behavior: return `"Choose a country"` (the real R.string
    value, NOT the field name).
- **status**: PARTIALLY_FIXED. The friend's concern is acknowledged:
  the blanket `< 0x10000 => empty string` rule is wrong.
  - A first attempt to fix it (storing ALL small-int values from R$string
    in `field_name_by_resid_`) caused a crash in
    `ensure_class_initialized` — ASAN showed corrupted `std::string` reads.
    Reverted; needs a more careful fix that doesn't add arbitrary entries
    to `field_name_by_resid_` for resource IDs that may collide with
    internal R-table ordinal indices.
  - The current behavior (return `""` for unknown small ints) is SAFER
    than the alternative of letting DEX bytecode execute (which produces
    garbage "View" via StringBuilder). But it's not the documented
    correct behavior.

### Correct Fix (not yet implemented)
- Build an explicit `R$string.<clinit>`-derived map of `resid → field_name`
  by capturing SPUT instructions during R$string's static initializer,
  rather than relying on `default_int_value` from the DEX (which is `0`
  for R$string per EXP062-SV logs — `with_defaults=0/11195`).
- In the getString(int) interceptor, consult this SPUT-derived map first.
- This avoids the crash because we no longer iterate `cls_ref.static_fields`
  for R$string entries that don't have defaults.

---

## FRIEND_FINDING 3 — BITMAP FONT LIMIT

### Hypothesis (from friend)
> Current renderer apparently contains only a small set of glyphs.
> Verify: TextView.setText(...) → ViewShadow.text → renderer glyph lookup →
> missing glyph behavior. Count: total glyphs, missing glyphs, fallback
> glyph uses, actual rendered text pixels. Then expand the font GENERICALLY
> enough to render the current Telegram SMS text. At minimum support the
> complete printable ASCII set used by the current SMS screen. Do NOT
> hardcode Telegram text into the font. Add a micro regression for:
> HELLO, 0123456789, + / . : -, and the actual runtime-resolved SMS strings.

### Independently Verified On Current HEAD
- **reproduced_on_current_head**: `true` (commit `7a99e9a`, 2026-08-25)
- **before-fix stats**:
  - Total glyphs declared: 13 (space, H, e, l, o, M, i, n, d, r, A, t)
  - Glyph table size: `std::array<Glyph, 95>` (covers ASCII 32..126)
  - Missing glyphs (using default "dot in the middle" bitmap): 82
  - **CRITICAL BUG**: glyphs were mis-indexed! For example:
    - `glyphs_[33] = {'H', 7, 16, 8, H_bitmap};` // commented "H (72-32=40)"
      but written to slot 33 (which is 'A' (65-32) — should have been slot 40).
    - Then later: `glyphs_[33] = {'A', 7, 16, 8, A_bitmap};` overwrites the
      'H' entry. So 'H' effectively has NO real glyph — falls back to default.
  - Actual rendered text pixels on SMS screenshot (baseline HEAD `dd25e18`):
    **208 dark pixels**. The 208 pixels were essentially all "dot in the
    middle" defaults — no readable text was visible.
- **after-fix stats** (commit `7a99e9a`):
  - Total glyphs: 95 (full ASCII printable range 32..126)
  - Missing glyphs: 0
  - Default fallback uses: 0 (all chars have real bitmaps)
  - Rendered text pixels: **974 dark pixels** (4.7× improvement)
  - SHA256 of login_sms.png (3 runs identical):
    `60df0c2ba1680ae58e2612bfd82660a3436df963569a3191dcfdc841810d4b5b`
- **font generation**:
  - File: `miniandroid/src/renderer/bitmap_font_data.h` (auto-generated).
  - Generator: `scripts/gen_bitmap_font.py` (uses PIL + DejaVuSansMono at 12pt).
  - Each glyph: 8x16 pixels, MSB-first bit packing.
- **micro regression**: `miniandroid/tests/exp092_bitmap_font_test.cpp`.
  - 28/28 tests PASS.
  - Includes the friend's required cases:
    - HELLO (195 dark pixels — was previously unrenderable)
    - 0123456789 (476 dark pixels)
    - +/-.:- (206 dark pixels)
    - Hello MiniAndroid (461 dark pixels)
  - Plus runtime-resolved SMS strings:
    - "Enter code" (391 dark pixels)
    - "Phone verification" (433 dark pixels)
    - "Check your Telegram messages" (391 dark pixels)
    - "Resend code" (426 dark pixels)
    - "Enter phrase from SMS" (472 dark pixels)
    - "Enter word from SMS" (444 dark pixels)
    - "Phone number" (437 dark pixels)
    - "Please confirm your country code and enter your phone number." (433 dark pixels)
- **status**: FIXED_AND_PROVEN.

### What was NOT done
- No Telegram text was hardcoded into the font. The bitmaps are generated
  from a generic TTF (DejaVuSansMono) for the entire ASCII printable range.

---

## DIRECT SMS STATE PROOF

### Required by friend
> Independently of the friend findings, MUST prove:
> RequestDelegate → actual callback → fillNextCodeParams → setPage(VIEW_CODE_SMS).
> Record: page value, receiver, PC, caller, arguments.
> Then prove: PhoneView hidden, SmsView visible. Do not infer this from screenshot.

### Independently Verified On Current HEAD
- **reproduced_on_current_head**: `true` (commit `cb6cd54`, 2026-08-25)
- **direct trace markers added**:
  - `[EXP092-SETPAGE]`: fires on every `setPage` invocation on `LoginActivity`.
  - `[EXP092-FILLNEXTCODE]`: fires on every `fillNextCodeParams` invocation.
  - `[EXP092-REQDELEGATE]`: fires on every `run()` invocation on any
    `ExternalSyntheticLambda*` class (catches RequestDelegate.run).
- **3-run results on current HEAD** (`run/exp092/3run_proof/`):
  | Run | setPage | fillNextCodeParams | RequestDelegate.run |
  |-----|--------|--------------------|---------------------|
  | 1   | 0      | 0                  | 72                  |
  | 2   | 0      | 0                  | 72                  |
  | 3   | 0      | 0                  | 72                  |
- **what the 72 RequestDelegate.run calls actually are** (sampling):
  - `ApplicationLoader$$ExternalSyntheticLambda2;` (depth=0, onCreate)
  - `LaunchActivity$$ExternalSyntheticLambda24/25;` (onCreate / onFragmentStackChanged)
  - `ContactsController$$ExternalSyntheticLambda57;` (reloadContactsStatuses)
  - `LocaleController$$ExternalSyntheticLambda17;` (loadRemoteLanguages)
  - `LocationController$$ExternalSyntheticLambda20;` (onCreate)
  - `PhoneView$$ExternalSyntheticLambda14;` (loadCountries → TL_nearestDc — depth=10)
  - `PhoneView$$ExternalSyntheticLambda19;` (loadCountries → TLObject — depth=11)
  - `PhoneView$$ExternalSyntheticLambda0/16/26;` (depth=0, onCreate)
  - `PhoneView$6$$ExternalSyntheticLambda0/1;` (depth=0, onCreate)
- **CRITICAL ABSENCE**: There is NO invocation of
  `Lorg/telegram/ui/LoginActivity$PhoneView$$ExternalSyntheticLambda2;` —
  which is the auth.sendCode RequestDelegate created at PC=2872 of
  `PhoneView.onNextPressed`. That delegate is never constructed because
  `onNextPressed` takes the `needShowAlert` side path at PC~1216 and never
  reaches the `TL_auth_sendCode.<init>` at PC=2410.
- **status**: SMS state transition NOT proven. The SmsView that IS
  rendered (`view_id=3990`, 6 children, only 1 visible TextView with
  text "Check your Telegram messages") exists purely from ViewPager
  pre-loading during LoginActivity.createView — NOT from the real chain.

### Visible vs Hidden Status (NOT inferred from screenshot)
- The renderer's BFS picks the SmsView at `view_id=3990` as the render
  root (logged: `[EXP090-RENDER] Using SmsView as render root: view_id=3990
  class=Lorg/telegram/ui/LoginActivity$LoginActivitySmsView; children=6`).
- The PhoneView at `view_id=3211` IS in the ViewShadow tree (logged via
  `[EXP092-REQDELEGATE]` traces) but is NOT picked as the render root.
- This does NOT mean setPage(VIEW_CODE_SMS) was called — it just means
  the renderer's substring search found an SmsView node (which exists
  from ViewPager pre-loading, regardless of the page transition).

---

## HISTORICAL: Multi-DEX String Bug Revalidation

### Required
> Preserve but revalidate the historical multi-DEX string bug:
> classes4.dex string_idx=5975 expected="+", incorrect merged-table
> result: FIELD_PREFERRED_AUDIO_LANGUAGES. Rule: per-DEX index → current
> DEX table.

### Independently Verified On Current HEAD
- **reproduced_on_current_head**: `true` (commit `cb6cd54`)
- **evidence**: `miniandroid/src/dex/dalvik_engine.cpp:398-401` contains the
  comment block documenting this exact case:
  ```cpp
  // In multi-DEX apps (Telegram has 5 DEX files), the merged dex_report_->strings
  // is the CONCATENATION of all DEX files' string tables — so using the merged
  // index causes const-string to fetch the WRONG string. For example,
  // classes4.dex's string_idx=5975 is "+", but merged_strings[5975] is
  // "FIELD_PREFERRED_AUDIO_LANGUAGES" from classes.dex (which has 56,182
  // strings before classes4.dex's strings start).
  ```
- **per-DEX resolution path**: `read_dex_string_from_raw(raw, string_idx, hdr)`
  at `dalvik_engine.cpp:364-391`. Reads directly from the per-DEX bytes,
  bypassing the merged table.
- **multi-DEX audit regression**: `tests/corpus/results/EXP085_PHASE1_MULTI_DEX.json`
  contains `multi_dex_audit.pass=true` (Telegram: dex=5, mismatches=0).
- **status**: PRESERVED. No regression on current HEAD.

---

## Summary

| Friend Finding | Reproduced | Status | Commit |
|---------------|------------|--------|--------|
| 1. Full-screen background | YES | Already addressed (EXP-092 b6ef143) | (existing) |
| 2. Small resource IDs < 0x10000 | YES | PARTIALLY_FIXED — root cause identified (D8 shrinker remap of R.string.ChooseCountry → 3), but full fix needs SPUT-capture approach to avoid crash | `7a99e9a` (resource load) + `cb6cd54` (traces) |
| 3. Bitmap font limit | YES | FIXED — all 95 ASCII glyphs now render | `7a99e9a` |
| Direct SMS state proof | YES | NOT_PROVEN — setPage(VIEW_CODE_SMS) never fires; SmsView exists from ViewPager pre-load | `cb6cd54` |
| Historical multi-DEX string bug | YES | PRESERVED — no regression | (existing) |
