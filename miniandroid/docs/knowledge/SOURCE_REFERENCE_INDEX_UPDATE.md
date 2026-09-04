# SOURCE_REFERENCE_INDEX — به‌روزرسانی کمپین Unified (append-only)

**تاریخ:** 2026-08-27 · این فایل مکمل `miniandroid/docs/knowledge/SOURCE_REFERENCE_INDEX.md` است (جداول جدید اضافه شود، چیزی حذف نشود).

## کتابخانه‌های به‌کاررفته/اثبات‌شده در این کمپین

| کتابخانه | نسخه sandbox | منبع | SHA/ریفرنس | لایسنس | نقش | وضعیت |
|---|---|---|---|---|---|---|
| Samsung/rlottie | depth-1 clone 2026-08-27 | github.com/Samsung/rlottie | `4307553814dbc03f54b99b0d49651c1e4429bf2d` | MIT | AnimationBackend (CM-026) | بازسازی static manual (35 TU) |
| FriBidi | 1.0.16 | fribidi.org (Debian) | pkg-config | LGPL-2.1 | bidi | POC PROVEN |
| HarfBuzz | 10.2.0 | harfbuzz.github.io | pkg-config | Old-MIT | shaping | POC PROVEN |
| FreeType | 2.13.3 | freetype.org | pkg-config | FTL/GPL | metrics/raster | POC PROVEN (مقایسه قبلی هم) |
| libwebp | system | developers.google | — | BSD | ImageBackend | موجود در build |
| libjpeg | system | IJG | — | IJG | ImageBackend | موجود در build |
| zlib | system | — | — | zlib | Archive | موجود |

## منابع AOSP/مرجع مورد استناد جدید

| منبع | استفاده |
|---|---|
| AOSP `TextDirectionHeuristics.FIRSTSTRONG` | الگوریتم base-direction در POC تایپوگرافی |
| AOSP `Uri.java` (frameworks/base) | مرجع پیاده‌سازی پیشنهادی T2-WS-C3 |
| AOSP minikin `Layout::splitByBidi` | الگوی production برای shape-per-run (محدودیت ثبت‌شده POC) |
| Robolectric nativeruntime (SQLiteMode.NATIVE) | precednet SQLite-as-data (WS-C4 D1) |
| dexlib2/baksmali (google/smali) | cross-check پارسر DEX |

## اجراهای real-APK این کمپین

| APK | SHA256 | نتیجه |
|---|---|---|
| Telegram 12.10.1 (vc 70389) | `f5e1192725772960cc94b83e54ffd8939f876b2b6e5f21d4a8537eb6fcba50e6` | exit=0، 12,544 کلاس، 41,233px، 3/3 deterministic (`06fb40da…`) قبل و بعد از UC-CM-001 |
