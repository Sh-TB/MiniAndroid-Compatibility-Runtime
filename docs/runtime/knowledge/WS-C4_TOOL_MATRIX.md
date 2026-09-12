# WS-C4 TOOL MATRIX — ماتریس ابزارهای متن‌باز (ادغام تحقیق WS-C4-RESEARCH)

**تاریخ:** 2026-08-27 · وضعیت پژوهش: وب‌جستجو (پنجره mid-2026) · موارد نامطمئن: UNVERIFIED
**واحدهای adoption:** USE / ADAPT / ORACLE-ONLY / REFERENCE / DEFER / REJECT
**وضعیت فعلی لینک‌شده در runtime:** zlib، libwebp+libwebpdemux، libjpeg، rlottie (static)، nlohmann/json

## GRAPHICS

| name | license | latest | build | C API | maintenance | size | relevance | class |
|---|---|---|---|---|---|---|---|---|
| Skia | BSD-3+patent | M144 (2025-12) | GN/Ninja | ❌ (C++) | very active | 30–70MB | med | **REFERENCE** |
| Blend2D | zlib | 2025-03 | CMake+asmjit | ✅ | active | 3–5MB | med | DEFER |
| ThorVG | MIT | v1.0 (2026-01) | CMake/Meson | ✅ | very active | 0.5–1.5MB | med | **DEFER** (جانشین rlottie) |
| NanoVG | zlib | تعطیل | — | ✅ | dead | ~0.3MB | none | **REJECT** |
| Cairo | LGPL/MPL | 1.18.4 (2025-03) | Meson | ✅ | slow | 3–6MB | low | REJECT |
| Pango | LGPL | 1.56.x | Meson | ✅ | active | 5–10MB | low | REJECT |

## GPU / SW-RASTER

| name | license | C API | size | class | یادداشت |
|---|---|---|---|---|---|
| ANGLE+SwiftShader | BSD/Apache | EGL/GLES | 30–60MB | **DEFER** | تنها مسیر معتبر GLES؛ بعد از وجود GLES workstream |
| Mesa llvmpipe | MIT | GL | بزرگ | REJECT | وابستگی سنگین LLVM |
| lavapipe | MIT | Vulkan | بزرگ | DEFER | |
| Zink | MIT | GL-on-Vulkan | — | REJECT | overhead روی CPU |

## IMAGE

| name | license | latest | class | یادداشت |
|---|---|---|---|---|
| stb_image | Public domain | 2.30 (2023) | **USE** (long-tail) | تک‌فایل؛ BMP/GIF/TGA؛ برای PNG/JPEG سریع‌تر: libpng/libjpeg-turbo اصلی بمانند |
| libpng | zlib | — | (موجود/مسیر فعلی) | PNG write لازم |
| libjpeg-turbo | BSD-3 | — | (موجود) | |
| libwebp | BSD | 1.6.0 (2025-06) | (موجود) **USE** | demux هم لینک است |
| Wuffs | Apache-2.0 | 0.4.0-alpha.10 | **USE** | decode امن memory-safe (GIF/NIE) |
| OpenJPEG | BSD-2 | 2.5.4 (2025-09) | DEFER | JPEG2000 نادر |
| libavif | BSD-2 | 1.3/1.4 (2025/26) | DEFER | AVIF رو به رشد |
| libheif | LGPL-3 | 1.20.2 | DEFER | HEVC patent/x265 GPL ریسک |
| libjxl | BSD-3 | 0.11.1 | DEFER | 5–15MB |
| APNG | — | — | **ADAPT** | acTL/fcTL روی libpng/Wuffs؛ lib مستقل سالم نیست |

## ANIMATION — rlottie (موجود، USE) · animated-WebP از libwebpdemux (موجود، frame iteration باقی مانده — CM-027 future)

## AUDIO

| name | license | latest | class |
|---|---|---|---|
| miniaudio | PD/MIT | 0.11.25 | **USE** (تک‌فایل؛ playback+device) |
| Oboe | Apache | — | REJECT (Android-only) |
| PortAudio | MIT | 2019 dormant | REJECT |
| OpenAL Soft | LGPL | 1.25.2 | DEFER |
| libopus | BSD | 1.6.1 (2026-01) | USE |
| libvorbis | BSD | 1.3.7 | USE |
| libFLAC | BSD | 1.5.0 | USE (اثبات bit-exact قبلی Coder4) |
| libmpg123 | LGPL | 1.33.x | USE |
| fdk-aac | Fraunhofer شرطی | — | **REJECT** (لایسنس+C++ API؛ FFmpeg AAC کافی) |
| FFmpeg (audio) | LGPL-2.1+ | 8.0 (2025-08) | ADAPT (trim) |

## VIDEO

| name | license | latest | class |
|---|---|---|---|
| FFmpeg | LGPL-2.1+ | 8.0 | **ADAPT** — مسیر اصلی decode→frame→Bitmap |
| GStreamer | LGPL | — | REJECT (فریم‌ورک 50MB+) |
| dav1d | BSD-2 | 1.5.2 (2025-11) | DEFER (AV1) |
| openh264 | BSD | 2.6.x | DEFER (patent pledge فقط باینری Cisco) |
| libvpx | BSD | 1.15.1 (2025-01) | DEFER |
| libaom | BSD | 3.12.x | ORACLE-ONLY (کند) |
| Media3/ExoPlayer | Apache | — | REJECT (JVM/Android) |

## NETWORK

| name | license | latest | class |
|---|---|---|---|
| OkHttp | Apache | — | REJECT به‌عنوان lib لینک‌شده (JVM؛ داخل APK ها خودش اجرا می‌شود) |
| libcurl | curl | 8.14.0 (2025-05) | **USE** (NetworkBackend اول) |
| Cronet | Apache | — | REJECT (Chromium stack) |
| nghttp2 | MIT | 1.68.0 | USE (معمولاً از طریق curl) |
| OpenSSL | Apache-2.0 | 3.5 LTS | USE |
| mbedTLS | Apache | 3.6 LTS | USE (جایگزین کوچک) |
| BoringSSL | — | بدون versioning | DEFER |

## DATABASE

| name | license | latest | size | class |
|---|---|---|---|---|
| SQLite | Public domain | 3.50.x (2025) | ~1.5MB | **USE — حیاتی** (11/11+ اثبات Coder4؛ Precedent: Robolectric nativeruntime هم SQLite واقعی bundle می‌کند) |
| SQLCipher | BSD | 4.10.0 (2025-08) | — | DEFER |
| LMDB | OpenLDAP | 1.0.0 (2026) | ~0.1MB | DEFER |
| LevelDB | BSD | 1.23 (2021) | — | REJECT (نگهداری محدود، self-declared) |
| RocksDB | GPLv2/Apache | 11.x | 10–25MB | REJECT |
| DuckDB | MIT | 1.4/1.5 | 40–80MB | REJECT |

## SERIALIZATION

| name | license | latest | class |
|---|---|---|---|
| protobuf | BSD | 31.x | DEFER (abseil dep) |
| FlatBuffers | Apache | 25.12.19 | DEFER |
| MessagePack (libmpack) | MIT | — | DEFER |
| tinycbor | MIT | 0.6.1→7.0 | DEFER |
| RapidJSON | MIT | 1.1.0 (2016!) | **REJECT** (فریز؛ nlohmann موجود) |
| simdjson | Apache | 4.0 | DEFER |

## ARCHIVES

| name | license | latest | class |
|---|---|---|---|
| zstd | BSD | 1.5.7 | **USE** (APK های آینده/alignment) |
| lz4 | BSD | 1.10.0 | USE (ART/odex) |
| bzip2 | BSD | 1.0.8 (2019) | DEFER |
| miniz | MIT | — | REJECT (zlib هست) |
| libarchive | BSD | 3.8.x | DEFER |
| **libdeflate** | MIT | 1.24 (2025-05) | **USE — بالاترین ارزش/حجم** (inflate سریع APK، ~0.1MB) |

## APK/DEX TOOLING — همه **ORACLE-ONLY** (هرگز لینک نمی‌شوند)
AAPT2 (AOSP binary) · apktool 2.10.x/v3.x (Apache) · baksmali/smali (dexlib2 3.0.x — Google) · JADX 1.5.6 (2026) · Androguard (Python) · bundletool 1.18.3 · APKEditor V1.4.8 (license UNVERIFIED) · enjarify (archived 2022 — REJECT)
+ **dexlib2 = مدل مرجع battle-tested فرمت DEX برای cross-check پارسر خودمان** (تجربه AppManager).

## JNI/NATIVE

| name | license | latest | class |
|---|---|---|---|
| libffi | MIT | 3.4.6→3.8.0 (2026-08) | **USE** (وقتی JNI واقعی شروع شد) |
| Capstone | BSD-3 | 5.0.x/6.0-alpha | DEFER (disassembler امن) |
| Unicorn | GPL | 2.1.4 | **ORACLE-ONLY** (GPL؛ هرگز in-process) |
| LIEF | Apache-2.0 | 0.17.1 (2025-10) | DEFER (ELF) |
| libdwarf | LGPL | 0.10–0.12 | DEFER |

## TEXT (POC این کمپین — WS-C2)

| name | license | sandbox | class |
|---|---|---|---|
| FreeType | FTL/GPL | 2.13.3 (بالا: 2.14.1 موجود) | **USE** (bump پیشنهادی) |
| HarfBuzz | Old-MIT | 10.2.0 (بالا: 14.4.0) | **USE** |
| FriBidi | LGPL | 1.0.16 | **USE** |
| SheenBidi | Apache-2.0 | 2.9.0/3.0.0 (2026-01) | USE (جایگزین permissive FriBidi در آینده) |

## WEBVIEW — Chromium embed (~150MB+) REJECT/DEFER · Servo (MPL, Rust) DEFER · **WPE WebKit** DEFER (کاربردنی‌ترین مسیر headless CPU-only)

---

## NOTABLE FINDINGS (خلاصه)

1. Robolectric خودش SQLite واقعی native bundle می‌کند → precednet مستقیم برای SQLite amalgamation.
2. **libdeflate**: بیشترین ارزش به‌ازای هر کیلوبایت (inflate سریع APK).
3. **ThorVG v1.0** جانشین بالقوه MIT/C-API برای rlottie — فعلاً DEFER.
4. fdk-aac نگیرید (لایسنس شرطی) — FFmpeg AAC کافی است.
5. Unicorn فقط به‌عنوان ORACLE خارج از process (GPL).
6. RapidJSON (2016) و LevelDB (نگهداری محدود) نگیرید.
7. Zink روی CPU نه — llvmpipe هم به‌خاطر LLVM رد.
8. Skia: بدون C API پایدار → فقط REFERENCE برای semantics پالت Canvas.
9. **ده کاندید برتر:** SQLite، libdeflate، miniaudio، FFmpeg-trim، libcurl+TLS، Wuffs، libffi، SheenBidi، zstd+lz4، ThorVG.
10. ANGLE+SwiftShader تنها مسیر GLES معتبر — تا ساخت workstream GLES ب defers.

## پاسخ سوالات خاص

- **A) stb_image:** v2.30، Public domain. فقط برای decode-only تک‌فایلی و قالب‌های دنباله‌بلند بهتر از جفت libpng/libjpeg؛ در سرعت SIMD و robustness و PNG-write بازنده است.
- **B) Robolectric native SQLite:** بله — `SQLiteMode.NATIVE` با `libnativeruntime.so` شامل libsqlite واقعی AOSP-deriv + ICU؛ دقیقاً الگوی «کتابخانه واقعی به‌صورت resource → dlopen» برای MiniAndroid.
- **C) C-API تمیز:** اکثریت (~40) C API دارند؛ C++-ABI خطرناک‌ها: Skia، LevelDB، RocksDB، protobuf/FlatBuffers/simdjson/RapidJSON، لایه C++ LIEF → isolation لازم.
