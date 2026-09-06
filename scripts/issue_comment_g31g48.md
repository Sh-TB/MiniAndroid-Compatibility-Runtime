## G31–G48 — REAL TYPOGRAPHY CAMPAIGN → GOLDEN-01 CLOSED (9/9 static checks) — commits ea51d96a → f2717ab6 → 84ce8c21

**CLAIM.** The frozen external APK `EXT-01 HelloWorldSelfAware v1.1.0` (SHA-256 `009b4671…cc41`) renders with real Android typography laws in MiniAndroid: AOSP `fonts.xml` family resolution, `Paint.FontMetrics` + `StaticLayout` line-box law, `TextAppearance` resource→`22sp`→`px` law, AOSP line-spacing law (`lineSpacingMultiplier`/`Extra`, `includeFontPadding`, `elegantTextHeight`), and ARSC version-qualifier selection — proven pixel-quantitatively against the author-published reference screenshot, never a single similarity number.

**COMMITS.** `ea51d96a` (fonts.xml monospace family + ARSC version-qualifier law) · `598e2432` (G36/G37 FontMetrics+line-box law) · `b9e6e66f` (G46 TextAppearance 22sp→px TypedValue rounding) · `98794ed0` (G47 AOSP line-spacing plumbing) · `f2717ab6` (G48 golden record, battery 11→16 stages) · `84ce8c21` (font pipeline probe evidence).

**TEST.** Battery extended 11 → **16 stages, ALL PASS**; helloworld **26/26**, tictactoe **8/8**, mutf8 **14/14**, semantic **96/96**.

**QUANTITATIVE EVIDENCE** (`docs/evidence/G48_TYPOGRAPHY_GOLDEN.md`, `typography_golden.json` committed):

| Quantity | Reference | MiniAndroid | Δ |
|---|---|---|---|
| background | black | black | 0 |
| text block rel. height | 0.2474 | 0.2458 | **0.64 %** |
| text block rel. width | 0.6433 | 0.6231 | 3.14 % |
| center x / y | 0.4992 / 0.5037 | 0.5000 / 0.5023 | 0.08 / 0.14 % |
| line spacing (B2B/h) | 0.07076 | 0.07187 | **1.58 %** |
| monospace advance/char | 0.03208 | 0.03111 | 3.03 % |

**GOLDEN-01 VERDICT: PASS (9/9 static checks)** — background, ink presence, 4-line band structure, H/V centering, block width/height, line spacing, monospace advance. Per-line ink geometry tables committed. Dynamic device values (`ANDROID_ID`/API levels) are same-length by design and are never compared; static geometry fully checked. The one known residual (first line gap +6 px @1080-scale, `fm.top`≠`fm.ascent` behavior) is recorded, quantified, and not fitted away.

**DETERMINISM.** 3 independent runs → PNG byte-identical, SHA-256 `142238fd92b69e11d3407526de95cad29bf46e3f4191767d09a24379fbe0bbf2`.

**EVIDENCE FILES.** `docs/evidence/G48_TYPOGRAPHY_GOLDEN.md` · `docs/evidence/GOLDEN01_EXTERNAL_HELLO_GATE_RECORD.md` · `docs/evidence/external_hello_golden/` (miniandroid_typography.png, font_pipeline_probe_58px.txt, structural_comparison.txt) · comparator `scripts/compare_ext01_typography.py`.

All commits pushed to `main` (HEAD `dc18dcd2` verified via `git ls-remote` read-back this session).
