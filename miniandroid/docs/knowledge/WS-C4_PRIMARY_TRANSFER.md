# WS-C4 PRIMARY TRANSFER

**به:** Primary Coder · **از:** WS-C4 · **تاریخ:** 2026-08-27

## ADOPTION DECISIONS (با SOURCE/EVIDENCE/CONFIDENCE/BENEFIT/RISK/ACTION)

### D1 — SQLite amalgamation → DatabaseBackend (بالاترین اولویت)
- SOURCE: sqlite.org 3.50.x, Public domain · EVIDENCE: اثبات قبلی Coder4 (11/11+) + precedent Robolectric nativeruntime
- CONFIDENCE HIGH · BENEFIT: بخش بزرگی از corpus (DB APks) باز می‌شود · RISK: LOW (فایل واحد C)
- ACTION: adapter در `DatabaseBackend` + contract tests (open/query/transaction/rollback/persistence). **داخلی SQLite را بازنویسی نکنید.**

### D2 — libdeflate → مسیر inflate داخلی ZIP/APK
- SOURCE: github.com/ebiggers/libdeflate 1.24 MIT · CONFIDENCE HIGH
- BENEFIT: سرعت load روی APK های بزرگ (تلگرام 73–83MB) · RISK: LOW (fallback zlib)
- ACTION: benchmark قبل/بعد روی همان APK v12؛ نگه داشتن zlib به‌عنوان fallback.

### D3 — miniaudio → AudioBackend (مرحله decode→PCM deterministic)
- SOURCE: github.com/mackron/miniaudio 0.11.25 PD/MIT · CONFIDENCE HIGH · RISK: LOW
- ACTION: اول فقط decode→PCM buffer (بدون device)؛ هدف §22: خروجی مجازی قطعی.

### D4 — FFmpeg-trim → VideoBackend/سخت‌افزار audio تکمیلی
- SOURCE: ffmpeg.org 8.0 LGPL-2.1+ · CONFIDENCE HIGH · RISK: MED (اندازه باینری؛ license: dynamic-link LGPL کافی)
- ACTION: oracle اول (compare با evidence های H264/VP9/AV1/MJPEG قبلی Coder4)، بعد adapter.

### D5 — libcurl(+OpenSSL/mbedTLS) → NetworkBackend
- SOURCE: curl.se 8.14.0 · اثبات قبلی Coder4: OkHttp 5/5، libcurl 6/6
- ACTION: shared network contract tests (HTTP/HTTPS/redirect/gzip/timeout) — §10 charter.

### D6 — FreeType+HarfBuzz+FriBidi (همین حالا اثبات شد — WS-C2)
- ارجاع به `WS-C2_PRIMARY_TRANSFER.md` T1. SheenBidi جایگزین permissive بعدی است.

## CODE REDUCTION LEDGER (§25 — اهداف کاهنده کد)
| جایگزین | کد فعلی که حذف/کوچک می‌شود |
|---|---|
| SQLite | کد db دست‌ساز فعلی/آینده (~هزاران LOC اجتناب‌شده) |
| libdeflate | inflate دستی بخش‌های hot (بخشی از apk_parser) |
| miniaudio | — (چیزی نبود که حذف شود؛ جلوگیری از نوشتن mixer/decode دستی) |
| ThorVG (DEFER) | هیچ — تا rlottie نیاز به تعویض شد |

## REJECTED (باید PRIMARY هم بداند — §21)
NanoVG (مرده)، Cairo/Pango (وابستگی سنگین/کم‌ارزش)، LevelDB/RocksDB/DuckDB (نگهداری/حجم)، Oboe/PortAudio (پلتفرمی/راکد)، fdk-aac (لایسنس)، Media3/OkHttp/Cronet (JVM/Chromium)، Unicorn in-process (GPL)، RapidJSON (فریز 2016)، llvmpipe (LLVM)، Zink (overhead)، enjarify (archived)。

## VERIFY AT ADOPTION TIME (UNVERIFIED در تحقیق)
apktool v3.x وضعیت · APKEditor license · mbedTLS 4.x rollout.
