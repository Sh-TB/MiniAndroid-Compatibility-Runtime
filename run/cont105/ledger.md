# CONT-105 RESULT — حالت دسته‌ای ×۵: ۲۹ واحد کاری در یک چرخه · ۱۸۴ حکم ریشه‌به‌ریشه · باتری کامل سبز · پوش تأیید شد

**Wave:** CONT-105 (×5 batch) · **HEAD:** `623561a9` (== origin/main — push verified) · **Registry:** 757 → **760** roots (F-NEW-443/444/445 + reconcile) · **Evidence:** `evidence/cont105/evidence.json` + `triage.md`

## بازیابی کانتینر و کشف بزرگ موج
کپی محلی دوباره snapshot کهنهٔ دورهٔ CONT-10 بود (e99c2fbd)؛ به `c9b0852b` (CONT-104) ریست شد. بازسازی **کامل** (همهٔ TUها، بدون lineage افزایشی) باینری `afaad5bd4f56f9d3` را داد — بایت‌متفاوت از `dd5118cc` ثبت‌شده. به‌جای پنهان‌کردن، ریشه‌یابی شد:

- **F-NEW-443 (ROOT-CAUSED-FIXED — ریشهٔ Harness):** سطر dooz دیوارِ wall به lineage ساخت حساس بود. `31ddd4d5` = قاب سفیدِ یکدست (مسیر GL، محصول build افزایشی با .o کهنه) در مقابل `d602648e` = قاب fafafa یکدست (مسیر نرم‌افزاری که windowBackground تم @0xfffafafa را با قانون EXT01-WINBG نقاشی می‌کند). دیکد PNG هر دو را «فقط-پس‌زمینه» ثابت کرد؛ چهرهٔ fafafa **AOSP-درست** است. WANT بازنگری و با حکم مستند دوباره سنجاق شد (×3 قطعی). بقیهٔ سطرها (opencalc/unote/microtimer/flappycow) بایت‌یکسان MATCH ×3.

## باتری کامل در باینری تازه — صفر دریفت رفتاری
goldens **4/4** · negatives **19/19** (بعد از تعمیر مستند کانتینر-تازه) · reinstall **8/8** · MG-310 **7/7** · MG-150 **3/3** · selftests **13/13** · F-NEW-376 **70/70** · پروب‌ها: c104i **4/4** · c74esc **5/5** · clinit1 (F-NEW-215 شلیک) · swipe1 (۱۳۱ ops) · sax1 (۱۲۸ خط SAX — این بار ساکت نبود)

## حکم‌های ریشه‌به‌ریشه (×۵)
- **۱۸۴ حکم** برای استخرهای PARTIAL (۱۱۲) + UNPROVEN (۷۲) با اسکریپت و بازبینی دستی: **HOLD-VERIFIED 9 · PARTIALLY_CONFIRMED 98 · BLOCKED_NEEDS_EVIDENCE 72 · STALE_OR_SUPERSEDED 5**. در دور اول ۳ حکم اشتباه (supersede کاذب از عنوان‌های کلی/توکن‌های ID) شناسایی و قواعد سخت‌گیرانه شد.
- **F-NEW-444 (NOT-APPLICABLE):** «شکاف merge مانیفست کتابخانه‌ای» CONT-104 برای AppLocalesMetadataHolderService **مثبت-کاذب بود** — aapt2 ثابت کرد سرویس در مانیفست ادغام‌شدهٔ هر دو APK وجود ندارد؛ AOSP هم همان NameNotFoundException را می‌دهد و appcompat خودش catch می‌کند. برابری موتور با AOSP برقرار است؛ هیچ تغییری زده نشد (فیکس اینجا = جعل سرویسی که AOSP ندارد).
- **F-NEW-445 (CLASSIFIED):** مرگ تلگرام در `o6;.k` — `<clinit>` اجرا شده (دو رنگ Paint موفق) ولی `o6.u1 (xj0)` در اولین استفاده null است؛ دیکد androguard: `sget u1 @0x56 → iput Y:Z`. یعنی مسیر کارخانهٔ lazy هرگز قبل از اولین استفاده اجرا نشده. قانون fixture-first؛ بدون fixture فیکسی زده نشد.
- F084-HALT-RETURN ×484 (pacing، بدون تغییر) · n2.r / chess-adapter / UPP-001 صادقانه حمل شدند.

## راستی‌آزمایی ثبت (bookkeeping)
شکاف ثبتِ CONT-104 پیدا و تعمیر شد: خانوادهٔ F-NEW-442..442e فقط در mirror بود — حالا در جدول اصلی هم هست. main == mirror == **760**، id-unique.

## نرخ موفقیت
- **۲۹/۲۹ واحد به وضعیت پایانی رسیدند** · **۲۲/۲۹ کاملاً بسته (۷۶٪)** · وزن‌دار ≈ **۸۵٪**
- به‌علاوهٔ ۱۸۴ حکم ریشه‌به‌ریشه (۱۴ بسته‌شده، ۱۷۰ بازِ صادقانه با اقدام بعدی مشخص)

## مالکیت موج بعد
پروب fixture-first برای F-NEW-445 (ترتیب initِ lazy-singleton) و بعد فیکس کلی · فیکس n2.r (compact-info) · فیکس adapter منوی چس · باستان‌شناسی stale-.o (کدام TU تعامل مسیر GL را عوض کرده) · مرز draw کامپوزِ dooz (ops=0 در مسیر نرم‌افزاری).
