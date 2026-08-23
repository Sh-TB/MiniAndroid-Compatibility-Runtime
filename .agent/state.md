# MiniAndroid Agent State — EXP-088+ Campaign

## Current Experiment
EXP-088+ — Long-horizon MiniAndroid generic compatibility campaign

## Current Commit (most recent state)
HEAD — A4 PROVEN + F PROVEN + intermittent-segfault root cause fixed (BitmapFont uninit memory)

## Status: 10 PROVEN, 1 BLOCKED (M)

### PROVEN this round
- **A4 (drawables/images)**: Real PNG pixel decoding end-to-end. A4.1-A4.7 all pass.
  - PNGDecoder: 4/4 color types byte-identical to PIL
  - draw_image: alpha-blends correctly
  - simplestopwatch tree: 3 ImageButtons rendered + PIL verified (591/591, 896/896, 704/704 pixel matches)
  - 3/3 reproducible runs (identical SHA)
- **F (Handler/Looper)**: 23/23 standalone C++ tests pass.
  - Implemented HandlerShadow::remove_callbacks() (was a no-op stub)
  - Implemented HandlerShadow::remove_all() (for removeCallbacksAndMessages(null))
  - Wired dispatch() to call the real methods
  - User scenario: post(A), post(B), postDelayed(C), removeCallbacks(B), drain → [A, C] ✓

### Root-cause fixes this round
1. **BitmapFont uninit memory** — `std::array<Glyph, 95> glyphs_` was default-initialized
   (POD struct → indeterminate member values). `fill_remaining_glyphs()` checked
   `if (glyphs_[i].character == '\0')` on uninitialized memory (UB). On most runs
   the garbage was '\0' so the body executed; occasionally garbage was non-zero
   and the body was skipped, leaving `bitmap` as a garbage pointer → segfault.
   FIX: `= {}` value-initializes the array. This was the "intermittent segfault
   in recursive rendering lambda" mentioned in the previous state — it was never
   the lambda's fault, it was the font system.
2. **PNG signature check** — bytes 2 and 3 were swapped (compared `0x47 0x4E`
   instead of `0x4E 0x47`). Affected both the runtime's stage_render_frame and
   the simplestopwatch_render test.
3. **PNGDecoder** — added `PNGDecoder::decode()` (zlib uncompress + PNG unfilter +
   color-type expansion to RGBA). Supports color types 0/2/4/6, bit depth 8,
   non-interlaced. All 5 PNG filter types (None, Sub, Up, Average, Paeth).
4. **SoftwareCanvas::draw_image()** — new method that draws decoded RGBA pixels
   onto the framebuffer with alpha-blending and optional nearest-neighbour scaling.
5. **Renderer wire-up** — replaced the placeholder rect + dimensions text in
   stage_render_frame with real PNGDecoder + draw_image calls.

## Mandatory Phase Status Table

| Phase | Status | Evidence |
|---|---|---|
| A1 (AXML inflation) | PROVEN | layout_cache.json + Python AXML parser |
| A2 (measure/layout) | PROVEN | Iterative BFS with MATCH_PARENT/WRAP_CONTENT |
| A5 (text rendering) | PROVEN | BitmapFont glyphs via SoftwareCanvas (now bug-free) |
| A4 (drawables/images) | **PROVEN** | PNGDecoder 4/4 + draw_image + simplestopwatch PIL-verified |
| B1 (PNG output) | PROVEN | zlib compress2 + crc32 |
| B5 (entry-point resolution) | PROVEN | Multi-DEX class injection |
| B (generic input/click) | PROVEN | findViewById + setOnClickListener + dispatch_click |
| B2 (event dedup) | PROVEN | one click = one onClick invocation |
| C (SQLite) | PROVEN | Python sqlite3 micro test 9/9 + independent validation |
| F (Handler/Looper) | **PROVEN** | 23/23 standalone C++ tests + removeCallbacks implemented |
| I (multi-DEX audit) | PROVEN | Per-DEX resolution functions audited |
| M (Telegram login) | BLOCKED | See "Phase M Blockers" below |

## Phase M Blockers (Telegram login regression)

Telegram LaunchActivity.onCreate now executes successfully (1330 instructions, no segfault) thanks to the BitmapFont fix. But the full login chain is blocked at multiple points:

### First failing boundary (precise)
`UserConfig.isClientActivated` returns "class not in index" — the runtime cannot resolve this method across the 5 Telegram DEX files. This causes LaunchActivity.onCreate to take the "user not activated" path that *should* transition to LoginActivity, but the unresolved method call returns null/false and the transition does not happen.

Evidence:
```
[TRY-INVOKE] Lorg/telegram/messenger/UserConfig;.isClientActivated depth=2
[RET-NOTFOUND] class_descriptor=Lorg/telegram/messenger/UserConfig; method=isClientActivated (class not in index)
```

UserConfig class descriptor `Lorg/telegram/messenger/UserConfig;` is present in classes3.dex, classes4.dex, classes5.dex (verified via zipfile inspection).

### Subsequent blockers (in order)
1. **UserConfig multi-DEX resolution** — Phase I audit verified per-DEX indexing is correct, but method resolution across DEXes during invoke-static may have an issue. Needs investigation.
2. **LoginActivity.onCreate transition** — even if UserConfig.isClientActivated resolves, the runtime needs to actually transition to LoginActivity (which means executing LoginActivity.onCreate bytecode).
3. **PhoneView rendering** — LoginActivity uses a PhoneView. No layout_cache.json exists for Telegram's login layouts (resource paths are obfuscated).
4. **Phone number injection** — no harness mechanism to inject a phone number into the EditText field.
5. **Mock auth.sendCode response** — Telegram's `PhoneView.onNextPressed()` calls `SendRequestDelegate` which calls `auth.sendCode`. No mock infrastructure exists.
6. **SMS view rendering** — needs setPage(VIEW_CODE_SMS) to actually swap the visible view.

## Resume Instructions (next round)

1. The campaign is NOT complete. M is BLOCKED.
2. **Exact next action**: Investigate the `UserConfig.isClientActivated` "class not in index" error.
   - It's a multi-DEX method resolution issue.
   - Phase I audit verified per-DEX indexing is correct, but invoke-static across DEXes may be the bug.
   - Reproducer: `cd miniandroid && ./build/miniandroid run download/exp038_telegram/Telegram.apk`
   - Search trace for: `RET-NOTFOUND class_descriptor=Lorg/telegram/messenger/UserConfig;`
3. If the multi-DEX issue is fixed and LoginActivity.onCreate executes:
   - Generate a layout_cache.json for Telegram's login layout
   - Wire phone number injection
   - Mock auth.sendCode
4. After M is PROVEN, the campaign is complete (10/11 PROVEN + M = 11/11).
5. Do NOT mark M as PROVEN unless the full chain works end-to-end.

## Build artifacts
- `/home/z/my-project/scripts/a4_build.sh` — builds all A4 tests + Phase F test
- `/home/z/my-project/scripts/a4_01_create_known_png.py` — generates deterministic PNGs
- `/home/z/my-project/scripts/a4_05_pil_verify_rendered.py` — PIL-verify single-image renders
- `/home/z/my-project/scripts/a4_07_pil_verify_simplestopwatch.py` — PIL-verify simplestopwatch render
- `/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/tests/exp088_a4_png_decoder_test.cpp` — A4.3 test
- `/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/tests/exp088_a4_render_image_test.cpp` — A4.4+A4.5 test
- `/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/tests/exp088_a4_render_multi_test.cpp` — A4.6 test
- `/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/tests/exp088_a4_simplestopwatch_render.cpp` — A4.7 test
- `/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/tests/exp088_phasef_handler_queue_semantics.cpp` — Phase F test

## Reproducibility
- All A4 tests pass: 3/3 reproducible runs (identical screenshot SHA)
- All Phase F tests pass: 23/23 (deterministic, no time dependence)
- All regression tests pass: A1, B, B2, C, F, I — no regressions introduced
