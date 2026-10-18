# CONT-99 RESULT — T1 «View measurement and layout contract» بسته شد (F-NEW-402..406) · ۲۱/۲۱ ردیف probe · صفر drift

**Wave:** CONT-99 · **HEAD:** `0b851125` → `3efe8315` (== origin/main، push تأیید شد) · **binary:** `e51d7a643e6817ba` → `4dd92ae1371569e4` · **registry:** 713 → **718** روت (sha16 `600f11af279e77aa`)

---

## ۰. گام صفر — پیشنهادی خودم (فریز بیس‌لاین + بازبینی کامل #364)

- housekeeping صادقانه: HEAD محلی یک کامیت پسماند با پیام UUID بود (`9d6faf2b`، فقط build intermediates در tmp/، push نشده) — با `reset --hard` حذف شد؛ `HEAD == origin/main == 0b851125` بازستانده شد؛ goldens 4/4 + selftests 13/13 در کانتینر بازتأیید شدند.
- **#364 کامل خوانده شد (۶۳ کامنت): بعد از ledger CONT-98 یعنی `6249783652` هیچ درخواست جدیدی نیامده** — مجموعه‌ی باز دقیقاً همان §4 ledger قبلی است: CONT-99 (۰/۱۰)، CONT-98 (۹ ترک باقی)، CONT-89/92/93، F-NEW-381.
- از میان آن‌ها بالاترین-اطمینان‌ترین ترک P0 به‌عنوان «پیشنهادی خودم» انتخاب و به‌صورت **یک تسک مجزا** اجرا شد: **CONT-99 T1 — View measurement and layout contract** (مستقیم به چهره‌ی `295x150` تلگرام و خانواده‌ی «دو ستون» گره خورده است).

## ۱. CONT-99 T1 — قرارداد measure/layout برنامه‌نویسی‌شده → **تایید (ROOT-CAUSED-FIXED، F-NEW-402..406)**

**fixture-first:** probe واقعی `fixtures/cont99_lay_probe` (aapt2/ECJ/D8؛ `c99lay.apk` sha16 `80e9399319060b70`، V2-C99LAY، ۲۱ ردیف قطعی در ۳ فاز) **قبل از** هر تغییر موتور ساخته شد. درخت: bar با padding + دو chip با margin · ردیف وزن‌دار مختلط (0px+weight ×۳ + match_parent بدون weight) · FrameLayout با padding + فرزند gravity-ctor + برگ با container-gravity · ردیف وزن تمیز 1:3 · دکمه/تصویر/mpChild/wrapTv · PHASE1 قبل-از-layout (قانون S103) / PHASE2 تثبیت‌شده / PHASE3 بعد از requestLayout.

| فاز | نتیجه |
|---|---|
| **PRE** روی باینری منجمد `e51d7a643e6817ba` | margin+padding گم شده (chip1 `(0,0)` به‌جای `(30,20)`؛ chip2 `(50,0)` به‌جای `(100,20)`)؛ فرزند gravity-ctor در گوشه‌ی بالا-چپ (inner `(0,250)` به‌جای `(480,310)`)؛ فرزندان 0px+weight فرو ریخته — **LPTRACE**: فیلد weight بیت‌های INT32 یعنی `0x3F800000` را داشت که به‌صورت مقداری `1.06535e9` خوانده می‌شد |
| **POST** روی `4dd92ae1371569e4` | **۲۱/۲۱ ردیف OK (۱۰۰٪)** — margin/padding دقیق؛ inner `(480,310,120,80)` وسط‌چین؛ برگ `(520,330,40,40)`؛ سهم وزن دقیق AOSP یعنی `colE=(0,450,270,150)` و `colF=(270,450,810,150)`؛ ردیف مختلط عین قانون AOSP؛ `btn-P3=(0,600,300,80)` — زنجیره‌ی requestLayout→traversal کار می‌کند |

**پنج ریشه‌ی عمومی (همه با ارجاع AOSP):**

| Root | قانون شکسته | مرجع AOSP | فیکس |
|---|---|---|---|
| **F-NEW-402** | `View.setPadding/setPaddingRelative` اصلاً پیاده نشده بود (stub عمومی بی‌صدا) — هر کانتینرِ pad شده فرزندان را از مبدأ خام می‌چید؛ getters هم غایب بودند | View.java padding law | `android_shadows.cpp`: ست چهار فیلد padding + layout_dirty؛ ۶ getter پاسخ از node زنده |
| **F-NEW-403** | قانون «وضعیت زنده‌ی LayoutParams»: store مستقیم فیلد عمومی بعد از addView (`lp.leftMargin = ..`) برای همه‌ی passها نامرئی بود — enrich فقط در زمان attach مقدارها را sync می‌کرد و **identity را گم می‌کرد** (getLayoutParams یک شیء نو می‌ساخت) | ViewGroup: layout هر pass از mLayoutParams زنده می‌خواند | ثبت identity روی node + refresh ورود-traversal برای اشیای LP مهرشده (`lp_bridge`)؛ LPهای مسیر XML (F-NEW-309) عمداً مهر نمی‌خورند |
| **F-NEW-404** | ctor سه‌پارامتری `(w, h, gravity)` آرگومان gravity را می‌انداخت (قرارداد receiver-first یعنی argc=4 و کد قدیم هیچ اسلاتی نداشت) → هر فرزند FrameLayout با gravity-ctor بالا-چپ | FrameLayout.LayoutParams L2417 | شاخه‌ی argc==4 با tail INT32 → فیلد gravity؛ dispatch بر اساس **نوع آرگ** نه شمارش |
| **F-NEW-405** | `MarginLayoutParams.setMargins(l,t,r,b)` no-op بی‌صدا | MarginLayoutParams.java | پل کامل: ۴ فیلد heap + مهر + sync معکوس از طریق identity فاز ۴۰۳ |
| **F-NEW-406** | **سرخط موج:** قانون بیت-ثبتِ رجیستر شناور DEX در iput — `const/high16 v0, 0x3f800000` خودِ `1.0f` است؛ store خام فیلد F را به‌صورت INT32ِ-بیت‌ها می‌گذاشت و هر خواننده‌ی float مقدار بیت‌ها را می‌دید (`1.06535e9`) → children وزن‌دار فرو می‌ریختند | معناشناسی رجیستر DEX (بیت‌ها، بدون تبدیل) | `execute_iput`: فیلد F با رجیستر INT32 → **BIT-CAST** به FLOAT32؛ قانون متقارن D+INT64→FLOAT64 |

## ۲. رگرسیون — صفر drift

wall **۱۲/۱۲ MATCH بایت‌برابر** (dooz `31ddd4d5b8e6d18e` · opencalc `f25b754c4565c38b` · unote `90a67cc1ddda57b7` · microtimer `bbd350b6c14fbd52` — هرکدام ×۳) · goldens **۴/۴** · negatives **۱۹/۱۹** · reinstall **۵/۵ identity ALL PASS** · MG-310 **۷/۷** · MG-150 **۳/۳** · selftests **۱۳/۱۳** · F-NEW-376 **۷۰/۷۰** · انکرها: sax1 **PASS 6/6**، clock1، clinit1 قانون‌درست، swipe1، c74esc containment OK، perf1 **جمع‌ها بایت‌برابر A/B** (3688000/31744000/14534196240/14569628240).

**نکات صادقانه:** (۱) انتظارات colA..colD در fixture نسخه‌ی ۱ **خطای فیکسچر** بود نه خطای موتور — در AOSP فرزند match_parent بدون weight کل ردیف را می‌بلعد و سهم وزنی‌ها صفر می‌شود؛ موتور عین قانون AOSP بود و fixture تصحیح شد. (۲) PHASE1 (Handler.post از onCreate) قبل از اولین traversal اجرا می‌شود — صفرهای آن معنای «قبل-از-layout» است (S103)، نه divergence. (۳) reinstall موقتاً ۵ FAIL شد: apks‌های `hidden_sources` در کانتینر گذرا بودند — از منابع canonical بازپر و identity shaها در خطوط PASS ثابت شد (همان کلاس تعمیرِ ثبت‌شده در CONT-98). (۴) ردیف‌های stdout انکرها (sax1/clinit1/swipe1/perf1) با rerun مستقیمCapture شد — شکاف ارثی اسکریپت باتری از CONT-98 همان‌جا flagged بود. (۵) روی sput (فیلد استاتیک float) residual نام‌گذاری شد (امروز caller در corpus ندارد). (۶) draft اول F-NEW-404 قرارداد argc را اشتباه خواند — با ردیف‌های POST2 صید و قبل از POST نهایی اصلاح شد؛ آن باینری میانی هرگز برای ادعای evidence استفاده نشد.

## ۳. مجموعه‌ی دقیق باز (ادامه در موج بعدی، هر مورد یک تسک مجزا)

1. **CONT-99** T2..T10 — transforms/density/insets، ImageView scaleType، button hitbox، text/z-order/clip، scroll geometry، white-forensic، frame integrity — **۱/۱۰ انجام شد (T1)**.
2. **CONT-98** T1/T2/T3/T4/T5/T7/T8/T9/T10.
3. **CONT-89** نردبان ۷-صفحه‌ای تلگرام · **CONT-92** addendum منبع‌محور · **CONT-93** ماتریس ده-بازی · **CONT-91** معطل artifact.
4. **F-NEW-381** opcode-core throughput — سرخط P0 مشترک (چهره‌های 295x150 و دیوار SVG تلگرام).

**نرخ موفقیت این موج:** ۱ تسک مجزا اجرا شد (CONT-99 T1)، ۱ APPROVED با ۲۱/۲۱ ردیف + باتری صفر-drift = **۱۰۰٪ از تلاش‌شده‌ها**. شمارش کل directiveها بر اساس ledger قبلی ثابت می‌ماند (۱۹ بسته‌ی کامل از ۲۷ = ۷۰.۴٪؛ با partial نصفه = ۷۵.۹٪) — CONT-99 اکنون «بخشی-بسته» است.

**Evidence:** `evidence/cont99/evidence.json` · probe `fixtures/cont99_lay_probe` (V2-C99LAY، `80e9399319060b70`) · commits `f9fc8921` + `38b9d869` + `3efe8315` · binary `4dd92ae1371569e4` · registry **718** روت.
