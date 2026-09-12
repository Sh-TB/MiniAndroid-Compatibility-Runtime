# WS-C3 KNOWLEDGE — Android Framework / Resources / Streams / Components / Corpus

**Unified Coder campaign:** 2026-08-27 · Tested HEAD: `bbe0ce3` → `86bd646`
**روش:** source audit روی `src/` (64k LOC)، اجرای real APK، مقایسه با baseline های C3 قبلی.

---

## UC3-001: شمارش پل API فعلی (FRAMEWORK FREQUENCY REMEASURE)

سطح فعلی پل (`bridge_to_api` + shadows) روی HEAD اندازه‌گیری شد:

- **95 کلاس** هندل‌شده در `dalvik_engine.cpp` (به‌علاوه ۸ Shadow در
  `framework/android_shadows.h`: ArchTaskExecutor, Thread, Looper, Handler,
  Intent, Activity, View, Collection)
- دسته‌ها: 30 widget/view، 12 androidx (appcompat+fragment)، 10 manager
  (system services)، io/lang/util پایه، 7 کلاس Telegram-specific
  (AndroidUtilities، TLRPC، LayoutHelper — فقط برای زنجیره login)

### شکاف‌های سطح اولویت (compared to §7 charter)

| سطح | وضعیت فعلی روی HEAD | وضعیت charter | شواهد |
|-----|---------------------|----------------|-------|
| InputStream خانواده | فقط `InputStream`/`InputStreamReader`/`BufferedReader` بنیادی (asset stream) | expand full | grep: بدون `BufferedInputStream`/`ByteArrayInputStream`/`FileInputStream` handlers |
| **Uri** | **ABSENT — هیچ handler برای `Landroid/net/Uri` وجود ندارد** | 24/24 semantics | grep کل src: 0 نتیجه |
| LayoutInflater | PARTIAL (layout_cache.json path + Factory basic) | Factory2/style/theme/include/merge | OA_API_MAP: PARTIAL |
| Drawable خانواده | فقط مسیر resource→Bitmap برای ImageView؛ **هیچ ColorDrawable/StateListDrawable/…** | 7 نوع | grep: 0 |
| Context methods | اکثر پایه‌ها IMPLEMENTED (getPackageName/getAssets/getFilesDir/…) | audit | bridged |
| Handler/Looper | Shadow + MessageQueue واقعی (CM-018 قبلی) | audit | 15 ارجاع shadow |
| Components (BR/Service/Provider) | **ABSENT** (فقط IntentShadow ثبت اطلاعات) | census | F010 همچنان OPEN |
| Kotlin semantics | هیچ (فقط skip class-init برای `Lkotlin/*`) | audit | F012 catch-all قبلاً مشکلات می‌ساخت |
| SystemClock | **ABSENT** (F004: بعد از fix مقدار-wide، mechanism باز شد ولی خود سرویس نیست) | verify | grep: 0 → **F004 همچنان OPEN** |
| Multi-DEX | WORKING (5 DEX v12 بارگذاری شد — شاهد جدید v12) | expand | UC3-002 |
| JNI census | ابزار دارد (`tools/exp042_jni_inventory.py` + docs/exp042/JNI_INVENTORY.md)؛ runtime: JNI همه stub | census | قبلی |
| Google census | NOT DONE در این کمپین (نیاز corpus scan) | census only | §31 — census-only قانون |

---

## UC3-002: Forward-version compat — Telegram 12.10.1 روی HEAD (NEW PROOF)

- **PROVEN**: 12,544 کلاس/5 DEX بارگذاری؛ 0 خطا؛ deterministic (3/3 SHA).
  این بزرگ‌ترین تغییر نسخه‌ای تست‌شده (10.14.5 → 12.10.1، دو سال نسخه).
- معنایش معماری: مسیرهای generic (multi-DEX injection، `$r8$lambda` dispatch،
  AXML inflate، RLottie hook) به نسخه وابسته نیستند؛ فقط **داده‌های mapping
  per-version** (resource_values.json) عوض می‌شوند → راه‌حل: تولید خودکار
  mapping از ARSC (همان UC2-001a).

---

## UC3-003: UC-CM-001 — بستن F012 (CATCH-ALL FALSE-SUCCESS)

- پیاده‌سازی و merge شد: commit `86bd646` — جزئیات کامل در `SOURCE_CHANGES.md`.
- classification F012: **FIXED** (قبلاً OPEN)
- classification F015 (superclass-bridge retry): **OPEN** (تغییری نکرد؛ مسیر
  پیشنهادی بعدی: در `try_recursive_invoke` شکست، قبل از bridge، یک بار با
  superclass زنجیره تلاش شود)

## UC3-004: Reconciliation بقیه یافته‌های C3

| ID | عنوان | وضعیت قبلی | وضعیت فعلی روی HEAD |
|----|-------|-------------|----------------------|
| F002 | openFileOutput path divergence | PROVEN/KEEP | تایید — sandbox سالم است، دست نخورد |
| F004 | SystemClock absent/zero | PARTIAL | **OPEN** — هنوز هیچ handler (grep=0) |
| F005 | Application lifecycle | FIXED (b7dc97b) | تایید — manifest android:name خوانده می‌شود (v12 هم) |
| F007 | getSystemService null | PARTIAL | PARTIAL — honest null؛ سرویس‌ها غایب |
| F010 | Components absent | OPEN | OPEN (unchanged) |
| F011 | PackageManager hardcode | NOT REPRODUCIBLE | تایید — hardcode وجود ندارد |
| F012 | catch-all void | OPEN | **FIXED** (UC-CM-001, 86bd646) |
| F016 | proto resolution ()V fallback | IMPLEMENTED | تایید + الان توسط UC-CM-001 هم مصرف می‌شود |
| F017/N9 | Makefile header deps (-MMD -MP) | OPEN | **ALREADY FIXED** در HEAD (Makefile line 5: `-MMD -MP` دارد) — بستن |

---

## UC3-005: CORPUS — وضعیت و افزودنی

- manifest فعلی: `tests/corpus/apks.json` — Telegram + gmdice + … (ورودی‌های
  خارجی، دانلود on-demand).
- این کمپین: Telegram **12.10.1** به‌عنوان entry جدید معرفی شد (hash/نسخه
  در `WS-C3_CORPUS.md`) — طبق §18 به‌صورت HASH-MISMATCH-vs-manifest ثبت شد
  ولی REAL و PASS.
- شمارش کل corpus از ادعای «100+»: در repo فقط manifest چندتایی هست؛
  **ادعای 100+ قابل راستی‌آزمایی از clone نبود** → طبق §18:
  UNKNOWN ثبت می‌شود، نه PASS. (نیاز: آپلود registry کامل نتایج)
- non-Telegram runs در این کمپین انجام نشد (زمان/شبکه) — ثبت صادقانه.

---

## وضعیت STOP GATE (§22) — WS-C3

| آیتم | وضعیت |
|------|--------|
| framework frequency remeasured | ✅ (95 کلاس + 8 shadow شمرده شد) |
| InputStream expanded | ❌ OPEN (فقط پایه) |
| Uri advanced | ❌ **ABSENT** — بالاترین اولویت جدید |
| LayoutInflater assessed | PARTIAL (Cache path؛ Factory2/theme باقی) |
| Drawable semantics assessed | ❌ ABSENT (فقط Bitmap) |
| resource qualifiers | PARTIAL (density/night در ARSC parser قبلی) |
| Context audit | ✅ پایه‌ها IMPLEMENTED |
| Handler/Looper audit | ✅ |
| components census | ❌ ABSENT (F010) |
| Kotlin audit | ❌ ABSENT |
| multi-DEX expansion | ✅ (v12 = 5 DEX proof جدید) |
| JNI census | PARTIAL (ابزار هست؛ census به‌روز نشد) |
| Google census | ❌ NOT DONE (census-only قانون) |
| 125+ corpus progress | UNKNOWN (registry 100+ خارج از clone) |
