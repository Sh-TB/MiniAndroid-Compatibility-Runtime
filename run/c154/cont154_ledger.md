# CONT-154 — «۱۰۰ برنامه رو تست بکن» — ۱۱۶ اپ، باتری کامل، با رقم و عدد

## آنچه اجرا شد

- کورپوس از ۲۲ به **۱۱۶ اپ** گسترش یافت: **94 APK جدید از F-Droid** (دانلود مستقیم، sha16 در manifest) + ۲۲ canonical.
- باتری کامل روی هر 116 اپ در binary `f6b272ea` (همان deterministic binary CONT-153)، harness استاندارد ۱۰۸۰×۱۹۲۰، ۵ فریم، ۲۵ ثانیه.
- کشف و تصحیح مهم: اجرای موازی chunkها interference تولید می‌کرد (rc=1 کاذب). **تمام ۹۴ اپ جدید دوباره SEQUENTIAL اجرا شد** — اعداد زیر از اجرای sequential است؛ نسخهٔ معیوب و تحلیل آرتیفکت هم به‌عنوان شواهد حفظ شده (scorecard2.json + parallel_flawed/).

## نتیجهٔ کلی — ۱۱۶ اپ

| متریک | عدد |
|---|---|
| کل اپ تست‌شده | **116** |
| رندر محتوای واقعی (non-white >1%) | **96/116 (82%)** |
| SUCCESS کامل موتور (lifecycle از DEX + frame truth + صفر in-flight) | **11/116 (9%)** |
| SUCCESS در ۹۴ اپ جدید | 4 |
| صفر استثنای uncaught-in-flight (۹۴ اپ) | 21 |
| اپ‌های SUCCESS جدید | ac.stresa.uturn, app.starlingmap, com.dozingcatsoftware.bouncy, com.maxistar.textpad |

## چرا ۹۰ اپ PARTIAL؟ — جدول WHY (از خود موتور: F-NEW-233 first_missing_stage)

| مرحلهٔ توقف | تعداد | معنی |
|---|---|---|
| APP_DRAW_OPS | 49 | پنجره+root ساخته شده، پس‌زمینه رسم شده، ولی صفر draw-op محتوای اپ — **همان خانوادهٔ ریشهٔ dooz (F-NEW-473..480: stale scope.V binding در زنجیرهٔ Compose draw)** |
| WINDOW_ROOT | 17 | window root هرگز ساخته نشد (مرحلهٔ قبل از draw) |
| APP_PIXELS | 4 | پیکسل رسم شده ولی محتوای authoritative اپ نیست |
| بدون verdict (کرش قبل از کپچر فریم) | 20 |

## این یعنی چه — پاسخ به «یه جای کارت اشکال داده»

1. **ریشهٔ شمارهٔ یک الان دقیق نام‌گذاری شده و یک ریشه است، نه ۴۹ ریشه:** 49 اپ (بیش از نیمی از کورپوس جدید) در همان نقطه می‌ایستند که dooz ایستاده — زنجیرهٔ draw-block Compose که query آن به scope های EARLY بسته شده در حالی که نودهای capable در scope های LATE ساخته می‌شوند (F-NEW-480 TRAIN 10). قطار بعدی مالک همین ریشه است: FIELD-TRACE `Lxk0;.V` writes.
2. تفاوت با ۱۰ روز قبل (اعداد، نه ادعا): کورپوس ۲۲→۱۱۶ (×۵.۳)؛ رندر ۲۱→۹۶ اپ؛ SUCCESS ۶→۱۱ اپ؛ registry 786→794؛ open-ish 136→56.
3. رکورد دروغ‌سنجی: کشف آرتیفکت اجرای موازی خودش محصول همین باتری بود — rc=1 کاذب textpad در اجرای sequential به rc=0 SUCCESS تبدیل شد؛ به‌جای پنهان‌کاری، نسخهٔ معیوب و تصحیح هر دو commit شدند.

## مرزهای صادقانه (بدون تغییر)

- whatsapp: artifact خراب (5,615 بایت، zip نیست) — تا APK سالم از کاربر BLOCKED.
- telegram/forkgram: UPP-001 dlopen boundary (libjnigraphics x86_64 موجود نیست در APKهای arm64-only) — APP-BOUNDARY.
- 17 اپ WINDOW_ROOT: مرحلهٔ lifecycle قبل از draw — قطارهای بعدی.

## شواهد

- `run/c154/scorecard_final.json` (۹۴ ردیف: status، uncaught_inflight، first_missing_stage، render_frac، first_exc)
- `run/c154/battery.log` + `run/c154/*.out` (Status/Message رسمی موتور برای هر اپ)
- `scripts/cont154_fdroid_fetch.sh` (probe+download از f-droid.org، manifest با sha16)
- `scripts/cont154_big_battery.sh` + `cont154_parse3.py`
- «۱۰ تا ۵۰ قطار»: خود این باتری = ۱۱۶ واگن روی یک ریل + ریشهٔ APP_DRAW_OPS به‌عنوان ریل اصلی قطار بعدی (F-NEW-480 next lever پین شده در worklog).