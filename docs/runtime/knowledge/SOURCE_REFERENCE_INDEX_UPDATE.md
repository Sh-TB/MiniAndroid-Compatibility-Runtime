# SOURCE_REFERENCE_INDEX — Unified campaign update (append-only)

**Date:** 2026-08-27 · this file complements `docs/runtime/knowledge/SOURCE_REFERENCE_INDEX.md` (add the new tables, remove nothing).

## Libraries used/proven in this campaign

| Library | Sandbox version | Source | SHA/reference | License | Role | Status |
|---|---|---|---|---|---|---|
| Samsung/rlottie | depth-1 clone 2026-08-27 | github.com/Samsung/rlottie | `4307553814dbc03f54b99b0d49651c1e4429bf2d` | MIT | AnimationBackend (CM-026) | manual static rebuild (35 TU) |
| FriBidi | 1.0.16 | fribidi.org (Debian) | pkg-config | LGPL-2.1 | bidi | POC PROVEN |
| HarfBuzz | 10.2.0 | harfbuzz.github.io | pkg-config | Old-MIT | shaping | POC PROVEN |
| FreeType | 2.13.3 | freetype.org | pkg-config | FTL/GPL | metrics/raster | POC PROVEN (previous comparison too) |
| libwebp | system | developers.google | — | BSD | ImageBackend | present in the build |
| libjpeg | system | IJG | — | IJG | ImageBackend | present in the build |
| zlib | system | — | — | zlib | Archive | present |

## New AOSP/reference sources cited

| Source | Use |
|---|---|
| AOSP `TextDirectionHeuristics.FIRSTSTRONG` | the base-direction algorithm in the typography POC |
| AOSP `Uri.java` (frameworks/base) | the reference implementation for the proposed T2-WS-C3 |
| AOSP minikin `Layout::splitByBidi` | the production pattern for shape-per-run (the POC's recorded limitation) |
| Robolectric nativeruntime (SQLiteMode.NATIVE) | the SQLite-as-data precedent (WS-C4 D1) |
| dexlib2/baksmali (google/smali) | DEX parser cross-check |

## Real-APK executions of this campaign

| APK | SHA256 | Result |
|---|---|---|
| Telegram 12.10.1 (vc 70389) | `f5e1192725772960cc94b83e54ffd8939f876b2b6e5f21d4a8537eb6fcba50e6` | exit=0, 12,544 classes, 41,233px, 3/3 deterministic (`06fb40da…`) before and after UC-CM-001 |
