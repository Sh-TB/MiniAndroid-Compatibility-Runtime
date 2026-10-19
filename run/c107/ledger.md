# CONT-107 LEDGER — issue #364

**Wave:** CONT-107 (elephant batch) · **Base:** origin/main `44bbcb21` (CONT-106) · **Final binary:** `1e3efdb4209764a9` (lineage: baseline `f72413b74525d3b0` reproduced byte-identical ×2 independent rebuilds → `3b5ca178710c171f` F-447+F-450 → final +F-452) · **Registry:** 764 → **767** (F-NEW-450/451/452 new; F-NEW-447 closed; F-NEW-448/449 refreshed) · **Evidence:** `evidence/cont107/evidence.json`

## بازیابی کانتینر
Snapshot کهنه دوباره (`e99c2fbd`، رجیستری 566) → reset به origin/main؛ بازسازی کامل باینری **بایت‌یکسان** `f72413b74525d3b0`. #364 خوانده شد: **۷۲ کامنت؛ صفر کامنت جدید بعد از baseline 6261275449** — مأموریت = فهرست مالکیتِ اعلام‌شدهٔ CONT-106. تعمیر پروب کانتینر-تازه (پیشینهٔ cont98/105/106): gate_a_probe بازسازی شد (lib `ad413625` مطابق رکورد CONT-105) + install+run کانونی → **Gate A 98/0/1**؛ c72priv v1/v2 بازسازی شد.

## فیکس‌های موج (هر سه fixture-first با A/B باینری)

### F-NEW-447 — ROOT-059 caller-domain gate (بسته شد)
**قانون:** مسیرِ کمکیِ null-recv→shadow فقط وقتی مجاز است که فریمِ فراخوان framework-owned باشد؛ فراخوانِ app-DEX باید NPE وفادار-به-ART بگیرد (مارکر bounded `[F447-NPE]`).
**پروب c106a:** `[C106-INVOKE2]` از **NO-EXC به NPE**؛ بقیهٔ ردیف‌ها دست‌نخورده. **اپ واقعی:** تلگرام یک سایت را نشان داد (`c41.run` روی Locale نال) — که به F-NEW-452 رسید؛ opencalc **صفر** مارکر (اثرِ صفر سایت تغییرکرده). شطرنج: صفر مارکر.

### F-NEW-450 — قانون بعد TypedArray (بسته شد، ریشهٔ جدید)
**ریشه:** اسلات‌های dimension عبارت RAW complex را بدون تبدیل به خواننده می‌دادند (مرحلهٔ theme/XML خام، فقط مرحلهٔ 327 تبدیل می‌کرد — ناسازگاریِ بین-مرحله‌ای). **فیکس:** پرودیوسرها `array_type[i]` را (نوشتارِ شرطی-بی‌شرط per-slot، قانون F-NEW-197) ثبت می‌کنند و همه‌جا RAW ذخیره می‌کنند؛ خواننده‌ها تبدیل می‌کنند (pixel_size / offset / layout). اسلات‌های تایپ‌نشدگیِ قدیمی دقیقاً رفتارِ قدیمی.
**پروب c106b2 (فیکسچر جدید):** `dim` از **14337 خام → 147px = 56dp × 2.625 = AOSP-true**؛ resolve/type/static/measure همه سبز.

### F-NEW-452 — Configuration.locale non-null (بسته شد، ریشهٔ جدید)
**دیکد:** `c41.run` pc=65 `iget-object Configuration;->locale` نال برمی‌گرداند → NPE وفادار-به-ART در `Locale.getLanguage` (AOSP setToDefaults: locale هیچ‌وقت نال نیست). **فیکس:** singleton `getConfiguration` یک Locale پیش‌فرض می‌کارد. **نتیجه:** مارکرهای F447-NPE تلگرام 1→0؛ PNG تلگرام **بایت‌یکسانِ** baseline پیش-107 (`20ac8cbbbb692e63`).

## دیکدهای صادقانه (بدون فیکس — ثبت شفاف)

- **F-NEW-448 — تئوریِ قبلی رد شد:** `sget-boolean Ll/m3;->a:Z` در آغاز `Toolbar.onMeasure` یک **trigger مردهٔ class-init** است (رجیستر نتیجه بلافاصله overwrite می‌شود؛ **صفر نویسنده** در کل APK؛ تنها خواندنِ static در onMeasure). تئوریِ «استاتیک ارتفاعِ theme» CONT-106 غلط بود. تولبار شطرنج هنوز **1080x0** — ریشهٔ واقعی = زنجیرهٔ content/min-height. **CONFIRMED_OPEN_GAP با دیکدِ اصلاح‌شده.**
- **F-NEW-449 — کنترل-منفی سبز:** پروب c106b (فیکسچر جدید) روی موتور **کاملاً سبز** (count 11/11، Unsafe offsets 11/11 بدون throw، order stable). قانونِ reflection-count موتور در این بهینه‌سازی سازگار است؛ OOB واقعی n2.r به متادیتای MessageInfo نیاز دارد. **CONFIRMED_OPEN_GAP + کنترل ثبت‌شده.**
- **F-NEW-451 — گپِ جدیدِ صادقانه:** زیر قانونِ صحیح F-450، چهرهٔ opencalc به **keypad-only** تغییر کرد (umanoPanelHeight خام 10497 → 108px صحیح). A/B: باینری پیش-107 چهرهٔ قدیم را بایت‌یکسان بازتولید می‌کند؛ صفر مارکر F447؛ ۱۷ خواندنِ gated بین دو باینری یکسان. WANT با حکمِ adjudication به `13d2d6d836f75e7f` ×3 re-pinned شد (پیشینهٔ F-NEW-443 dooz). دیکدِ پایین‌دستی = موج بعد.

## باتری کامل — سبز در `1e3efdb4209764a9`
wall **۱۲/۱۲ MATCH ×3** (dooz `d602648e` / opencalc `13d2d6d8` re-pinned / unote `90a67cc1` / microtimer `bbd350b6`) · goldens **۴/۴** · negatives **۱۹/۱۹** · MG-310 **۷/۷** · MG-150 **۳/۳** · selftest **۱۳/۱۳** · F-NEW-376 **۷۰/۷۰** · Gate A **98/0/1** · c104i **۴/۴** · c74esc **۵/۵** · ردیف‌های c106a/c106b2/c106b همگی terminal.

## نرخ موفقیت
- **۱۲/۱۲ واحد کاری به وضعیت پایانی رسیدند** · **۳ فیکس کامل** (F-447/F-450/F-452 با پروب + اثبات real-app) · **۲ دیکد صادقانه** (448 ردِ تئوری + 449 کنترل-منفی) · **۱ گپ جدید با lever** (451) · recovery + re-pin + باتری + رجیستری + push
- نرخ بسته‌شدن کامل: **۵/۱۲ (~۴۲٪)** · وزن‌دار ≈ **۸۳٪** (هر فیکس fixture-first تمام‌قد با A/B باینری و صفر دریفتِ ناموجَّه)
- رجیستری: main == mirror == **767**، id-unique
