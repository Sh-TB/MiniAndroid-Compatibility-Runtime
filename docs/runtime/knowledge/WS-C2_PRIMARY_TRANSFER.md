# WS-C2 PRIMARY TRANSFER

**به:** Primary Coder · **از:** WS-C2 (Unified Coder) · **تاریخ:** 2026-08-27
**اقدام درخواستی بر اساس شواهد، به ترتیب ارزش:**

## T1. تایپوگرافی واقعی را داخل runtime بیاورید (بالاترین ارزش)
- اثبات کامل پایپ‌لاین انجام شد: `scripts/wsc2_text_pipeline.cpp`
  (FriBidi 1.0.16 → HarfBuzz 10.2.0 → FreeType 2.13.3) — فارسی متصل،
  RTL درست، metrics درست، 4/4 نمونه OK.
- ACTION: `FontBackend` interface در `src/renderer/` بسازید؛ backend اول:
  FreeType+HarfBuzz+FriBidi با **first-strong** base direction
  (کد POC را کپی کنید). BitmapFont را به‌عنوان fallback نگه دارید.
- EVIDENCE: `run/wsc2_text_pipeline.{png,ppm}` + metrics JSON (27,875 px، 4/4)
- CONFIDENCE: HIGH · RISK: LOW (interface جدید، مسیر فعلی دست نمی‌خورد)
- BENEFIT: فارسی/عربی — یعنی کاربر اصلی تلگرام فارسی‌زبان — واقعی می‌شود.

## T2. متن v12 = نام فیلد، نه مقدار (SFS-010)
- resource mapping per-version شکننده است. ACTION: تولید خودکار string map
  از `resources.arsc` (پارسر modern ARSC موجود در resource_parser.cpp) در
  زمان load، به‌جای `resource_values.json` دستی.
- EVIDENCE: trace `RES-INTERCEPT → SMSWordTitle` روی v12 · CONFIDENCE: HIGH

## T3. RLottie روی v12 را کامل کنید
- 7 pending view شناسایی شد (trace EXP098-RLOTTIE-PENDING) ولی R$raw mapping
  جدید ندارد. با T2 حل می‌شود (raw map هم از ARSC). CONFIDENCE: MEDIUM-HIGH

## T4. measure با FreeType برای wrap صحیح
- زیربرآورد 36% advance (FREETYPE_VS_BITMAPFONT.md) → متن‌ها زودتر wrap می‌شوند.
  حداقل: `measure_text_accurate()`. CONFIDENCE: HIGH · RISK: VERY LOW

## T5. text overlap عنوان‌های v12
- LoginActivityPhraseView بدون layout واقعی. بعد از T1/T4 دوباره بسنجید.

## DO NOT (طبق قانون §4/§6)
- BitmapFont را حذف نکنید (fallback + سناریوی بدون freetype).
- هیچ Telegram-specific mapping در core نگذارید (T2 باید generic از ARSC باشد).
- decoders اثبات‌شده (PNG/WebP/JPEG/RLottie) را بازنویسی نکنید.
