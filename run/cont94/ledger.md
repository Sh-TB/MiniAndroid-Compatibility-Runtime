# CONT-94 RESULT — #364: تلگرام الویت اول اجرا شد · ریشه‌ی هویت فعالیت (F-NEW-396) رفع شد · اولین پیکسل‌های واقعی UI تلگرام/فورکگرام

**Wave:** CONT-94 · **directive کاربر:** «ادامه تلگرام رو الویت اول اجرا بزار ۳۶۴ تموم بشه» (اجرا CONT-88 فاز ۱ + CONT-89 + CONT-92 درون #364) · **HEAD:** `9d313976` (روی `a2f2255b` = CONT-87 closeout) · **binary:** قبل `caa24290aad77ca9` → بعد `7cf6fe7f3d6abb81` · **registry:** 703 روت، sha16 `70a7f20478b1af40`

---

## ۰. درخواست‌های #364 (استخراج کامل — طبق دستور: استخراج → لیست → نمایش → اجرا)

| # | کامنت | عنوان | وضعیت |
|---|-------|-------|-------|
| 1 | 6245430786 | **CONT-87** — ده فیکس execution-first | ترک ۱ بسته شد (CONT-87)؛ ترک‌های ۲..۱۰ باز |
| 2 | 6245477077 | **CONT-88** — REAL APP EXECUTION (تلگرام end-to-end؛ WhatsApp-family؛ ≥۴ فیکس؛ ≥۸ APK) | **این موج: فاز ۱ + T1/T2 شروع شد (F-NEW-396)** — بقیه باز |
| 3 | 6245481160 | **CONT-89** — TELEGRAM UI FORENSIC (نردبان ۷ صفحه) | صفحه ۱ (login/phone) اکنون پیکسل واقعی دارد؛ صفحات ۲..۷ باز |
| 4 | 6245481420 | **CONT-90** — WHITE GAME/APP RECOVERY (۵+۵) | باز |
| 5 | 6245481662 | **CONT-91** — WHATSAPP PARITY (اول حکم آرتیفکت) | **حکم آرتیفکت همین موج صادر شد: NOT_AVAILABLE** (upload/whatsapp.apk = فایل ۵,۶۱۵ بایتی stub، sha16 `c473ad25086720a8`)؛ کنترل cross-family = فورکگرام/تلگرام/Signal(وقتی آرتیفکت باشد) |
| 6 | 6245501827 | **CONT-92** — TELEGRAM SOURCE-GROUNDED ADDENDUM | لینک‌های upstream ثبت شد؛ نقشه source→runtime باز |
| 7 | 6245531086 | **CONT-93** — TEN-GAME MATRIX (حرکت/3D/strategy/farm) | باز — پس از ترک ۲ CONT-87 (GLSL) یا BLOCKED صادقانه |

## ۱. هویت دقیق APK (badging واقعی، نه فرض)

- **تلگرام رسمی:** `upload/telegram_official.apk` = `org.telegram.messenger.web` **12.10.5** vc71059، sha16 `e37aced2a49c1dbb`
- **فورکگرام:** `upload/forkgram_709208.apk` = `org.forkgram.classic` **12.10.8.0** vc709208، sha16 `3baeecb3288577e9`
- **واتساپ:** `upload/whatsapp.apk` فقط **۵,۶۱۵ بایت** است — آرتیفکت واقعی نیست؛ حکم: **NOT_AVAILABLE** (هیچ APK جعلی‌ای ساخته نشد؛ هیچ ادعای دسترسی به سورس خصوصی نشد)

## ۲. اجرای تلگرام در HEAD فعلی — کشف ریشه

اجرا (`run/cont94/tg_official_1`): LaunchActivity → RESUMED، درخت view عمیق `org/telegram/ui` — اما framebuffer فقط **۱۸۸/۲,۰۷۳,۶۰۰ پیکسل غیرسفید** (رندر نیست — صادقانه). ۳۱ استثنای uncaught؛ زنجیره‌ی NPE در `ActionBar/s2.checkSystemBarColors` و `onBecomeFullyVisible` ×۳.

**decode واقعی** (androguard؛ `scripts/cont94_decode_*.py`):
- `s2.checkSystemBarColors`: `getParentActivity()` → `instanceof LaunchActivity` → check-cast → `H(Z Z Z)V`
- `LaunchActivity.H` فیلد `p0` را می‌خواند و `ActionBarLayout.w()` را روی آن صدا می‌زند
- `z0(I)V`: `iget y0` → `e4.setInternalNavigationBarColor`

**پروب‌های موتور** (`MINIANDROID_F141_DIAG` + پروب جدید `[C94-SINGLETON]`):
- گیرنده‌ی invoke در H برابر **NULL** بود؛ `this` برابر **obj#7307**
- `[C94-SINGLETON] MISS 'Lorg/telegram/ui/LaunchActivity;' (no cache entry) → allocated obj#7307`
- `[U0113-ACTIVITY] activity heap object #694` — فعالیت واقعی که onCreate را اجرا کرد
- `[R414-INIT-DEFAULT]` ثابت کرد حتی state اولیه‌ی فیلدها روی #7307 غایب بود

## ۳. ریشه (F-NEW-396) — تایید با شواهد

**مسیر launch DEX-0 فعالیت واقعی را می‌سازد (`#694`) اما هرگز `api_singletons_[cls.name]` را ذخیره نمی‌کرد** (فقط مسیرهای multi-DEX و legacy-scan ذخیره می‌کردند). سه سایت intercept والدِ `getParentActivity()` همه با `get_or_create_singleton("Lorg/telegram/ui/LaunchActivity;")` پاسخ می‌دادند — cache MISS → **ساخت یک شیء تازه‌ی مقدار-اولیه-نشده از کلاس هاردکد** (کلاس درست، نمونه غلط). `instanceof` اپ رد می‌شد؟ نه — رد می‌گذشت! سپس `H(Z Z Z)V` روی شیء خالی اجرا شد → `p0`=null → `ActionBarLayout.w()` روی گیرنده null → NPE ×۳ → سه APP-BOUNDARY unwind → ساخت UI لاگین کشته شد → قاب سفید.

## ۴. فیکس — عمومی، ۴ سایت، بدون هیچ شرط package

1. **قانون هویت**: مسیر launch DEX-0 حالا `api_singletons_[cls.name]` را ذخیره می‌کند (همان قانون دو مسیر دیگر) — ردیف `[C94-SINGLETON] LAUNCH-STORE`
2. **قانون والد زنده**: intercept اصلی `getParentActivity` اکنون فعالیت زنده را از `ActivityShadow::current_activity_id()` برمی‌گرداند (کلاس از heap حل می‌شود)؛ پنجره‌ی قبل-از-اتچ = null (قرارداد AOSP)
3. + 4. دو قلوی bridge و shadow-dispatch: همان قانون

**residual نام‌گذاری‌شده (صداقت):** اتصال آرایه‌ی `doneButtonVisible[0..9]` روی گیرنده یک پچ APP-SPECIFIC از era EXP-071 است (اسم فیلد هاردکد تلگرام) — این موج دست‌نخورده ماند تا رفتار ثبت‌شده‌ی flow لاگین حفظ شود؛ عمومی‌سازی fixture-first به‌عنوان follow-up ثبت شد.

## ۵. اثبات — fixture + دو APK واقعی

### fixture `com.probe.c94p` (sha16 `a90f3d0eaf113ed0`)
| ردیف | قبل (`caa24290aad77ca9`) | بعد (`7cf6fe7f3d6abb81`) |
|---|---|---|
| C94-PROBE | `identity=OTHER-SAME-CLASS marker=null` ❌ | `identity=THIS marker=C94-MARKER-V1` ✅ |

### APK واقعی
| هدف | قبل | بعد |
|---|---|---|
| تلگرام رسمی | ۱۸۸ px؛ ۳۱ uncaught؛ ۳× NPE؛ ۳× APP-BOUNDARY | **۹,۳۴۰ px واقعی** (باکس «+» کد کشور، حاشیه فیلد شماره، متن آکسنت)؛ ۱۵ uncaught (مرزهای boot-init صورت‌حساب/نیتیو/فایربیس)؛ ۰ ردیف f141؛ ۰ unwind |
| فورکگرام | ۱۸۸ px | **۱۵,۵۹۹ px واقعی** («Your Number»، فیلد شماره، QRLoginButton)؛ ۵ uncaught |

## ۶. رگرسیون — صفر drift روی باینری نهایی `7cf6fe7f3d6abb81`

**wall 12/12** (بایت‌برابر) · **goldens 4/4** (`helloworld` کانونی `83720c1028f832d0`) · **negatives 19/19** · **reinstall 8/8** · **MG-310 7/7** · **MG-150 3/3** · **c72priv ۱۳ ردیف 0-BAD** · **selftests 13/13** · **F-NEW-376 70/70** · فنس c74esc همه OK · clock1 OK · swipe1 قانون‌درست (dx=-16/dy=+25، vx=+1055.77/vy=-1562.49؛ residual e2 نام‌برده و تغییری‌نکرده) · **as2048_47: 0 uncaught**

## ۷. لیست کاری بزرگ — به‌روز CONT-94 (باقی‌مانده‌ها اول)

| # | مورد | حکم | تایید/رد |
|---|------|-----|---------|
| 1 | **F-NEW-396 هویت فعالیت** | ROOT-CAUSED-FIXED — fixture + ۲ APK + باتری صفر-drift | ✅ تایید |
| 2 | **CONT-91 حکم آرتیفکت واتساپ** | NOT_AVAILABLE (stub ۵,۶۱۵ بایتی) — صادقانه بسته | ✅ تایید (حکم) |
| 3 | تلگرام صفحه ۱ (login/phone) | پیکسل واقعی؛ اما top-anchored (مرز bounds/offset) | ⏳ PARTIAL |
| 4 | تلگرام صفحات ۲..۷ (Next/SMS/Dialogs/Search/Chat/Settings/Back) | باز — نیازمند قانون bounds/offset + RecyclerView | ⏳ باز |
| 5 | CONT-88 T3 (قانون bounds/offset fragment-view) | **فرونتیر بعدی** — محتوا top-anchored رندر می‌شود | ⏳ باز P0 |
| 6 | CONT-88 T4 (RecyclerView/Dialogs list) | باز | ⏳ باز |
| 7 | CONT-88 T6 (رزولوشن string-resource — چهره `[resid:0x...]`) | باز | ⏳ باز |
| 8 | native libs مرز (UnsatisfiedLinkError در ApplicationLoader.onCreate) | باز | ⏳ باز |
| 9 | زنجیره play-billing UOE + FirebaseInitProvider Ll9/j | مرزهای boot-init — تغییری نکرده | ⏳ باز |
| 10 | doneButtonVisible APP-SPECIFIC attach | residual نام‌گذاری‌شده — عمومی‌سازی fixture-first | ⏳ باز (صداقت) |
| 11 | CONT-87 ترک ۲ (GLSL backend) | BLOCKED (project-scale/RAM) | ⏸ باز |
| 12 | CONT-87 ترک ۳ (throughput) | CONFIRMED_NOT_FIXED (پروفایل مسطح) | ❌ رد (باز) |
| 13 | CONT-87 ترک ۴ (Compose first-frame) | CLASSIFIED frontier | ⏳ باز |
| 14 | CONT-87 ترک ۵ (F-145 multi-activity screenshot) | OPEN P1 | ⏳ باز |
| 15 | CONT-87 ترک ۶..۱۰ (z-order/logs-as-data/Canvas diag/AndroidGraphics/swipe e2 ۶-float) | باز-شرطی/نام‌برده | ⏳ باز |
| 16 | CONT-90 (۵ اپ سفید + ۵ هدف) | باز — نردبان first-divergence | ⏳ باز |
| 17 | CONT-93 (ماتریس ۱۰ بازی) | باز — پس از GLSL یا BLOCKED صادقانه | ⏳ باز |
| 18 | attribution فریم EXC-PROPAGATE (invoke_pc=751/994/1011 به‌جای سایت واقعی 1988) | نویز bookkeeping فریم موتور — ثبت شد، این موج دوباره-صفت نشد | ⏳ باز (P2) |

## ۸. پرسنتاژ

- **این موج: ۲ حکم نهایی تایید (فیکس F-NEW-396 + حکم آرتیفکت واتساپ) + ۱ PARTIAL صادقانه (صفحه ۱ تلگرام) از ۳ قلم پردازش‌شده — ۶۶٪ تایید کامل، ۳۳٪ پیشرفت واقعی partial.**
- **رگرسیون: ۱۳/۱۳ گیت سبز، صفر drift — ۱۰۰٪.**
- **جهش UI: تلگرام ۱۸۸ → ۹,۳۴۰ پیکسل واقعی (×۴۹.۷)؛ فورکگرام ۱۸۸ → ۱۵,۵۹۹ (×۸۲.۹) — اولین پیکسل‌های app-owned در HEAD فعلی.**

fixtures: `fixtures/cont94_parent_probe` (com.probe.c94p) · scripts: `cont94_build_probe.sh`، `cont94_decode_launch.py`، `cont94_decode_h.py`، `cont94_decode_z0.py`، `cont94_decode_s2.py`، `cont94_find_h_callers.py`، `cont94_registry_update.py`، `cont94_app_registry_update.py` · evidence: `evidence/cont94/` (evidence.json + MANIFEST + ۵ چهره + mosaic) + `run/cont94/`
