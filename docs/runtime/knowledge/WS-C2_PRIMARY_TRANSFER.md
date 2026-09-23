# WS-C2 PRIMARY TRANSFER

**To:** Primary Coder · **From:** WS-C2 (Unified Coder) · **Date:** 2026-08-27
**Requested actions based on evidence, in order of value:**

## T1. Bring real typography inside the runtime (highest value)
- The pipeline was fully proven: `scripts/wsc2_text_pipeline.cpp`
  (FriBidi 1.0.16 → HarfBuzz 10.2.0 → FreeType 2.13.3) — connected Persian,
  correct RTL, correct metrics, 4/4 samples OK.
- ACTION: build the `FontBackend` interface in `src/renderer/`; first backend:
  FreeType+HarfBuzz+FriBidi with the **first-strong** base direction
  (copy the POC code). Keep BitmapFont as fallback.
- EVIDENCE: `run/wsc2_text_pipeline.{png,ppm}` + metrics JSON (27,875 px, 4/4)
- CONFIDENCE: HIGH · RISK: LOW (new interface, current path untouched)
- BENEFIT: Persian/Arabic — i.e. the main Telegram user base, Persian-speaking — becomes real.

## T2. v12 text = field name, not value (SFS-010)
- The per-version resource mapping is fragile. ACTION: auto-generate the string map
  from `resources.arsc` (the existing modern-ARSC parser in resource_parser.cpp) at
  load time, instead of the hand-made `resource_values.json`.
- EVIDENCE: `RES-INTERCEPT → SMSWordTitle` trace on v12 · CONFIDENCE: HIGH

## T3. Complete RLottie on v12
- 7 pending views identified (EXP098-RLOTTIE-PENDING trace) but no new R$raw mapping.
  Solved by T2 (the raw map also comes from ARSC). CONFIDENCE: MEDIUM-HIGH

## T4. Measure with FreeType for correct wrapping
- 36% advance underestimation (FREETYPE_VS_BITMAPFONT.md) → texts wrap too early.
  Minimum: `measure_text_accurate()`. CONFIDENCE: HIGH · RISK: VERY LOW

## T5. Text overlap of the v12 titles
- LoginActivityPhraseView without real layout. Re-test after T1/T4.

## DO NOT (per the §4/§6 rule)
- Do not remove BitmapFont (fallback + the no-freetype scenario).
- Put no Telegram-specific mapping in core (T2 must be generic from ARSC).
- Do not rewrite proven decoders (PNG/WebP/JPEG/RLottie).
