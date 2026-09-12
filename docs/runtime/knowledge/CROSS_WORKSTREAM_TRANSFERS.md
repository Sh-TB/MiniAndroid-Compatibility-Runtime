# CROSS-WORKSTREAM TRANSFERS — رکوردهای انتقال بین جریان‌ها (§10)

هر رکورد: SOURCE / FINDING ID / EXPECTED / ACTUAL / EVIDENCE / RELEVANT WS / RECOMMENDATION

---

### X-001 — از UC2-001a (کمپین) به WS-C3/PRIMARY
- **SOURCE:** اجرای Telegram 12.10.1 — trace RES-INTERCEPT
- **FINDING ID:** X-001 (resource map per-version)
- **EXPECTED:** متن‌های صفحه = رشته‌های واقعی localised
- **ACTUAL:** نام فیلد R (SMSWordTitle/WrongCode/…) به‌عنوان متن رندر شد
- **EVIDENCE:** stderr `[EXP091-SETTEXT] … text="SMSWordTitle"` + screenshot v12
- **RELEVANT:** WS-C3 (resources/ARSC)، Primary
- **RECOMMENDATION:** تولید خودکار string/raw map از resources.arsc در زمان load؛ ثبت SFS-010

### X-002 — از WS-C4 به WS-C2
- **FINDING ID:** C4TOC2-001..003 (متن کامل: `WS-C4_TO_C2_C3.md`)
- **خلاصه:** FriBidi/HarfBuzz/FreeType آماده و اثبات‌شده؛ ThorVG جانشین آینده rlottie؛ APNG adapt-on-libpng
- **RECOMMENDATION:** FontBackend adapter (T1)

### X-003 — از WS-C4 به WS-C3
- **FINDING ID:** C4TOC3-001..003
- **خلاصه:** SQLite amalgamation (D1)، libdeflate benchmark، dexlib2 cross-check
- **RECOMMENDATION:** به ترتیب D1 → benchmark → CI difftest

### X-004 — از WS-C5 به WS-C3/PRIMARY
- **SOURCE:** تحقیق Robolectric/VirtualApp/Evoke/Redroid
- **FINDING ID:** X-004 (interception map + environment)
- **EXPECTED:** — (معماری)
- **ACTUAL:** سطح intercept واقعی کوچک و شمارش‌پذیر است (system services + natives + libcore-delta)
- **EVIDENCE:** 607 shadow Robolectric خوشه‌ای؛ proxies/ ویچوال‌اپ؛ kernel-deps redroid
- **RELEVANT:** WS-C3، Primary
- **RECOMMENDATION:** `SERVICE_INTERCEPTION_MAP.md` + Environment simulation (P1/P2 در WS-C5_PRIMARY_TRANSFER)

### X-005 — از WS-C3 به WS-C2
- **SOURCE:** ممیزی src + اجرای v12
- **FINDING ID:** X-005 (text overlap v12)
- **EXPECTED:** عنوان‌ها جدا رندر شوند
- **ACTUAL:** هم‌پوشانی عمودی (custom view بدون measure/layout کامل)
- **EVIDENCE:** `run/uc_v12_top.png`
- **RELEVANT:** WS-C2
- **RECOMMENDATION:** بعد از T1/T4 دوباره trace EXP095-LAYOUT برای v12

### X-006 — از UC-CM-001 به همه
- **FINDING ID:** UC-CM-001 (86bd646)
- **EXPECTED:** F012 false-success خاموش بسته شود بدون رگرسیون
- **ACTUAL:** merge شد؛ 3/3 SHA یکسان با baseline؛ trace count برابر
- **EVIDENCE:** `SOURCE_CHANGES.md` + runs
- **RELEVANT:** همه (semantic VM)
- **RECOMMENDATION:** merge روی main + بعد از آن F015 (superclass retry) را ببندید

# CROSS_CODER_RECONCILIATION — جدول پل Coder2/Coder3/Coder4/Primary/UC (§6 قسمت دوم charter)

| CODER | FINDING | SOURCE SHA/مرجع | STATUS قبلی | STATUS فعلی روی `86bd646` | شواهد | تصمیم |
|---|---|---|---|---|---|---|
| C2 | C2-F31 (OX board render) | branch Coder2 | NOT INTEGRATED | NOT INTEGRATED (خارج از دامنه این کمپین) | CODER2_KNOWLEDGE | باز — نیاز branch merge توسط Primary |
| C2 | C2-F01/F06/F07/F12/F22 | EXP-061/089/093 | INTEGRATED | INTEGRATED — تایید مجدد روی v12 (lambda dispatch کار کرد) | اجرای v12 | بسته |
| C3 | F002 | PRIMARY_CODER_TRANSFER_REPORT | PROVEN/KEEP | KEEP — sandbox سالم | کد | هیچ تغییری نکن |
| C3 | F004 SystemClock | CODER3 | PARTIAL | **OPEN** (grep=0) | UC3-001 | T3-WS-C3 |
| C3 | F005 Application lifecycle | b7dc97b | FIXED | FIXED — روی v12 هم بارگذاری Application انجام شد | اجرا | بسته |
| C3 | F007 | CODER3 | PARTIAL | PARTIAL (honest null) | کد | بعد از interception map |
| C3 | F010 components | CODER3 | OPEN | OPEN | grep | T4-WS-C3 |
| C3 | F011 PackageManager | CODER3 | NOT REPRODUCIBLE | تایید مجدد — hardcode نیست | grep | بسته |
| C3 | **F012 catch-all void** | CODER3 | OPEN | **FIXED (UC-CM-001, 86bd646)** | 3/3 SHA + trace | merge شود |
| C3 | F015 | CODER3 | OPEN | OPEN | کد | T5-WS-C3 (بعد از CM-001) |
| C3 | F016 proto resolver | CODER3 | IMPLEMENTED | IMPLEMENTED + حالا مصرف‌کننده UC-CM-001 | کد | بسته |
| C3 | F017/N9 Makefile deps | CODER3 | OPEN | **ALREADY FIXED** (Makefile: -MMD -MP) | Makefile line 5 | بسته |
| C4 | SQLite 11/11+ | CODER4 transfers | PROVEN (POC) | NOT INTEGRATED در main | matrix D1 | D1 adoption |
| C4 | OkHttp 5/5, libcurl 6/6 | CODER4 | PROVEN (POC) | NOT INTEGRATED | matrix D5 | D5 |
| C4 | stb_image/giflib/rlottie/FreeType/HarfBuzz | CODER4 | PROVEN | rlottie/FreeType IN (build)، بقیه oracle | build | — |
| C4 | FFmpeg/audio/video oracles | CODER4 | PROVEN (oracle) | NOT INTEGRATED | matrix D4 | D4 |
| Primary | CM-001..CM-027 | CODER_MAIN_KNOWLEDGE | PROVEN | همه روی HEAD؛ بدون رگرسیون در v12 (به‌جز resource map) | v12 run | — |
| UC | UC2-002 typography POC | این کمپین | PROVEN (POC) | خارج از runtime | evidence B | T1-WS-C2 |
