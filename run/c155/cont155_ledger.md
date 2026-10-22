# CONT-155 — «ادامه ۱۰ قطار» — دو ریشه‌ی موتوری جدید، ۹ از ۱۷ اپ WINDOW_ROOT رند شد

**پایه:** HEAD `f41e2ac5` (CONT-154 TRAIN 2)، باینری f6b272ea (بازسازی قطعی #9)، رجیستری 795.
**پایان:** HEAD `e1ac5e7e`، باینری `d7d3d61a`، رجیستری **799** (id-unique، main==mirror).
**۱۰/۱۰ قطار push شد؛ HEAD==origin/main بعد از هرکدام تأیید شد.**

## دیوار صفر-انحراف
- شروع: بازسازی قطعی #9 = f6b272ea بایت-یکسان؛ دیوار ۹/۹ لنگر MATCH.
- بعد از هر تغییر موتوری: دیوار کامل. دو لنگر با **اصلاح واقعی محتوا** re-base شدند (زیر).
- پایان: دیوار ۹/۹ MATCH + negatives **۱۹/۱۹** + skill selftest **۱۳/۱۳**.

## قطار ۱-۲ — نقشه‌ی کامل ورودی رسم dooz (F-NEW-481)
- کل-dex سرشماری با ابزار جدید `cont155_methxref.py` (۴ قانون walker اصلاح شد): ‏`Lel0;.i` **دقیقاً ۲ caller** دارد: `Lt4;.dispatchDraw` (پاس رسم هر-فریم «AndroidOwner:draw» + getRoot هر فریم) و `Lug0;.h1` (overlay).
- **ردِ صادقانه‌ی** قانون «scope snapshot اول»: ریشه هر فریم دوباره خوانده می‌شود؛ حلقه‌ی زنجیره در M0 کامل دیکد شد (T0(4) → gl0.c رسم واقعی → walk زنجیره .j با ماسک .g).
- **قانون نهایی:** مسیر lambda-replay (لایه‌ها → r1 → Loz0; → oz0.a → M0) **هرگز اجرا نمی‌شود** (METHOD-TRACE = ۰ خط) — ۳۹ lambda دیرهنگام با capture درست ساخته شده ولی صفر بار فراخوانی شدند.

## قطار ۳-۴ — WINDOW_ROOT ۱۷ اپ + **F-NEW-482 ROOT-CAUSED-FIXED**
- سرشماری: A=7 onCreate-never-ran، B=2 Koin، C=3 AppCompat theme-gate، D=4 استثناهای نام‌دار.
- **ریشه‌ی A:** مسیر DEX-0 فقط onCreate «همان-کلاس» را می‌جست (SplashActivity فقط `<init>` دارد؛ onCreate ارثی Ll7/h; هرگز اجرا نمی‌شد) → fix: dispatch onCreate ارثی با try_recursive_invoke + wrap کامل AOSP.
- **نتیجه:** flashlight ‏onStart 27→1190 دستور، setContentView فعال، چهره 0%→**۱۰۰٪**؛ **۶/۱۷ اپ حالا رند می‌شوند** (flashlight, subster, voyager, how2vote, fossify-contacts, fossify-filemanager).

## قطار ۵-۸ — **F-NEW-484 ROOT-CAUSED-FIXED** (سه‌گانه‌ی theme-gate)
- زنجیره کامل: manifest اکتیویتی launcher = ‏`Theme.SplashScreen` (بایت-exact)؛ **نقص واقعی:** ‏`Activity.setTheme(int)` در موتور فقط LOG می‌شد — ‏postSplashScreenTheme اسپلش-لایبراری bind نمی‌شد → slot-117 ‏AppCompatTheme_windowActionBar ‏hasValue=false → ISE «Theme.AppCompat» در createSubDecor pc=404.
- **fix:** setTheme handler در ActivityShadow::dispatch + مسیر bridge → ‏`ResourceRuntime::set_activity_theme`.
- **نتیجه:** todolist/leradar/exodusprivacy **هر ۳ رند شدند** (۱۰۰٪ non-white، root واقعی 628) → **مجموع WINDOW_ROOT: ۹/۱۷ رند**.
- دو لنگر با **دلیل** re-base شد: unote ‏90a67cc1→7481e9b4 (اپ setTheme(0x1030128) می‌زند)، opencalc ‏d5f3c7b5→63020bc7 (اپ setTheme(0x7f12013d) می‌زند) — قانون AOSP حالا رعایت می‌شود، پیشرفت REAL_APP_CONTENT (همان دسته‌ی re-base سابقه).

## قطار ۹ — aat دیکد شد (F-NEW-485 CLASSIFIED)
- ‏`WindowManager.getCurrentWindowMetrics` (API 30) سایه ندارد → null → Kotlin ‏checkNotNull «must not be null» در `AppLayout.updateMeasurementSDK30` → NPE. پین ۴-دستوری + stack کامل. اصلاح: خانواده‌ی سایه‌ی WindowManager/WindowMetrics (قطار بعدی).
- اصلاح صادقانه‌ی طبقه‌بندی: launcher اپ aat **دارد** onCreate اعلان می‌کند (A→D).

## رجیستری 795→799
- F-NEW-482 ‏ROOT-CAUSED-FIXED، F-NEW-483 ‏CLASSIFIED (زنجیره‌ی C کامل با یک لینک باز صادقانه)، F-NEW-484 ‏ROOT-CAUSED-FIXED، F-NEW-485 ‏CLASSIFIED. کل: **۲۹۸ ROOT-CAUSED-FIXED** + 155 VERIFIED-CORRECT + 50 VERIFIED-FIXED.

## گام بعدی (تک‌سؤال)
خانواده‌ی سایه‌ی WindowManager/WindowMetrics (F-NEW-485) → aat؛ سپس زوج Koin (B) و سه‌گانه‌ی NPE/ArrayStore (D). مسیر موتوری F-NEW-481 (lambda-replay) برای ۴۹-اپ APP_DRAW_OPS همچنان بزرگ‌ترین اهرم رندر است.
