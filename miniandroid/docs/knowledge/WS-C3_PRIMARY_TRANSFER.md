# WS-C3 PRIMARY TRANSFER

**به:** Primary Coder · **از:** WS-C3 (Unified Coder) · **تاریخ:** 2026-08-27

## T1. UC-CM-001 را merge کنید (آماده است)
- commit `86bd646` / patch فایل ضمیمه. صفر رگرسیون روی تلگرام 12.10.1 (3/3 SHA).
- F012 را می‌بندد؛ مقادیر STUBBED type-aware می‌شوند.
- CONFIDENCE: HIGH · RISK: LOW · EVIDENCE: `SOURCE_CHANGES.md`

## T2. Uri را پیاده‌سازی کنید (بزرگ‌ترین شکاف اندازه‌گیری‌شده)
- `Landroid/net/Uri` **هیچ handler ای ندارد** (grep کل src = 0) در حالی که
  charter آن را 24/24 اثبات‌شده فرض می‌کرد (احتمالاً تست‌های Python بوده).
- ACTION: bridge handler برای parse/Builder/scheme/authority/path/
  queryParameter/getQueryParameter/normalizeScheme + object model ساده.
- منبع مرجع: AOSP `Uri.java` / libcore. EVIDENCE: WS-C3_KNOWLEDGE §UC3-001
- CONFIDENCE: HIGH (gap قطعی) · BENEFIT: deep-link/content URI ها در corpus

## T3. SystemClock را اضافه کنید (F004 — راحت و پرتکرار)
- `uptimeMillis/elapsedRealtime*` → از `clock_gettime(CLOCK_MONOTONIC/BOOTTIME)`.
  deterministic-clock switch را هم اضافه کنید (برای reproducibility).
- CONFIDENCE: HIGH · LOC: ~40

## T4. Components حداقلی (F010): BroadcastReceiver فقط dispatch داخلی
- هدف اول: manifest-declared receivers با intent filter های explicit.
  census Google را جدا نگه دارید (§31 census-only).

## T5. F015 (superclass-bridge retry)
- بعد از UC-CM-001: در fail مسیر `try_recursive_invoke`، قبل از bridge،
  زنجیره superclass را امتحان کنید. کوچک و generic.

## T6. Corpus registry واقعی را در repo بریزید
- ادعای 100+ قابل راستی‌آزمایی از clone نیست (فقط چند manifest entry).
  `WS-C3_CORPUS.md` الگوی فیلدها را دارد.

## DO NOT
- F012-AMPLIFIER (commit ab48fbc از branch ادغام‌نشده) را blindly نیاورید —
  UC-CM-001 هدفش را با ریسک کمتر برآورده کرد.
- SQLite/Google support وسیع را «فقط چون هست» پیاده نکنید (§31).
