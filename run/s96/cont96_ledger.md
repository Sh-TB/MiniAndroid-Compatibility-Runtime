# CONT-96 RESULT — #364: پیشرفت تلگرام گزارش شد · ریشه‌ی جدید F-NEW-398 (halt کاذب F084 در حلقه‌های دارای invoke) رفع شد · بهداشت داغ مفسر با صفر drift

**Wave:** CONT-96 · **directive:** «ادامه اصلا پیشرفتی داشتی تو ۳۶۴ تلگرام چطور ادامه بده تا ۳۶۴ کامل تموم بشه» · **HEAD:** `3f032f46` → `89c10a65` · **binary:** `aa9ade61b147c12b` → `79d93a6ada630e73` · **registry:** 704 → 708 روت

---

## ۰. استخراج درخواست‌ها (۵۶ کامنت — استخراج → نمایش → لیست کاری → اجرا)

بعد از ledger CONT-95 (کامنت `6247425386`) **هیچ درخواست جدیدی نیامده.** بک‌لاگ باز همان CONT-87..93 + residualهای نام‌گذاری‌شده است. **لیست کاری تلگرام-اول:** R1=T3 bounds/offset · R2=T4 RecyclerView · R3=T6 string-resource (LOC_ERR) · R4=boot boundaries · R5=صفحات ۲..۷ · R6=CONT-90 · R7=CONT-93 · R8=CONT-87 tracks. **این موج P0 تلگرام را برداشت:** residual THROUGHPUT نام‌گذاری‌شده‌ی CONT-95 (پارس SVG ۵۰۷KB = ۱۲.۶M+ دستورالعمل مفسر، قطع با F084 budget wall-stop در گیت ۳۰-ثانیه‌ای).

## ۱. پاسخ مستقیم به سوال «اصلا پیشرفتی داشتی؟» — بله، با عدد

- CONT-94: اولین پیکسل‌های واقعی اپ-دار تلگرام/فورکگرام (F-NEW-396 — هویت activity).
- CONT-95: مرگ بوت Night-theme حذف شد (F-NEW-397 — قانون واقعی SAX؛ `parse OK: 746 elements -> SvgHelper$SVGHandler` با ۴.۷M فراخوانی API کار واقعی DEX خود اپ)؛ بوت به onResume می‌رسد؛ ۶ uncaught (فقط مرزهای billing/native/firebase)؛ ۰ WALL-STOP در ۲۴۰ ثانیه.
- **این موج (CONT-96):** نرخ دستورالعمل در گیت ۳۰-ثانیه **۳۴۱K → ۴۲۳K ins/s (+24%)** + یک ریشه‌ی جدید P0 (F-NEW-398) کشف/اثبات/رفع شد + بهداشت داغ مفسر با صفر drift.

## ۲. کشف موج — F-NEW-398: halt کاذب F084 در **هر حلقه‌ای که بدنه‌اش invoke دارد**

**fixture-first دوباره برنده بود.** Probe جدید `com.probe.perf1` (apk `8cbe1d87b7a68cff`، toolchain واقعی aapt2/ECJ/D8) یک حلقه‌ی `sum += ident(k)` ساخت: `[F084] "Infinite loop at PC=0x3 ... visited 50001 times"` — ولی **[SPIN-REGS] v2=50000: شمارنده‌ی حلقه هر بازدید جلو رفته بود.** اثبات نهایی: امضای شاخه‌ی F084 بر اساس **مقادیر رجیستر** است؛ اگر k جلو می‌رفت و epoch bump نمی‌شد،机制 خراب است — decode کردیم:

- قانون frame-entry هر چهار عضو F084 را در ورود هر متد پاک می‌کند (`pc_visit_count_`, `pc_branch_sig_`, `frame_progress_epoch_`, `pc_epoch_checkpoint_`).
- `try_recursive_invoke` فقط `pc_visit_count_` را save/restore می‌کرد (مجموعه‌ی EXP-052 قدیمی‌تر از قانون امضاست).
- پس بعد از هر return، نقشه‌ی امضای صدا-zننده **خالی** بود → بازدید بعدی امضا را «اولین بازدید» می‌نوشت → epoch تا ابد ۰ → بازدید ۵۰۰۰۱ = «stall» کاذب.

**هر حلقه‌ی واقعی هر اپی که بدنه‌اش متد صدا می‌زند (یعنی عملاً هر حلقه‌ی واقعی) در معرض این مرگ بود** — همان شکل فریم `SvgHelper$ParserHelper.advance`.

## ۳. فیکس + بهداشت داغ (همه با صفر تغییر معنا)

| قانون | محتوا |
|---|---|
| **F-NEW-398** | save/restore کامل مجموعه F084 در `try_recursive_invoke` |
| **W3-A** | وضعیت per-pc از `std::map` → **وکتور flat** (per-instruction find/insert گره قرمز-سیاه حذف؛ save/restore از **کپی کامل نقشه به‌ازای هر invoke** → swap) با seen-flag معادل قانون insert-vs-compare |
| **W3-B** | memo `(dex, method_idx) → {name, class, proto, params parsed}` — MUTF-8 decode و parse proto به‌ازای هر متد **یک‌بار** (قبلاً ۳-۴ materialization رشته per invoke)؛ نسخه‌های uncached بایت-یکسان فقط برای fill |
| **W1** | ۶۰ سایت `getenv` در مسیر داغ → کش `diag_env` با هویت pointer literal (شامل macro `ARITH_2ADDR` که **به‌ازای هر عمل حسابی** environ walk می‌کرد) |
| **W2** | ۱۰ چاپ debug همیشه-روشن با گارد `string::find` per-invoke → env-gated (EXP058/061/062/079/081/082/088)؛ سایت‌های find **رفتاری** دست‌نخورده |

## ۴. اثبات — fixture A/B با checksumهای اثبات‌شده

| ردیف [PERF1] | قبل `aa9ade61b147c12b` | بعد `79d93a6ada630e73` |
|---|---|---|
| charat (۲۱۶K تکرار) | ۲۵۶۳ms، sum=3688000 ✓ | ۲۶۹۰ms، sum=3688000 ✓ |
| chararray | ۴۹۱ms، sum=31744000 ✓ | ۴۳۸ms، sum=31744000 ✓ |
| **virtual (۳۰۰K invoke)** | **هرگز تمام نشد — halt کاذب F084** ❌ | **۳۳۴۰ms، sum=14534196240 ✓** |
| کل | قطع در >۱۲۰ ثانیه (۲/۴ ردیف) | **۶۴۷۴ms، verdict=DONE rows=4** ✅، HALT-LOOP=۰ |

checksums با معناشناسی host-Java بایت-یکسان. تلگرام گیت ۳۰ ثانیه: نرخ +24%.

## ۵. رگرسیون — صفر drift روی `79d93a6ada630e73`

**wall 12/12 MATCH** (dooz `31ddd4d5b8e6d18e` ×3، opencalc `f25b754c4565c38b` ×3، unote `90a67cc1ddda57b7` ×3، microtimer `bbd350b6c14fbd52` ×3) · **goldens 4/4** · **negatives 19/19** (gate-A probe بازسازی‌شده: **۹۸ PASS / ۱ INFO / ۰ FAIL** — مجموعه‌ی verdict بایت-یکسان با ثبت) · **reinstall 8/8** · **MG-310 7/7** · **MG-150 3/3** · **selftests 13/13** · **F-NEW-376 70/70** (ردیف‌های c72priv داخلش) · sax1 **events=6/6 PASS** · clock1 **4/4** · clinit1 ردیف‌ها law-correct (UT2 NCDFE) · swipe1 setup OK · c74esc containment OK · perf1 4/4.

## ۶. باقی‌مانده‌های نام‌گذاری‌شده (صداقت)

1. **گیت ۳۰-ثانیه‌ی تلگرام هنوز با F084 budget wall-stop قطع می‌شود** (۱۰۲۴ ردیف deferred). چهره‌ی فاز-کلاک این موج: **`bridge_to_api` ≈۴۸.۶µs به‌ازای هر فراخوانی × ۷۰۲K فراخوانی** (زنجیره‌ی dispatch رشته‌ای) + ~۰.۴۵µs resolve فیلد per-op. این **فرانتیر معماری** است (ART معادلش intrinsics/fast-path dispatch است) — **ادعا نشد که این موج بست؛ چهره‌ی مشخص + harness قطعی (ردیف‌های perf1) تحویل شد.** موج بعد: جدول dispatch/intrinsic fast-path.
2. T3 (bounds/offset)، T6 (LOC_ERR)، R2/R5..R8 تغییر نکردند — باز.
3. resync محیط (بار چهارم): snapshot محلی CONT-10-era بود؛ reset به `3f032f46` و بازسازی بایت-یکسان قبل از هر تغییر؛ probe storeها طبق `closeout_baseline.sh` بازپر شدند.

## ۷. پرسنتاژ

- **این موج: ۱ ریشه‌ی P0 جدید کامل (کشف → decode → فیکس → fixture A/B + checksum → باتری کامل) = ۱۰۰٪ تایید · ۴ قانون infra با اثبات A/B = تایید · ۰ مورد رد.**
- رگرسیون ۱۳/۱۳ گیت سبز صفر-drift = ۱۰۰٪.
- **آمار تجمیعی بک‌لاگ ۳۶۴ (بعد از این موج):** CONT-87 Track 1 ✓ · Track 2..10 باز · CONT-88 T3/T4/T6 باز · CONT-89 صفحه ۱ partial، ۲..۷ باز · CONT-90 باز · CONT-91 حکم NOT_AVAILABLE بسته، بقیه باز · CONT-92/93 باز · **+ F-NEW-398 این موج بسته شد.**

fixtures: `fixtures/cont96_perf_probe` · scripts: `cont96_build_probe.sh`، `cont96_decode_benchvirtual.py`، `cont96_hotpath_cleanup.py`، `cont96_apply_edits.py`، `cont96_battery.sh`، `cont96_registry_update.py` · evidence: `evidence/cont96/` · runs: `run/cont96/`
