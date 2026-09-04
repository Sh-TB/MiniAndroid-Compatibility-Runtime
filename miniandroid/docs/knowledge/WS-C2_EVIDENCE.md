# WS-C2 EVIDENCE — فهرست شواهد کمپین (per §14)

**تاریخ:** 2026-08-27 · همه فایل‌ها نسبت به `miniandroid/` (مگر مسیر کامل)

## A. اجرای real APK (Telegram 12.10.1)

| Artifact | مسیر | SHA/مقدار |
|----------|------|-----------|
| APK | `download/exp038_telegram/Telegram.apk` | `f5e1192725772960cc94b83e54ffd8939f876b2b6e5f21d4a8537eb6fcba50e6` |
| screenshot ×3 (قبل تغییر) | `run/uc_v12_run{1,2,3}/screenshot.png` | هر سه `06fb40da16b1f473980cfea9…` |
| screenshot ×3 (بعد UC-CM-001) | `run/uccm001_run{1,2,3}/screenshot.png` | هر سه `06fb40da16b1f473980cfea9…` (بدون تغییر) |
| پیش‌نمایش برش بالا | `run/uc_v12_top.png` (+ small) | — |
| report | `run/uc_v12_first/report.md` | 12,544 classes, 0 errors |
| pixel statistics | stderr `[EXP092-COPY]` | 41,233 non-white (1.99%) |
| ViewTree traces | stderr `EXP092-RENDER` | node=3746 TextView "WrongCode" depth=3 |
| RLottie pending | stderr `EXP098-RLOTTIE-PENDING` ×7 | resid=917654/917529/917634/917597/3 |

## B. تایپوگرافی POC (UC2-002)

| Artifact | مسیر | مقدار |
|----------|------|-------|
| کد POC | پک تحویلی: `scripts/wsc2_text_pipeline.cpp` | — |
| framebuffer | `run/wsc2_text_pipeline.ppm` / `.png` | 1080×340 |
| metrics JSON | `run/wsc2_text_pipeline_metrics.json` | 4/4 ok؛ RTL:3، LTR:1 |
| non-white | — | 27,875 |
| کتابخانه‌ها | pkg-config | fribidi 1.0.16 / harfbuzz 10.2.0 / freetype2 26.2.20 (2.13.3) |
| فونت | DejaVuSans.ttf | پوشش عربی پایه (برای تولید: Vazirmatn لازم است) |

## C. ساخت/ابزار

| Artifact | مسیر | مقدار |
|----------|------|-------|
| rlottie source | `/home/z/my-project/tools/rlottie` (بیرون repo) | Samsung/rlottie `4307553814dbc03f54b99b0d49651c1e4429bf2d` (depth-1) |
| librlottie.a | `tools/rlottie/build/src/librlottie.a` | 1.2MB، 35 TU |
| build log runtime | make -j4 | SUCCESS؛ فقط warning های `-Wunused-parameter` قبلی |
| binary | `build/miniandroid` | 49,818,192 bytes (بعد از تغییر) |

## D. چیزهایی که اثبات نشد (صادقانه، §18)

- non-Telegram APK regression در این کمپین: **NOT RUN** (دانلود corpus انجام نشد)
- ASAN: **NOT RUN** (تغییر فقط return-value mapping است؛ هیچ pointer/array
  semantics عوض نشد — بازبینی کد انجام شد)
- RLottie render روی v12: **OPEN** (نیاز R$raw map جدید)
- GPU/GLES مسیرها: N/A (runtime مسیر CPU است)
