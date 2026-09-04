# SOURCE_CHANGES.md — تغییرات سورس‌کد کمپین UNIFIED CODER

**Task ID:** UNIFIED-CAMPAIGN-2026-08-27
**Base commit (قبل از تغییرات):** `bbe0ce3` — EXP-098/CM-027: RLottieImageView → RLottieDecoder runtime wiring
**Commit تغییر (بعد از تغییرات):** `86bd646` — UC-CM-001
**توضیح:** این سند دقیقاً طبق خواسته شما نوشته شده: هر تغییر سورس + دلیل + شواهد، تا در آینده بتوانید سورس اصلی را بر اساس آن به‌روزرسانی کنید.

---

## فهرست تغییرات

| ID | فایل(ها) | نوع | وضعیت رگرسیون |
|----|----------|-----|----------------|
| UC-CM-001 | `src/dex/dalvik_engine.cpp`, `src/dex/dalvik_engine.h` | اصلاحیه generic (بستن F012) | ✅ 3/3 SHA یکسان با baseline |

---

## UC-CM-001: بازگشت مقدار Type-Aware در catch-all پل API (بستن یافته باز F012)

### شرح مشکل (منشأ یافته)
این مشکل اول‌بار توسط **Coder 3** به‌عنوان یک الگوی سیستمی «false-success خاموش» ثبت شده بود:

```
متد ناشناخته → STUBBED + VOID → متعاقباً move-result / move-result-wide → صفرِ خاموش
```

یعنی هر متدی که به پل (`bridge_to_api`) می‌رسید و هندلر اختصاصی نداشت، همیشه
`DalvikValue::make_void()` برمی‌گرداند — حتی اگر امضای واقعی متد در DEX
`Z` (boolean)، `I` (int)، `J` (long) یا یک reference باشد. نتیجه:

1. اگر بایت‌کد بعد از فراخوانی `move-result` بزند، یک مقدار VOID به ثبات
   نشت می‌کند (نوع نامعتبر در ثبات).
2. `if-nez` / `if-eqz` روی چنین مقداری تصمیم نادرست می‌گیرند.
3. وضعیت «شکست خاموش» ایجاد می‌شود که در trace دیده نمی‌شود چون
   status درست (`STUBBED`) ثبت شده ولی مقدار غلط است.

توصیهٔ ثبت‌شده در `CODER3_KNOWLEDGE.md` (بخش F012):
> "The real fix: for unknown methods, check return type from proto
> descriptor and return appropriate default (0 for int, null for objects,
> false for boolean) instead of always returning void."

### فایل‌ها و محل دقیق تغییر

#### 1) `miniandroid/src/dex/dalvik_engine.h` — امضای `bridge_to_api`
پارامتر اختیاری `method_idx_hint` اضافه شد (default = `0xFFFFFFFF` یعنی «بدون hint»):

```cpp
// قبل:
bool bridge_to_api(const std::string& class_name, const std::string& method,
                   const std::vector<DalvikValue>& args, DalvikValue& result,
                   ApiCallTrace::Status& status);

// بعد:
bool bridge_to_api(const std::string& class_name, const std::string& method,
                   const std::vector<DalvikValue>& args, DalvikValue& result,
                   ApiCallTrace::Status& status,
                   uint32_t method_idx_hint = 0xFFFFFFFFu);
```

**سازگاری:** چون پارامتر default دارد، هیچ caller قدیمی نمی‌شکند.

#### 2) `miniandroid/src/dex/dalvik_engine.cpp` — catch-all انتهای `bridge_to_api`
بلوک پایانی (`// Default: stubbed but not crashing`) جایگزین شد:

```cpp
// جدید (خلاصه):
status = ApiCallTrace::Status::STUBBED;          // مثل قبل — صادقانه
if (method_idx_hint != 0xFFFFFFFFu) {
    const std::string proto = resolve_method_proto_for_dex(method_idx_hint, current_dex_index_);
    const size_t rparen = proto.rfind(')');
    if (rparen != std::string::npos && rparen + 1 < proto.size()) {
        const std::string ret = proto.substr(rparen + 1);   // return descriptor
        // V→void(قدیم) | Z→false | B/S/C/I→0 | J→0L | F/D→0.0 | L…/[…→null
        ... // map به DalvikValue::make_bool/make_int/make_long/make_null/...
        return true;
    }
}
result = DalvikValue::make_void();   // fallback: رفتار قدیمی
return true;
```

**نکات کلیدی:**
- Status همچنان `STUBBED` می‌ماند → صادق‌بودن bookkeeping حفظ شده
  (ما success جعلی نمی‌سازیم؛ فقط «مقدار پیش‌فرض درست‌نوع» برمی‌گردانیم).
- `resolve_method_proto_for_dex` (موجود از EXP-088/F016) پروتوی واقعی callee
  را از `proto_ids` همان DEX درمی‌آورد؛ fallback خودِ آن تابع `()V` است که
  همان رفتار قدیمی را می‌دهد → بدون ریسک اضافه.
- Reference types (`L...;` و آرایه‌ها) → `make_null()` (معادل «بدون نتیجه»
  در ART برای متد ناموجود، بدون crash).

#### 3) `miniandroid/src/dex/dalvik_engine.cpp` — ۶ call-site به‌روزرسانی شد
همه جاهایی که `bridge_to_api` صدا زده می‌شود حالا `method_idx` را هم پاس می‌دهند:

| خط (تقریبی) | تابع دربرگیرنده | تغییر |
|--------------|------------------|-------|
| 4817 | `execute_method_internal` | `..., status, method_idx)` |
| 7230 | `execute_invoke` (مسیر اصلی virtual/interface/static) | `..., api_status, method_idx)` |
| 7398 | super-call path (`<super>`) | `..., api_status, method_idx)` |
| 7561 | `execute_invoke_direct` | `..., status, method_idx)` |
| 7875 | `execute_invoke_static` | `..., status, method_idx)` |
| 7969 | `execute_invoke_interface` | `..., status, method_idx)` |

### چرا این تغییر امن است (تحلیل ریسک)
1. **بدون hint** → دقیقاً رفتار قبلی (void). فقط invoke-site هایی که method_idx
   دارند (و همه دارند) مسیر جدید را می‌روند.
2. مسیر جدید فقط روی متدهایی اجرا می‌شود که **قبلاً هم fail می‌شدند**
   (هیچ هندلر موفقی عوض نمی‌شود).
3. اگر پروتو resolve نشود → fallback تابع resolver خودش `"()V"` می‌دهد →
   همان void قدیمی.
4. مقادیر جدید (0/false/null) همان مقادیری هستند که در واقع ART برای
   «متد مفقود» در سطح register semantic نزدیک‌تر است؛ CM-008 قبلاً
   zero-truthiness برای BOOLEAN/BYTE/SHORT/CHAR را درست کرده و با آن هم‌خوان است.

### شواهد (EVIDENCE)

#### APK واقعی — Telegram **12.10.1** (versionCode 70389، 5 DEX، 73MB)
- این نسخه **هرگز قبلاً تست نشده بود** (پایگاه دانش روی 10.14.5 ساخته شده بود)
  → اولین شواهد forward-compatibility.
- SHA256 APK: `f5e1192725772960cc94b83e54ffd8939f876b2b6e5f21d4a8537eb6fcba50e6`
- **قبل از تغییر:** ۳ اجرا → هر سه `06fb40da16b1f473980cfea9...`، exit=0،
  41233 non-white pixel، 12582 trace event، 0 خطا
- **بعد از تغییر:** ۳ اجرا → هر سه `06fb40da16b1f473980cfea9...` (یکسان با قبل)،
  exit=0، همان pixel count، همان 12582 event، 0 خطا
- نتیجه: **صفر رگرسیون** روی full-chain اجرای واقعی (launch→login→SMS screen→render).

#### محیط ساخت
- g++ 14.2.0 (Debian)، `make -j4` → BUILD SUCCESS بدون error جدید
- rlottie بازسازی شد از منبع Samsung/rlottie (SHA `43075538`) به روش static manual build
  (meson در sandbox نبود) — اسکریپت: `scripts/build_rlottie.sh` (بیرون repo)

### نحوه اعمال روی سورس اصلی (برای آینده)
دو راه:
1. **patch file:** `0001-UC-CM-001-Type-aware-STUBBED-defaults-in-bridge_to_a.patch`
   → `git apply` یا `git am` روی commit `bbe0ce3` یا هر HEAD بعدی (تا وقتی
   تابع `bridge_to_api` و catch-all انتهایی بازنویسی نشده باشند).
2. **دستی:** سه بخش بالا (header، catch-all، ۶ call-site) — کل diff حدود ۷۰ خط.

---

## تغییرات non-source (تجهیزات/محیط) — برای بازتولید

| مورد | شرح |
|------|-----|
| rlottie rebuild | clone عمیق-1 از Samsung/rlottie + `config.h` دستی (`LOTTIE_THREAD_SUPPORT=1`, `LOTTIE_CACHE_SUPPORT=0`) + کامپایل ۳۵ TU به `librlottie.a` |
| Telegram APK | دانلود از `telegram.org/dl/android/apk` → نسخه 12.10.1؛ **HASH MISMATCH** با manifest (10.14.5) — version drift، واقعی و قابل‌استفاده |
| فونت تست فارسی | DejaVuSans.ttf (پشتیبانی عربی پایه) — برای تولید واقعی: Vazirmatn/Noto Naskh پیشنهاد می‌شود |

## یافته‌های جعبه‌ابزار (برای شفافیت)
- خروجی grep در برخی فایل‌ها به‌خاطر الگوی `ids[method_idx]` دچار artifact
  ترمینال شد (`ESC[m`) — فایل سالم بود؛ با خواندن بایت-به-بایت python تأیید شد.
  عبرت: قبل از هر تغییر مبتنی بر grep، raw bytes را تأیید کنید (همان درس C2-F11).
