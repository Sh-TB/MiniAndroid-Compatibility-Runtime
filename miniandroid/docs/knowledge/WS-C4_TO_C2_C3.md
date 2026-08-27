# WS-C4 → WS-C2 TRANSFER (یافته‌های ابزاری مرتبط با گرافیک/متن/انیمیشن)

**FINDING ID:** C4TOC2-001
- **SOURCE:** تحقیق WS-C4 (mid-2026) + POC داخلی WS-C2
- **FINDING:** سه‌گانه FriBidi/HarfBuzz/FreeType هم‌اکنون در sandbox قابل build و اثبات است
  (POC: 4/4 فارسی/RTL OK). SheenBidi 3.0.0 (Apache-2.0) جایگزین permissive برای FriBidi (LGPL) در آینده.
- **EXPECTED:** متن فارسی/عربی متصل و RTL در framebuffer
- **ACTUAL:** POC موفق؛ داخل runtime هنوز BitmapFont بدون bidi
- **EVIDENCE:** `run/wsc2_text_pipeline.png` + metrics JSON
- **RELEVANT:** WS-C2
- **RECOMMENDATION:** FontBackend adapter (T1 در WS-C2_PRIMARY_TRANSFER)

**FINDING ID:** C4TOC2-002
- **SOURCE:** WS-C4 matrix
- **FINDING:** ThorVG v1.0 (MIT، C API) جانشین جدی rlottie برای بلندمدت (DEFER نه USE)؛
  libwebpdemux موجود برای animated-WebP آماده است (فقط frame iteration مانده).
- **RECOMMENDATION:** بعد از پایداری RLottie فعلی، spike کوچک ThorVG؛ animated-WebP را
  روی مسیر AnimationBackend کامل کنید (CM-027 future work).

**FINDING ID:** C4TOC2-003
- **SOURCE:** WS-C4 matrix
- **FINDING:** APNG کتابخانه C مستقل سالم ندارد → ADAPT روی libpng (acTL/fcTL/fdAT)
- **RECOMMENDATION:** اگر corpus APNG خواست، پارسر chunk-level کوچک بنویسید نه lib جدید.

# WS-C4 → WS-C3 TRANSFER (یافته‌های ابزاری مرتبط با فریمورک/corpus)

**FINDING ID:** C4TOC3-001
- **SOURCE:** WS-C4 matrix + Robolectric research (WS-C5)
- **FINDING:** SQLite amalgamation تک‌فایل (Public domain) + precedent Robolectric nativeruntime
  (بوت SQLite واقعی برای shadow) → مسیر امن DatabaseBackend.
- **RECOMMENDATION:** D1 در WS-C4_PRIMARY_TRANSFER — اولین adoption بعدی.

**FINDING ID:** C4TOC3-002
- **SOURCE:** WS-C4 matrix
- **FINDING:** libdeflate 1.24 (MIT, ~0.1MB) inflate سریع‌تر از zlib برای hot-path APK.
- **RECOMMENDATION:** benchmark روی تلگرام v12؛ بعد adapter با fallback.

**FINDING ID:** C4TOC3-003
- **SOURCE:** AppManager research (WS-C5)
- **FINDING:** dexlib2 (baksmali) مدل مرجع battle-tested فرمت DEX است — برای cross-check
  پارسر خودمان (به‌ویژه بعد از درس C2-F11 درباره misdecode ابزارها).
- **RECOMMENDATION:** در CI: difftest ساختاری کلاس‌ها بین dexlib2 و dex_parser خودمان
  روی همان APK v12 (schema-level، بدون لینک Java در runtime).
