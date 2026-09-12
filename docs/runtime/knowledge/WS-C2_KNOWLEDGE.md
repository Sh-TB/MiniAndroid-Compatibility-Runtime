# WS-C2 KNOWLEDGE — Graphics / Text / Image / Animation / Audio-Visual

**Unified Coder campaign:** 2026-08-27
**Tested HEAD:** `bbe0ce3` (baseline) → `86bd646` (UC-CM-001, no graphics impact)
**Real APK:** Telegram 12.10.1 (SHA256 `f5e11927…`, versionCode 70389, 5 DEX)

این سند یافته‌های WS-C2 در این کمپین است. یافته‌های قبلی Coder 2/Primary در
`CODER2_KNOWLEDGE.md` و `CODER_MAIN_KNOWLEDGE.md` (CM-018..CM-027) باقی می‌مانند؛
اینجا فقط reconciliation و یافته‌های جدید.

---

## UC2-001: Forward-version render — Telegram 12.10.1 SMS-family screen (REAL APX EVIDENCE)

### کلاسیفیکاسیون: PROVEN (new evidence)

- Runtime بدون هیچ تغییری، نسخه‌ی جدید تلگرام (12.10.1) را اجرا کرد:
  - 12,544 کلاس از 5 DEX بارگذاری شد
  - زنجیره click واقعی (`phase_b_click` ×4) اجرا شد
  - SMS-family screen رندر شد: **41,233 non-white pixel** (1080×1920)
  - **3/3 اجرای مجدد → SHA یکسان** `06fb40da16b1f473…` (deterministic)
  - 0 crash، 0 خطا در crash.log
- شواهد: `run/uc_v12_run{1,2,3}/screenshot.png` + `run/uc_v12_first/*`
- **اهمیت:** تمام پایگاه دانش (resource mapping ها، D8-shrunk names مثل `res/cs3.json`)
  روی 10.14.5 ساخته شده بود؛ صفحه خانواده-SMS در نسخه جدید هم ساختار مشابه
  پیدا کرد و رندر شد → معماری runtime به نسخه APK وابسته نیست.

### یافته فرعی UC2-001a: resource VALUES در نسخه جدید resolve نمی‌شوند (OPEN)
- متن‌های صفحه به‌جای مقدار رشته واقعی، **نام فیلد R** هستند:
  `SMSWordTitle`, `SMSWordError`, `SMSPhraseTitle`, `WrongCode`, …
- علت: mapping `resource_values.json` فقط برای 10.14.5 تولید شده؛ در 12.10.1
  مقادیر `R$string` عوض شده‌اند (D8 ordinals جدید: 987201…, resid=3 برای بعضی).
- رگرسیون مرتبط: SFS — متن «موجود» است ولی «مقدار واقعی کاربر-نمایان» نیست.
  **این را باید به `ANDROID_SILENT_FALSE_SUCCESS_MAP.md` اضافه کرد**
  (و اضافه شد — SFS-010 در این کمپین).
- رفع پیشنهادی generic: تولید خودکار resource map از خود APK
  (ARSC → string pool per config) به‌جای JSON دستی per-version. مسیر موجود
  `resource_parser.cpp` (modern ARSC، C3-F022a/b/c) همین را می‌تواند.
- Confidence: HIGH (trace مستقیم RES-INTERCEPT + متن رندرشده)

### یافته فرعی UC2-001b: 7 عدد RLottie pending view در v12 شناسایی شد
- trace: `[EXP098-RLOTTIE-PENDING] view=2393 … resid=917654 target=28x28` (و ۶ مورد دیگر)
- یعنی wiring عمومی CM-027 روی نسخه جدید هم hook می‌شود (بدون hardcode).
- رندر خود Lottie برای v12 هنوز verify نشد (نیاز به R$raw mapping جدید) — OPEN.

---

## UC2-002: تایپوگرافی — پایپ‌لاین کامل متن اثبات شد (NEW PROOF)

### کلاسیفیکاسیون: PROVEN (POC خارج از runtime، کتابخانه‌های مرجع)

پایپ‌لاین الزامی §6: `Unicode → bidi → shaping → glyph selection → metrics →
rasterization → layout → framebuffer` — به‌صورت real implementation اجرا و
اثبات شد (کد: `scripts/wsc2_text_pipeline.cpp` در پک تحویلی):

| مرحله | کتابخانه مرجع | نسخه sandbox | نتیجه |
|-------|----------------|---------------|--------|
| bidi | FriBidi | 1.0.16 | ✅ visual reorder + first-strong |
| shaping | HarfBuzz | 10.2.0 | ✅ اتصال حروف عربی/فارسی صحیح |
| glyph/metrics | FreeType | 2.13.3 | ✅ advance/bbox واقعی |
| raster | FreeType AA | — | ✅ anti-aliased |
| layout | — | — | ✅ RTL right-align / LTR left-align |
| framebuffer | PPM→PNG | — | ✅ 27,875 non-white px |

### نمونه‌های تست (4/4 OK)
1. `کد تأیید تلگرام ۱۲۳۴۵ — Telegram code 67890` → RTL، اعداد فارسی درست، Latin embed درست
2. `ما یک کد به شماره شما فرستادیم +98 912 345 6789` → RTL صحیح
3. `Enter code` → LTR صحیح
4. `کد را دریافت نکردید؟ Didn't get the code?` → RTL صحیح با یک artifact مرزی

### یافته کلیدی UC2-002a: تشخیص جهت پایه (base direction) باید first-strong باشد
- اجرای اول با base=LTR اجباری → **خرابی کامل ترتیب** در خطوط فارسی‌محور
  (Latin معکوس شد: `?edoc eht teg t'ndiD`)
- با heuristic **first-strong** (مطابق `TextDirectionHeuristics.FIRSTSTRONG`
  اندروید: اولین کاراکتر قوی R/AL → RTL، L → LTR) → همه ۴ نمونه درست.
- **نسخه فعلی runtime هیچ bidi/shape ای ندارد** → هر متن فارسی/عربی در
  MiniAndroid الان جدا-حرف و چپ‌به‌راست رندر می‌شود.
- Confidence: HIGH (هر دو حالت با تصویر اثبات شده)

### محدودیت ثبت‌شده (نه پنهان)
- روش «reorder-then-shape» (FriBidi بعد HarfBuzz روی کل خط visual) برای
  scripts اتصال‌پذیر ساده جواب می‌دهد ولی neutral های مرزی (مثل `؟` بین
  RTL و Latin) ممکن است به run اشتباه بچسبند (در نمونه ۴ دیده شد).
- راه درست production: shape per bidi-run در ترتیب منطقی
  (AOSP minikin: `Layout::splitByBidi` → hb_shape هر run → reorder فقط placement).
- فونت DejaVu فقط پوشش پایه عربی دارد؛ برای فارسی واقعی Vazirmatn/Noto
  Naskh لازم است (font fallback chain → FontBackend).

### پیوند به ابزار (WS-C4)
- هر سه کتابخانه (FriBidi/HarfBuzz/FreeType) در sandbox حاضرند و لایسنس‌ها
  سازگار (LGPL/Old-MIT/FTL) — ماتریس در `WS-C4_TOOL_MATRIX.md`.

---

## UC2-003: وضعیت فونت فعلی runtime (RECONCILIATION)

- BitmapFont (8px advance یکنواخت، 95 ASCII) همچنان تنها backend داخل runtime است.
- یافته FREETYPE_VS_BITMAPFONT.md قبلی تایید شد: زیربرآورد advance حدود 36٪
  → مشکل wrap/clip واقعی؛ IoU با FreeType فقط 13.1٪.
- **دو مسیر ارتقا (اولویت‌بندی WS-C2):**
  1. حداقلی: `measure_text_accurate()` با FreeType فقط برای measure
     (رندر BitmapFont بماند) — ریسک کم، بصری بهتر برای wrap.
  2. کامل: FontBackend interface + backend فری‌تایپ با shaping HarfBuzz
     و bidi FriBidi (UC2-002 اثباتش کرده) → فارسی/عربی واقعی.
- از بازنویسی decoder های اثبات‌شده پرهیز شد (قانون §6).

---

## UC2-004: شواهد بصری v12 (VISUAL EVIDENCE per §14)

- text overlap در بالای صفحه v12 دیده شد (عنوان‌ها روی هم) — احتمالاً
  custom view (LoginActivityPhraseView) بدون measure/layout واقعی.
  classified: OPEN (نیاز به trace EXP095-LAYOUT برای v12)
- code-field row (۵ کادر) درست رندر شد؛ toolbar band درست.
- screenshot SHA هر سه اجرا یکسان → پایدار.
- فایل‌ها: `run/uc_v12_run1/screenshot.png` (1080×1920) + crop تحویلی.

---

## وضعیت STOP GATE (§22) — WS-C2

| آیتم | وضعیت |
|------|--------|
| graphics backend analysis | PARTIAL (CM-024/027 قبلی + این کمپین) |
| font pipeline | POC PROVEN (UC2-002)؛ داخل runtime هنوز BitmapFont |
| FreeType | PROVEN (POC + مقایسه قبلی) |
| HarfBuzz | PROVEN (POC اتصال فارسی) |
| image pipeline | PROVEN قبلی (63/64) — دست‌نخورده، بدون رگرسیون |
| animation pipeline | PROVEN قبلی (CM-026)؛ v12 pending شناسایی (UC2-001b) |
| RLottie actual-screen proof | PROVEN قبلی (CM-027)؛ v12 render OPEN |
| Telegram typography | PARTIAL (v12 field-names به‌جای strings — UC2-001a) |
| non-Telegram graphics regressions | NOT RUN در این کمپین (APKهای corpus خارجی دانلود نشدند — ثبت طبق §18) |
| malformed inputs | قبلاً 14/14 (CM-025) — تغییر مرتبطی نبود |
| ASAN native | NOT RUN (تغییر فقط در مسیر value-return؛ ریسک overflow ندارد — کد بازبینی شد) |
