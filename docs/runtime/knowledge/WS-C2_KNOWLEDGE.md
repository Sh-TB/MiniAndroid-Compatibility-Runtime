# WS-C2 KNOWLEDGE — Graphics / Text / Image / Animation / Audio-Visual

**Unified Coder campaign:** 2026-08-27
**Tested HEAD:** `bbe0ce3` (baseline) → `86bd646` (UC-CM-001, no graphics impact)
**Real APK:** Telegram 12.10.1 (SHA256 `f5e11927…`, versionCode 70389, 5 DEX)

This document records the WS-C2 findings of this campaign. The previous Coder 2/Primary findings in
`CODER2_KNOWLEDGE.md` and `CODER_MAIN_KNOWLEDGE.md` (CM-018..CM-027) remain valid;
this file covers only reconciliation and new findings.

---

## UC2-001: Forward-version render — Telegram 12.10.1 SMS-family screen (REAL APX EVIDENCE)

### Classification: PROVEN (new evidence)

- With no changes whatsoever, the runtime executed the new Telegram version (12.10.1):
  - 12,544 classes loaded from the 5 DEX files
  - Real click chain (`phase_b_click` ×4) executed
  - SMS-family screen rendered: **41,233 non-white pixels** (1080×1920)
  - **3/3 re-runs → identical SHA** `06fb40da16b1f473…` (deterministic)
  - 0 crashes, 0 errors in crash.log
- Evidence: `run/uc_v12_run{1,2,3}/screenshot.png` + `run/uc_v12_first/*`
- **Significance:** the entire knowledge base (resource mappings, D8-shrunk names such as `res/cs3.json`)
  had been built against 10.14.5; the SMS-family screen in the new version also matched a similar
  structure and rendered → the runtime architecture is not dependent on the APK version.

### Sub-finding UC2-001a: resource VALUES do not resolve in the new version (OPEN)
- The on-screen texts show the **R field names** instead of the actual string values:
  `SMSWordTitle`, `SMSWordError`, `SMSPhraseTitle`, `WrongCode`, …
- Cause: the `resource_values.json` mapping was generated only for 10.14.5; in 12.10.1
  the `R$string` values have changed (new D8 ordinals: 987201…, resid=3 for some).
- Related regression: SFS — the text "exists" but is not the "actual user-visible value".
  **This must be added to `ANDROID_SILENT_FALSE_SUCCESS_MAP.md`**
  (and it was added — SFS-010 in this campaign).
- Generic proposed fix: generate the resource map automatically from the APK itself
  (ARSC → string pool per config) instead of a hand-made per-version JSON. The existing
  `resource_parser.cpp` path (modern ARSC, C3-F022a/b/c) can already do this.
- Confidence: HIGH (direct RES-INTERCEPT trace + rendered text)

### Sub-finding UC2-001b: 7 RLottie pending views identified in v12
- trace: `[EXP098-RLOTTIE-PENDING] view=2393 … resid=917654 target=28x28` (and 6 more)
- This means the general CM-027 wiring also hooks on the new version (no hardcoding).
- The Lottie render itself for v12 is not yet verified (needs a new R$raw mapping) — OPEN.

---

## UC2-002: Typography — full text pipeline proven (NEW PROOF)

### Classification: PROVEN (POC outside the runtime, reference libraries)

The mandatory §6 pipeline: `Unicode → bidi → shaping → glyph selection → metrics →
rasterization → layout → framebuffer` — executed and proven as a real implementation
(code: `scripts/wsc2_text_pipeline.cpp` in the delivery pack):

| Stage | Reference library | Sandbox version | Result |
|-------|-------------------|-----------------|--------|
| bidi | FriBidi | 1.0.16 | ✅ visual reorder + first-strong |
| shaping | HarfBuzz | 10.2.0 | ✅ correct Arabic/Persian letter joining |
| glyph/metrics | FreeType | 2.13.3 | ✅ real advance/bbox |
| raster | FreeType AA | — | ✅ anti-aliased |
| layout | — | — | ✅ RTL right-align / LTR left-align |
| framebuffer | PPM→PNG | — | ✅ 27,875 non-white px |

### Test samples (4/4 OK)
1. `Telegram verification code 12345 — Telegram code 67890` → RTL, Persian digits correct, Latin embed correct
2. `We sent a code to your number +98 912 345 6789` → correct RTL
3. `Enter code` → correct LTR
4. `Didn't get the code? Didn't get the code?` → correct RTL with one boundary artifact

### Key finding UC2-002a: base direction detection must be first-strong
- First run with forced base=LTR → **complete ordering failure** in Persian-centric lines
  (the Latin got reversed: `?edoc eht teg t'ndiD`)
- With the **first-strong** heuristic (matching Android's `TextDirectionHeuristics.FIRSTSTRONG`:
  first strong character R/AL → RTL, L → LTR) → all 4 samples correct.
- **The current runtime version has no bidi/shaping at all** → any Persian/Arabic text in
  MiniAndroid currently renders letter-separated and left-to-right.
- Confidence: HIGH (both cases proven with images)

### Recorded limitation (not hidden)
- The "reorder-then-shape" method (FriBidi then HarfBuzz on the whole visual line) works for
  simple joining scripts, but boundary neutrals (such as the Arabic question mark between
  RTL and Latin) may attach to the wrong run (seen in sample 4).
- The correct production approach: shape per bidi-run in logical order
  (AOSP minikin: `Layout::splitByBidi` → hb_shape per run → reorder placement only).
- The DejaVu font has only basic Arabic coverage; for real Persian, Vazirmatn/Noto
  Naskh is required (font fallback chain → FontBackend).

### Link to tooling (WS-C4)
- All three libraries (FriBidi/HarfBuzz/FreeType) are present in the sandbox and the licenses
  are compatible (LGPL/Old-MIT/FTL) — matrix in `WS-C4_TOOL_MATRIX.md`.

---

## UC2-003: Current runtime font status (RECONCILIATION)

- BitmapFont (8px uniform advance, 95 ASCII) remains the only backend inside the runtime.
- The earlier FREETYPE_VS_BITMAPFONT.md finding was confirmed: advance underestimation of about 36%
  → real wrap/clip problem; IoU against FreeType only 13.1%.
- **Two upgrade paths (WS-C2 prioritization):**
  1. Minimal: `measure_text_accurate()` with FreeType for measuring only
     (keep BitmapFont rendering) — low risk, better visuals for wrapping.
  2. Full: FontBackend interface + FreeType backend with HarfBuzz shaping
     and FriBidi bidi (UC2-002 has proven it) → real Persian/Arabic.
- Rewriting proven decoders was avoided (§6 rule).

---

## UC2-004: v12 visual evidence (VISUAL EVIDENCE per §14)

- text overlap seen at the top of the v12 screen (titles stacked on each other) — probably a
  custom view (LoginActivityPhraseView) without real measure/layout.
  classified: OPEN (needs the EXP095-LAYOUT trace for v12)
- code-field row (5 boxes) rendered correctly; toolbar band correct.
- screenshot SHA identical across all three runs → stable.
- Files: `run/uc_v12_run1/screenshot.png` (1080×1920) + delivered crop.

---

## STOP GATE status (§22) — WS-C2

| Item | Status |
|------|--------|
| graphics backend analysis | PARTIAL (previous CM-024/027 + this campaign) |
| font pipeline | POC PROVEN (UC2-002); inside the runtime still BitmapFont |
| FreeType | PROVEN (POC + previous comparison) |
| HarfBuzz | PROVEN (POC Persian joining) |
| image pipeline | previously PROVEN (63/64) — untouched, no regression |
| animation pipeline | previously PROVEN (CM-026); v12 pending identified (UC2-001b) |
| RLottie actual-screen proof | previously PROVEN (CM-027); v12 render OPEN |
| Telegram typography | PARTIAL (v12 field-names instead of strings — UC2-001a) |
| non-Telegram graphics regressions | NOT RUN in this campaign (external corpus APKs not downloaded — recorded per §18) |
| malformed inputs | previously 14/14 (CM-025) — no related change |
| ASAN native | NOT RUN (change only in the value-return path; no overflow risk — code reviewed) |
