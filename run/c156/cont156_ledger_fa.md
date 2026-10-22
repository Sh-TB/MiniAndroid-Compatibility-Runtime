# CONT-156 — «ادامه ۱۰ قطار ۵۰ واگن» — ۳ اصلاح موتوری جدید + ۱۲ عبور جدید + صفر واپس‌رفتگی

**پایه:** HEAD `e5ca5772` (CONT-155 TRAIN 10)، بازسازی قطعی #۱۰ = `d7d3d61a` بایت-یکسان.
**پایان:** رجیستری **۸۰۷** (id-unique، main==mirror). دیوار ۹/۹ MATCH + negatives **۱۹/۱۹** + selftest **۱۳/۱۳** در **همه‌ی** باینری‌های میانی (`2dc7f5b4` → `9a36acf0` → `dd2622762` → `c7092cab`).

## قطار ۱ — سرشماری اهرم F-NEW-481 (کوهورت ۴۹-اپ APP_DRAW_OPS)
- ابزار جدید xref: دارنده‌ی typed = `Lpz0;.N : Loz0;` — **تنها یک سایت نوشتن** (`pz0.<init> pc=64`)؛ `Loz0;.g` ارجاع برگشتی؛ `pz0.r1` هر بار Loz0; تازه می‌سازد.
- سرشماری زنده (dooz v23، ۵ فریم): dispatchDraw=۶، el0.i=۶، pz0.<init>=**۴۱** (۲ زودهنگام + ۳۹ دیرهنگام)، r1=**۲** (فقط از xk0.k0/ug0.k0)، em1.g/ff.g/sc0.g=**۰** (کال‌بک‌های لایه هرگز)، gl0.c=**۰** (رسم محتوای واقعی هرگز)، مسیر RenderNode فریم‌ورک **بلااستفاده** (beginRecording=0)، rh1.a=۰ (تریگر رکورد مرده در بالادست).
- **ردِ صادقانه:** فرضیه‌ی قحطی frame-pump رد شد — Choreographer سالم است (`Lh9;.doFrame` هر فریم می‌آید). قانون `kz0.d` در این بیلد مرده است (گیرنده‌ی ریشه = `kz0.c` با ۲۰۱ اجرا).

## قطار ۲ — **F-NEW-486 ROOT-CAUSED-FIXED** (خانواده‌ی سایه‌ی WindowMetrics)
- ریشه: `getCurrentWindowMetrics` (API 30) سایه نداشت → null → checkNotNull NPE در `updateMeasurementSDK30` (aat، F-NEW-485).
- fix: getCurrentWindowMetrics/getMaximumWindowMetrics → singleton WindowMetrics با mBounds=Rect(0,0,1080,1920) (قانون پروفایل دستگاه) + mWindowInsets=Insets(0,0,0,0)؛ getBounds/getWindowInsets هرگز null (قانون AOSP).
- **نتیجه:** aat ‏۰٪→**۹۹.۳٪** non-white — امضای قاتل غایب. WINDOW_ROOT: ‏۹/۱۷→**۱۰/۱۷**.

## قطار ۳ — اندازه‌گیری مجدد کوهورت WINDOW_ROOT (۱۷ اپ)
- **۱۲/۱۷ رند** (معیار face ≥۵۰٪): عبورهای جدید aat + librecontactsbackup (۷۴.۱٪)؛ شش عبور CONT-155 دوباره تأیید شد (۹۹.۴٪).
- ۵ blank باقی — هر پنج با دیکد پین‌شده CLASSIFIED شدند (قطار ۷).

## قطار ۴ — **F-NEW-487 ROOT-CAUSED-FIXED** (fallback مرده‌ی filled-new-array)
- ریشه: fallback حل type در filled-new-array یک **استاب مرده** بود → آرایه با class_descriptor لیترال `<unknown>` تخصیص می‌یافت → store-check (R-NEW-010) هر ذخیره‌ی typed را رد می‌کرد → **ArrayStoreException کاذب** در `Utils.<clinit>` گوست‌اسکویر (String[][]) → آبشار NoClassDefFoundError.
- fix: fallback از dex_report_ types + گارد `<unknown>` در asc_src_known.
- **نتیجه:** ghostsq commander ‏۰٪→**۹۹.۴٪** — ArrayStoreException و آبشار هر دو غایب.

## قطار ۵ — **F-NEW-488 ROOT-CAUSED-FIXED** (PackageManager.getApplicationInfo)
- ریشه: واریانت PackageManager سایه نداشت (REC-MISS → null) → NPE روی `.metaData` (ricochlime pc=16).
- fix: singleton ApplicationInfo + Bundle metaData + **NameNotFoundException صادقانه** برای پکیج بیگانه (قرارداد AOSP).
- **نتیجه:** قاتل metaData غایب؛ ricochlime بعدش مرز بعدی خودش را نشان داد: **FLUTTER-BOUNDARY** (نیاز به Dart VM — F-NEW-489).

## قطار ۶ — باتری مجدد fdroid (۹۴ اپ، تازه، باینری نهایی)
- رندر واقعی (≥۵۰٪): **۸۵/۹۴** (از ۷۳/۹۴ در c154) — **۱۲ عبور جدید، صفر واپس‌رفتگی**.
- scorecard کامل در `run/c156/big/scorecard.json` (face% + rc + شمار استثنا برای هر اپ).

## قطار ۷ — باتری مجدد ۲۲ کانونیکال + رجیستری ۸۰۷
- ‏۱۷/۲۱ non-white>۱٪ (klondike/stopwatch = face مرزی پایدار بایت-یکسان با لنگر؛ forkgram/telegram = مرز UPP-001؛ whatsapp = آرتیفکت خراب).
- CLASSIFIED صادقانه: F-NEW-489 (فلاتر)، F-NEW-490 (خانواده‌ی silent-null سازنده)، F-NEW-491 (vararg-null کواین)، F-NEW-492 (attach ok=false)، F-NEW-493 (مرز IPC شیزوکو).

## قطار ۸ — سرشماری F-NEW-490 (دو شکاف dispatch نام‌گذاری شد)
- MINIANDROID_F490_DIAG (فقط-خواندنی): **صفر** [F490-NULL] — فراخوانی Constructor.newInstance هرگز به handler پل نمی‌رسد، درحالی‌که getConstructor **همان کلاس** پل می‌شود ([F106-CTOR] اثبات).
- **شکاف A:** execute_invoke_virtual فراخوانی newInstance را قبل از پل گم می‌کند. **شکاف B (جدید):** invoke-direct گارد null-this ندارد (f141 فقط در invoke-virtual است) — بدنه‌ی ctor با this=null اجرا می‌شود؛ AOSP در **سایت فراخوانی** پرتاب می‌کند تا catch فراخوان کار کند.

## واگن‌شمار صادقانه
۴۰ واگن مقدماتی (۵×۸ قطار) + ۱۰ واگن بستن (ورک‌لاگ، ledger، دیوار نهایی، push، راستی‌آزمایی HEAD==origin/main، توازن رجیستری، تقطیع census، شواهد باتری، بهداشت کامیت، جمع‌بندی) = **۵۰/۵۰**.

## گام بعدی (تک‌سؤال)
شکاف A/B سازنده‌ی بازتابی (F-NEW-490) → پاسخ‌دادن invoke-direct به گارد null-this + رساندن newInstance به پل؛ سپس کواین vararg (F-NEW-491) و census اهرم F-NEW-481 (walk زنجیره‌های دیرهنگام).
