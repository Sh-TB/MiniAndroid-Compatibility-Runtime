# CONT-104 RESULT — حالت دسته‌ای: ۱۴ واحد کاری در یک چرخه · خانوادهٔ NPE چس (۴ منبع null) ریشه‌یابی-و-رفع شد · ۵ ریشهٔ جدید ثبت شد · باتری کامل بدون هیچ دریفت

**Wave:** CONT-104 · **HEAD:** `dd5118cccc6e7f56` (باینری نهایی) · **Registry:** 752 → **757** roots (F-NEW-442..442e) · **Evidence:** `evidence/cont104/evidence.json`

## پیش از اجرا — بازخوانی #364 و بازیابی کانتینر
۶۹ کامنت خوانده شد؛ جدیدترین کامنت = گزارش CONT-103 خود ما (۶۲۵۴۷۴۱۹۲۹) — **هیچ کارت جدیدی از کاربر بعد از آن نیامده**. مأموریت این موج: دستور دائمی (ادامه + حالت دسته‌ای ≥۱۰-۱۵ واحد) + لیست تحویل CONT-103.

**کشف مهم:** کپی محلی ریپو یک snapshot قدیمی (دورهٔ CONT-10) بود؛ با fast-forward به `99ffb45c` همگام شد و بازسازی قطعی باینری، `2bb822526e7588a5` را بایت‌یکسان بازتولید کرد — ورود بدون دریفت.

## اجرای دسته‌ای (۱۴ واحد — هر آیتم با وضعیت پایانی)

| # | واحد | وضعیت | نتیجه |
|---|------|--------|--------|
| U1 | بازیابی کانتینر + بازسازی قطعی باینری | ✅ تایید | HEAD == origin/main؛ باینری ورود بایت‌یکسان |
| U2 | تلگرام PRE در HEAD جدید | ✅ تایید | کسکد کامل: `n2.r pc=692 aget-oob (length=11; index=11)` ×۱ + F084 ×۵۳۱ + `o6;.k` iput-null ×۱ (چهرهٔ جدید کوچک) + UnsatisfiedLinkError ×۱ — ۱۲۱۸۲ خط stderr |
| U3 | دیکد aget-oob ن2.r (play_billing) | 🔎 **GAP تأییدشده** | کلاس = سازندهٔ MessageSchema در protobuf-lite؛ دیکد دقیق androguard: OOB در `aget-object` بایت `0x568` (پیمایش نام‌ها → n2.B → getDeclaredField → Unsafe.objectFieldOffset zze..zzj + zzn=144)؛ ناسازگاری طول-آرایه/کران در ساخت s2 — نیازمند پروب fixture-first تجزیهٔ compact-info (موج بعد؛ بدون fixture هیچ fixی زده نشد) |
| U4 | دیکد و رفع NPE چس (start;.onCreate pc=9) | ✅ **تایید — ۵ ریشهٔ جدید** | خانوادهٔ `Ln0/k1;.c` (WindowInsetsCompat.toWindowInsetsCompat با requireNonNull درون‌خطی‌شدهٔ R8) **۴ منبع null** داشت که یکی‌یکی با CL-TRACE دیکد شد: `getRootWindowInsets` (**F-NEW-442**)، `computeSystemWindowInsets` (**F-NEW-442b**)، `WindowInsets.inset(IIII)` (**F-NEW-442d**، از طریق delegate منتقل‌شدهٔ R8 به androidx/lifecycle/c0;j)، `dispatchApplyWindowInsets` (**F-NEW-442e**) + `Rect.isEmpty` بی‌پیاده‌سازی (**F-NEW-442c**). شمارندهٔ f141: **۸ → ۰**؛ چس حالا اسکلت منوی appcompat+Material را بوت می‌کند |
| U5 | پروب fixture-first + سوییچ انکرها | ✅ تایید | `fixtures/cont104_insets_probe` (aapt2/ECJ/D8 واقعی): PRE روی باینری منجمد `[ATTACHED nonnull=false]` → POST **۴/۴ سبز**؛ c74esc احتوای ۵/۵؛ c103a سبز؛ clinit1 قانون F-NEW-215 شلیک می‌شود؛ swipe1 GCB-E2 تایید؛ sax1 ساکت (آرتیفکت pacing شناخته‌شده — null صادقانه) |
| U6 | باتری کامل رگرسیون | ✅ تایید | **wall 4/4 بایت‌یکسان ×۳** (dooz `31ddd4d5b8e6d18e` / opencalc `f25b754c4565c38b` / unote `90a67cc1ddda57b7` / microtimer `bbd350b6c14fbd52`) · goldens **4/4** · negatives **19/19** · reinstall identity **5/5** · MG-310 **7/7** · MG-150 **3/3** · selftests **13/13** · F-NEW-376 **70/70** |
| U7 | UPP-001 (مرز اجرای native) | ⛔ مسدود | تغییری نکرده: dlopen واقعی → dlerror واقعی (وابستگی libjnigraphics)؛ forkgram arm64 رد واقعی |
| U8 | CONT-89/92 (تلگرام UI) | ⚠️ تایید نسبی | سه خانوادهٔ CONT-103 در باینری جدید هم بسته می‌مانند؛ باقیمانده: F084 pacing + n2.r + NDK |
| U9 | CONT-90 (سوییچ سفیدها) در HEAD جدید | ✅ تایید | flappy ۹۵٪ · sudoku ۹۹.۸٪ · chessclock ۹۷٪ · notes کامل · klondike سفید (WebView — بی‌تغییر) · چس **پیشرفت کرد** (f141 ۸→۰). **بدون هیچ رگرسیون**؛ مشاهدهٔ جدید غیرکشنده: SVCINFO-miss برای AppLocalesMetadataHolderService (شکاف merge مانیفست کتابخانه‌ای) در sudoku/notes |
| U10 | CONT-93 (ماتریس کورپوس) | ✅ تایید | همهٔ REAL_APP_CONTENT ثبت‌شده حفظ شد (بایت‌یکسان یا درصدی) |
| U11 | registry + mirror | ✅ تایید | 752 → **757**، id-unique |
| U12 | evidence + worklog | ✅ تایید | `evidence/cont104/evidence.json` + worklog |
| U13 | کامنت نتیجه در #364 | ✅ تایید | همین کامنت |
| U14 | push + HEAD == origin/main | ✅ تایید | پایین را ببینید |

## نتیجهٔ کلیدی موج — خانوادهٔ چهارگانهٔ null در مسیر WindowInsets چس
یک NPE، چهار منبع: مسیر `k1.c` در appcompat از **چهار API پلتفرمی** تغذیه می‌شد که هر چهار با stub بی‌صدا null برمی‌گرداند. هر منبع با CL-TRACE زنده جدا شد، با پروب fixture-first قبل از فیکس ثبت شد، و با قانون AOSP دقیق رفع شد. این همان الگوی «یک چهرهٔ مرگ = یک خانوادهٔ ریشه» است که در CONT-96..103 تثبیت شد.

## یادداشت‌های صداقت
- چس **کامل بسته نشده**: خانوادهٔ NPE (۸→۰) یک پیشرفت واقعی به اسکلت منوی Material است، ولی RecyclerView منو هنوز ۰ فرزند دارد (مسیر دادهٔ adapter) و یک NotFound گرفته‌شده (id=-1) باقی است — صادقانه در evidence ثبت شد.
- `n2.r aget-oob` = **GAP تأییدشده**؛ دیکد عمیق (سازندهٔ schema با compact-string) ثبت شد ولی بدون پروب fixture-first هیچ fixی زده نشد — طبق پروتکل.
- gates نیاز به تعمیرهای مستند «کانتینر تازه» داشتند (بازسازی probe + نصب + اجرا، بازگردانی hidden_sources از canonical) — آرتیفکت ترتیب بود، نه دریفت؛ بعد از تعمیر همه سبز.
- تلگرام در گیت ۳۰ ثانیه هنوز به فریم نمی‌رسد (startup محاسبات‌BOUND)؛ هیچ میان‌بر app-specific زده نشد.

## نرخ موفقیت
- **۱۴/۱۴ واحد به وضعیت پایانی رسیدند** (تایید/تایید نسبی/GAP/مسدود)
- **۱۱/۱۴ کاملاً بسته** (۷۹٪) · وزن‌دار ≈ **۸۶٪**

## باتری — صفر دریفت در `dd5118cccc6e7f56`
wall **4/4** بایت‌یکسان ×۳ · goldens **4/4** · negatives **19/19** · reinstall **5/5** · MG-310 **7/7** · MG-150 **3/3** · selftests **13/13** · F-NEW-376 **70/70** · پروب c104i **4/4**

## مالکیت موج بعد
پروب تجزیهٔ compact-info (n2.r) · مسیر دادهٔ adapter منوی چس + id=-1 · شکاف merge مانیفست کتابخانه‌ای (AppLocales) · چهرهٔ `o6;.k xj0;.Y` تلگرام · قانون بودجهٔ F084.
