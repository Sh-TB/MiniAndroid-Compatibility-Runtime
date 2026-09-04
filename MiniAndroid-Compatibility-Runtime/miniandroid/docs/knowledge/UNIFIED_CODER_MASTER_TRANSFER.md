# UNIFIED_CODER_MASTER_TRANSFER

**کمپین:** Unified Multi-Workstream Coder (C2+C3+C4+C5) — **تاریخ:** 2026-08-27
**Baseline:** `bbe0ce3` · **تولیدشده روی:** `86bd646` (UC-CM-001) · **APK مرجع:** Telegram 12.10.1 (vc 70389)
**PUSH:** PUSH_PENDING (بدون credential در sandbox) — همه چیز به‌صورت فایل تحویل شد.

---

# TOP 10 DISCOVERIES

1. **Forward-version compat PROVEN:** تلگرام 12.10.1 (هرگز-دیده‌شده، 5 DEX، 12,544 کلاس) اجرا شد؛ 3/3 SHA یکسان `06fb40da…`، 0 خطا، SMS-family screen رندر (41,233px). معماری runtime version-agnostic است.
2. **UC-CM-001 (بستن F012):** catch-all پل API حالا type-aware است (0/false/null/0.0 به‌جای VOID) — با صفر رگرسیون. patch آماده.
3. **فارسی/RTL full-pipeline PROVEN:** FriBidi 1.0.16 → HarfBuzz 10.2.0 → FreeType 2.13.3؛ 4/4 نمونه (اتصال حروف، first-strong، right-align) — داخل runtime هنوز نیست.
4. **base-direction حیاتی است:** با base اجباری LTR، خطوط فارسی کاملاً خراب می‌شوند (Latin معکوس)؛ heuristic FIRSTSTRONG (AOSP) مشکل را حل کرد — باید داخل runtime پیاده شود.
5. **Uri در runtime ABSENT است** (charter آن را اثبات‌شده فرض می‌کرد) — grep کل src = 0 handler برای `Landroid/net/Uri`.
6. **SystemClock هنوز ABSENT** (F004 هنوز OPEN) — بعد از fix مقدار-wide فقط mechanism باز شده بود.
7. **resource map per-version شکننده است (SFS-010 جدید):** در v12 متن‌ها = نام فیلد R (SMSWordTitle/WrongCode) نه مقدار واقعی → راه‌حل: تولید خودکار از resources.arsc در load-time.
8. **RLottie wiring عمومی روی v12 هم hook شد** (7 pending view شناسایی شد) ولی render نیاز به R$raw mapping جدید دارد.
9. **هیچ پروژه بیرونی APK واقعی را CPU-only بدون Android اجرا نمی‌کند** (12 پروژه بررسی شد) — نیچ MiniAndroid تأیید؛ نزدیک‌ترین قالب: Robolectric architecture + RNG/Paparazzi render.
10. **F017/N9 (Makefile header deps) قبلاً روی HEAD fixed است** — `(-MMD -MP)` موجود؛ یافته باز قدیمی بسته شد.

# TOP 10 ACTIONS FOR PRIMARY

1. `git am 0001-UC-CM-001-….patch` (ضمن‌شده؛ صفر رگرسیون روی v12).
2. FontBackend: FreeType+HarfBuzz+FriBidi با FIRSTSTRONG — کد POC آماده کپی (`scripts/wsc2_text_pipeline.cpp`).
3. پیاده‌سازی `android.net.Uri` bridge (parse/Builder/queryParameter/normalizeScheme) — مرجع: AOSP Uri.java.
4. SystemClock با `clock_gettime(CLOCK_MONOTONIC/BOOTTIME)` + کلید deterministic-clock.
5. تولید خودکار string/raw resource map از ARSC (حذف وابستگی به resource_values.json دستی) — SFS-010 و RLottie-v12 را با هم می‌بندد.
6. SQLite amalgamation → DatabaseBackend + contract tests (§10) — بزرگ‌ترین باز corpus.
7. benchmark libdeflate روی load تلگرام؛ در صورت برد، adapter با fallback zlib.
8. `SERVICE_INTERCEPTION_MAP.md` بسازید (فهرست خوشه‌های proxy از VirtualApp/Evoke/Robolectric) — نقشه هدفمند F007/F010.
9. Environment simulation: clock کنترل‌پذیر + reset-state بین اجراها (الگوی @Resetter) — determinism ساختاری.
10. Registry کامل 100+ corpus را در repo بریزید (JSON/CSV در `tests/corpus/results/`) — ادعای فعلی از clone قابل راستی‌آزمایی نیست.

# TOP 10 THINGS NOT TO IMPLEMENT

1. KVM/container مسیرها (redroid/cuttlefish/Waydroid) — خارج از mission هدلس.
2. Chromium/Servo embed (WebView) — بدون evidence ممنوع (§8)؛ WPE فقط DEFER.
3. F012-AMPLIFIER (branch ادغام‌نشده ab48fbc) — UC-CM-001 هدف را با ریسک کمتر بست.
4. بازنویسی decoders اثبات‌شده (PNG/WebP/JPEG/RLottie).
5. fdk-aac (لایسنس شرطی) و Unicorn in-process (GPL).
6. RapidJSON/LevelDB/RocksDB/DuckDB/Cronet/Cairo/Pango/NanoVG (ریجکت matrix).
7. جایگزینی کامل BitmapFont قبل از آماده شدن FontBackend (fallback لازم).
8. Telegram-specific mapping در core (همه mapping ها باید generic از ARSC).
9. Rust migration زودهنگام (§ priority 10 charter دوم).
10. Google Play Services وسیع — فقط census (§31).

# CURRENT BLOCKERS

- PUSH_PENDING — credential push در sandbox نیست.
- RLottie render روی v12: نیاز R$raw map (با action 5 حل می‌شود).
- Corpus 100+: registry خارج از clone — UNKNOWN طبق §18.
- non-Telegram regression این کمپین: NOT RUN (دانلود corpus انجام نشد) — طبق §18 ثبت شد.
- ASAN این کمپین: NOT RUN (تغییر فقط value-mapping بود؛ بازبینی انجام شد).

# HIGHEST-VALUE SOURCES

- AOSP: `TextDirectionHeuristics`, `Uri.java`, minikin `Layout` (shape-per-run)
- Robolectric: `AndroidTestEnvironment`, `@Resetter`, `SQLiteMode.NATIVE` (nativeruntime)
- Paparazzi/Roborazzi: capture-at-canvas + diff engines (PixelPerfect/MSSIM/ΔE2000)
- VirtualApp proxies/ + Evoke (0BSD): نقشه service interception
- dexlib2: cross-check پارسر DEX
- matrix ابزار: `WS-C4_TOOL_MATRIX.md` (ده کاندید برتر)

# REAL APK PROOF

| APK | SHA256 (prefix) | نتیجه |
|---|---|---|
| Telegram 12.10.1 vc70389 | `f5e1192725…` | exit=0 · 12,544 کلاس · 41,233px · 3/3 deterministic · قبل/بعد UC-CM-001 یکسان |

# BACKEND RECOMMENDATIONS

| Backend | انتخاب اول | جایگزین | منبع |
|---|---|---|---|
| Font | FreeType+HarfBuzz+FriBidi (اثبات‌شده) | BitmapFont fallback | WS-C2 |
| Image | libpng+libjpeg-turbo+libwebp (موجود) + Wuffs long-tail | stb_image decode-only | WS-C4 |
| Animation | rlottie (موجود) | ThorVG v1.0 (DEFER) | WS-C4 |
| Database | SQLite amalgamation | SQLCipher (DEFER) | WS-C4 |
| Network | libcurl+OpenSSL/mbedTLS | nghttp2 داخلی curl | WS-C4 |
| Archive | zlib (موجود) + libdeflate (hot path) + zstd/lz4 | — | WS-C4 |
| Audio | miniaudio (decode→PCM deterministic) | libFLAC/opus/vorbis/mpg123 مستقیم | WS-C4 |
| Video | FFmpeg-trim (oracle→adapter) | dav1d/libvpx per-codec | WS-C4 |

# REGRESSION RISKS

1. UC-CM-001 مقادیر STUBBED را تغییر می‌دهد → اپ‌هایی که «اتفاقاً» با void کار می‌کردند ممکن است مسیر دیگری بروند (مثلاً if-nez حالا false می‌بیند به‌جای stale). **کمپین فعلی: صفر رگرسیون؛ ولی corpus کامل بعد از merge re-run شود.**
2. FontBackend جدید → خروجی تصویری همه صفحه‌ها عوض می‌شود؛ baseline های PNG/SHA باید re-baseline شوند.
3. resource-map خودکار از ARSC → ممکن است با mapping دستی فعلی در چند مورد فرق کند؛ OX gate بعدش الزامی.
4. libdeflate → خروجی byte-level ممکن است متفاوت (فقط سرعت باید فرق کند؛ CRC gate نگه دارید).

# CONFIDENCE

| موضوع | اطمینان | دلیل |
|---|---|---|
| UC-CM-001 بی‌رگرسیون | HIGH | 3/3 SHA + trace count برابر + منطق fallback |
| absent بودن Uri/SystemClock | HIGH | grep کل src (دو روش) |
| typography POC | HIGH | تصویر + metrics JSON + نسخه libs |
| matrix ابزار | MED-HIGH | تحقیق وب mid-2026؛ 3 مورد UNVERIFIED علامت خورده |
| WS-C5 جمع‌بندی | HIGH | 12 پروژه با منبع؛ موارد نامطمئن علامت‌گذاری |
| forward-compat v12 | HIGH | اجرای واقعی deterministic |

---

# پیوست: فهرست تحویلی‌ها (این پک)

| فایل | محتوا |
|---|---|
| `SOURCE_CHANGES.md` | **تغییرات سورس + توضیحات کامل برای اعمال آینده** (خواسته شما) |
| `0001-UC-CM-001-….patch` | patch قابل `git am` |
| `WS-C2_KNOWLEDGE.md` / `_PRIMARY_TRANSFER.md` / `_EVIDENCE.md` | گرافیک/متن/انیمیشن |
| `WS-C3_KNOWLEDGE.md` / `_PRIMARY_TRANSFER.md` / `_CORPUS.md` | فریمورک/corpus |
| `WS-C4_TOOL_MATRIX.md` / `_PRIMARY_TRANSFER.md` / `_TO_C2_C3.md` | ابزارها |
| `MINIANDROID_EXTERNAL_RUNTIME_KNOWLEDGE.md` / `_INDEX.md` / `WS-C5_PRIMARY_TRANSFER.md` | رانتایم‌های خارجی |
| `CROSS_WORKSTREAM_TRANSFERS.md` | انتقال‌ها + CROSS_CODER_RECONCILIATION |
| `SOURCE_REFERENCE_INDEX_UPDATE.md` | append به SOURCE_REFERENCE_INDEX |
| `wsc2_text_pipeline.cpp` + تصاویر | POC تایپوگرافی + evidence |
| `uc_v12_top.png` و پیش‌نمایش‌ها | شواهد بصری v12 |

محل پیشنهادی commit در repo:
- اسناد WS → `miniandroid/docs/knowledge/`
- `SOURCE_CHANGES.md` → ریشه repo
- POC → `miniandroid/scripts/`، evidence تصاویر → `run/` (یا `docs/knowledge/assets/`)
