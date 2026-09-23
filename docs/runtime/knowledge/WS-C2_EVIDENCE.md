# WS-C2 EVIDENCE — campaign evidence list (per §14)

**Date:** 2026-08-27 · all files relative to `miniandroid/` (unless a full path)

## A. Real APK execution (Telegram 12.10.1)

| Artifact | Path | SHA/value |
|----------|------|-----------|
| APK | `download/exp038_telegram/Telegram.apk` | `f5e1192725772960cc94b83e54ffd8939f876b2b6e5f21d4a8537eb6fcba50e6` |
| screenshot ×3 (before change) | `run/uc_v12_run{1,2,3}/screenshot.png` | all three `06fb40da16b1f473980cfea9…` |
| screenshot ×3 (after UC-CM-001) | `run/uccm001_run{1,2,3}/screenshot.png` | all three `06fb40da16b1f473980cfea9…` (unchanged) |
| top-crop preview | `run/uc_v12_top.png` (+ small) | — |
| report | `run/uc_v12_first/report.md` | 12,544 classes, 0 errors |
| pixel statistics | stderr `[EXP092-COPY]` | 41,233 non-white (1.99%) |
| ViewTree traces | stderr `EXP092-RENDER` | node=3746 TextView "WrongCode" depth=3 |
| RLottie pending | stderr `EXP098-RLOTTIE-PENDING` ×7 | resid=917654/917529/917634/917597/3 |

## B. Typography POC (UC2-002)

| Artifact | Path | Value |
|----------|------|-------|
| POC code | delivery pack: `scripts/wsc2_text_pipeline.cpp` | — |
| framebuffer | `run/wsc2_text_pipeline.ppm` / `.png` | 1080×340 |
| metrics JSON | `run/wsc2_text_pipeline_metrics.json` | 4/4 ok; RTL:3, LTR:1 |
| non-white | — | 27,875 |
| Libraries | pkg-config | fribidi 1.0.16 / harfbuzz 10.2.0 / freetype2 26.2.20 (2.13.3) |
| Font | DejaVuSans.ttf | basic Arabic coverage (for production: Vazirmatn needed) |

## C. Build/tooling

| Artifact | Path | Value |
|----------|------|-------|
| rlottie source | `/home/z/my-project/tools/rlottie` (outside the repo) | Samsung/rlottie `4307553814dbc03f54b99b0d49651c1e4429bf2d` (depth-1) |
| librlottie.a | `tools/rlottie/build/src/librlottie.a` | 1.2MB, 35 TU |
| runtime build log | make -j4 | SUCCESS; only the previous `-Wunused-parameter` warnings |
| binary | `build/miniandroid` | 49,818,192 bytes (after the change) |

## D. Things not proven (honestly, §18)

- non-Telegram APK regression in this campaign: **NOT RUN** (corpus download not done)
- ASAN: **NOT RUN** (the change is only return-value mapping; no pointer/array
  semantics changed — code review done)
- RLottie render on v12: **OPEN** (needs a new R$raw map)
- GPU/GLES paths: N/A (the runtime is a CPU path)
