# DIFFERENTIAL_TESTING_010 — oracles and three-way comparisons (R22)

## 1. PNG decode: three-way RGBA differential (the campaign's flagship oracle)

Input: 7,036 real APK PNGs (8 APKs, IHDR-profile: 4,255 palette incl. 169
sub-8-bit, 1,835 gray+alpha, 467 rgba, 449 gray, 30 rgb).

| Comparison | Result |
|---|---|
| libpng 1.6.48 vs stb_image v2.30 | **byte-identical RGBA on ALL common files** |
| custom (pre-010) vs libpng | 6,827/6,830 identical; 3 diffs = tRNS bugs in custom |
| custom success rate | 97.07% (206 hard failures: sub-8-bit depths) |
| libpng/stb success | 100% |

Timing: custom 1,583 ms · libpng 958 ms · stb 698 ms (corpus total).
Method: per-file TSV with FNV-1a-64 of the RGBA buffer, joined by script
(`run/uc010_png_harness.cpp`, `run/uc010_stb_bench.cpp`).

PIL fixture oracle (12 cases, `tests/exp088_a4_png_decoder_test.cpp`):
12/12 byte-identical post-adoption, incl. tRNS colorkey (RGB + gray +
palette), Adam7, 16-bit gray (strip→>>8 semantics), 1-bit gray, 4-bit palette.
Fixture-generation finding recorded: **PIL drops transparency kwargs when
saving RGB/L PNGs** — fixtures require manual tRNS chunk injection.

## 2. Layout: Yoga vs custom `measure_layout`

Real GMDice `act_gmdice` AXML through the runtime ResourceRuntime stack:
10/10 nodes within 8px (max 2.2px, dp point-grid rounding), 6/10 within 1.5px;
speed ratio ~35–39× Yoga-favor. Output table preserved in
`evidence/uc010_yoga_differential.txt`.

## 3. GLES: golden-cube pixel oracle

PortableGL output vs expected scene semantics: background = clear color
(20,25,35 ±3 tolerance), Lambert-lit faces (yellow +Z fully lit → 241,241,0 at
center), depth-tested faces (evidence PNGs). Non-background coverage 10.0% /
25.7% at the two resolutions — exact cube silhouette expectations.

## 4. Bidi: FriBidi vs SheenBidi

Ran on the §14 Persian case set (pure RTL / mixed / Eastern digits / embedded
LTR). Uncalibrated level diffs reported — the harness mixed base-direction
policies (FriBidi PAR_ON auto vs SheenBidi SBLevelDefaultLTR). Verdict
deliberately: **buildability proven, semantic verdict pending recalibrated
run**; FriBidi remains the §14-PROVEN pipeline. No adoption claim.

## 5. Stack-trace semantics: interpreter vs Kotlin Intrinsics expectations

Before: stack-walk livelock (HALT-LOOP). After: real frames
(`top=LM1/i;`) → Intrinsics throws real NPE with propagation (9 records).
Oracle: real Kotlin Intrinsics behavior on device (throw NPE naming the
method + parameter).

## 6. Standing goldens as regression oracles

GMDice pixdata SHA-16 `26fc4116e4ba65b4` (158,040 non-white px) and Telegram
pixdata `b9b06072ea17d7fd` (41,233 px) — checked after EVERY adoption
(REGRESSION_010.md). These function as render-level differential oracles for
the whole pipeline (AXML → ARSC → layout → draw → PNG encode).
