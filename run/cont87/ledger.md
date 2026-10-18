# CONT-87 RESULT — #364: ۷ درخواست جدید خوانده شد · Track 1 (F-NEW-395) با A/B کامل بسته شد · لیست کاری به‌روزشده با تایید/رد تک‌تک

**Wave:** CONT-87 · **HEAD:** `fee659ab` (روی `5ca26fa3` = CONT-86) · **binary sha256-16:** `caa24290aad77ca9` · **registry:** 702 روت، sha16 `76e52c8d9d991ad9` · validator **ALL PASS**

---

## ۰. تازگی محیط (صادقانه)
کانتینر در شروع این موج reset شده بود (checkout محلی از era CONT-10 بود). قبل از هر حکمی: fast-forward به origin/main، باینری + gate_a_probe + probe_store از سورس‌های git-tracked بازسازی شد. هیچ حکمی روی وضعیت کهنه صادر نشده است.

## ۱. درخواست‌های جدید #364 (بعد از ledger CONT-86، کامنت 6243553102) — ۷ directive
| # | کامنت | عنوان |
|---|-------|-------|
| 1 | 6245430786 | **CONT-87** — ده فیکس execution-first از residual ledger واقعی CONT-86 (ترک ۱: F-NEW-395 P0؛ ترک ۲: GLSL؛ ترک ۳: throughput؛ ترک ۴: Compose first-frame؛ ترک ۵: F-145؛ ترک ۶-۱۰: شرطی به evidence) |
| 2 | 6245477077 | **CONT-88** — REAL APP EXECUTION CAMPAIGN: Telegram هدف end-to-end؛ WhatsApp-family parity؛ ≥۴ تلاش فیکس؛ ≥۸ APK |
| 3 | 6245481160 | **CONT-89** — TELEGRAM UI FORENSIC COMPLETION (نردبان ۷-صفحه‌ای + اثبات سه‌اجرته) |
| 4 | 6245481420 | **CONT-90** — WHITE GAME/APP RECOVERY BATCH (۵ اپ سفید نام‌برده + ۵ هدف دیگر) |
| 5 | 6245481662 | **CONT-91** — WHATSAPP/MESSAGING FAMILY PARITY (اول حکم آرتیفکت؛ Signal کنترل) |
| 6 | 6245501827 | **CONT-92** — TELEGRAM SOURCE-GROUNDED ADDENDUM (نقشه source→runtime؛ سفر واقعی؛ ۱۲ لاین ممیزی) |
| 7 | 6245531086 | **CONT-93** — TEN-GAME EXECUTION MATRIX (حرکت/action/strategy/farm/3D) |

## ۲. Track 1 (F-NEW-395 P0) — اجرا شد؛ حکم دو-بخشیِ صادقانه

### بخش الف — ادعای ثبت‌شده‌ی «handler-match» با شواهد **رد می‌شود**
- **decode واقعی** (androguard، `scripts/cont87_decode_luu.py`، APK `org.andstatus.game2048_47` sha16 `2d6707624623fe88`): try در `Luu;.<clinit>` فقط code-units **7..12** را می‌پوشاند (ناحیه‌ی `getMethod("onSpinWait")`)؛ فراخوانی `forName` در unit **2** است — **بیرون از try**. پس verdict موتور («uncaught» در pc=2) طبق semantics درستِ DEX بود؛ ریشه‌ی ثبت‌شده در CONT-86 یک decode اشتباه بود.
- **fixture** `com.probe.clinit1` (sha16 `d0de76b819c1f725`) ثابت کرد catch-all درون‌فریمی برای **هر دو** منبع raise درست dispatch می‌شود: CNFE→`deferred handler @0x14`، ARITH→`@0x15`.
- روی دستگاه واقعی هیچ‌وقت به این پوشش وابسته نبود — forName برای کلاس framework هرگز throw نمی‌کند (پل F-NEW-394 همان قانون را در CONT-86 برگرداند).

### بخش ب — نقص صداقتی ثبت‌شده **تأیید و رفع شد** (fixture قبل از فیکس fail، بعد از فیکس pass)
| ردیف fixture | قبل (`d22b36be55764348`) | بعد (`caa24290aad77ca9`) | قانون |
|---|---|---|---|
| C87-CC (forName در catch درون-clinit) | caught:CNFE ✅ | caught:CNFE ✅ (بدون تغییر) | catch درون‌فریمی |
| C87-AC (10/0 در catch درون-clinit) | caught:AE ✅ | caught:AE ✅ (بدون تغییر) | همان قانون |
| C87-UT (استفاده‌ی اول از کلاسِ throw-کرده) | AE خام به caller | AE خام به caller ✅ (رفتار app-visible حفظ شد) | استثنای اصلی در handler پوشاننده |
| C87-UT2 (استفاده‌ی دوم) | **s=42 — clinit دوباره اجرا شد!** | **NoClassDefFoundError** ✅ | JVMS 5.5 erroneous |
| [CLASS_INIT] ClinitThrow | **result=OK با وجود throw** | **result=FAILED + F-NEW-215 erroneous** ✅ | صداقت state machine |

**ریشه‌ی واقعی:** `halted_on_return_` هم برای return معمولی ست می‌شود هم برای unwind — بنابراین finalize گزارش `COMPLETED_SUCCESS` برای clinitِ unwound می‌داد؛ کلاس poison-marked INITIALIZED می‌ماند و استثنای خام به invoke-site «بعدها» teleport می‌شد (همان CNFE داخل MyMainActivity.onCreate).

**فیکس (عمومی، ۳ سایت، بدون شرط package):**
1. finalize: unwind ⇒ `COMPLETED_PARTIAL` + `halt_reason="unwind <type>"`؛ SUCCESS مارکرهای stale را پاک می‌کند.
2. سایت فراخوانی clinit مارکر را می‌خواند و کلاس را به مسیر ثبت‌شده‌ی F-NEW-215 می‌برد.
3. گارد `clinit_exc_already_in_flight()` در ۶ سایت active-use (sget/sget-object/sput/sput-object/new-instance/forName) — استفاده‌ی trigger-کننده استثنای خود clinit را تحویل می‌گیرد؛ استفاده‌های بعدی NCDFE.

**null صادقانه‌ی میانی:** تلاش اول فیکس double-raise داد (NCDFE در pc پیش‌رونده از try بیرون زد و boot کشته شد — `clinit_post2.stderr` rc=1). با گارد in-flight جایگزین شد؛ ثبت شد، پنهان نه.

### رگرسیون — صفر drift روی باینری نهایی
**wall 12/12** (هر ۱۲ صورت بایت‌برابر) · **goldens 4/4** · **negatives 19/19** · **reinstall 8/8** · **MG-310 7/7** · **MG-150 3/3** · **c72priv 12-OK/0-BAD** · **selftests 13/13** · **F-NEW-376 70/70** · فنس c74esc 5/5 · clock1 4/4 · swipe1 قانون‌درست (residual e2 همچنان نام‌برده) · **as2048_47: 0 uncaught** (کاشف همین ریشه).

## ۳. لیست کاری بزرگ — تایید/رد تک‌تک (به‌روز CONT-87)
| مورد | حکم | تایید/رد |
|------|-----|---------|
| F-NEW-395 بخش الف (handler-match) | **REJECTED_WITH_EVIDENCE** — ادعا با decode + fixture رد شد | ❌ رد (ادعا) |
| F-NEW-395 بخش ب (honesty defect) | **ROOT-CAUSED-FIXED** — A/B کامل + باتری صفر-drift | ✅ تایید |
| bookkeeping registry (V1/V7/V8/V9 validator) | بدهی CONT-86؛ این موج بسته شد — **ALL PASS** | ✅ تایید |
| CONT-87 ترک ۲ (GLSL backend) | BLOCKED (project-scale/RAM؛ به‌عنوان BLOCKED ثبت‌شده از CONT-83) | ⏸ باز |
| CONT-87 ترک ۳ (throughput ~310K inst/s) | CONFIRMED_NOT_FIXED (profile مسطح؛ طبق خود directive بدون profile جدید تغییر نمی‌کند) | ❌ رد (باز) |
| CONT-87 ترک ۴ (Compose first-frame) | CLASSIFIED frontier — موج اختصاصی Compose می‌خواهد | ⏳ باز |
| CONT-87 ترک ۵ (F-145 multi-activity screenshot) | OPEN P1 — fixture+trace لازم | ⏳ باز |
| CONT-87 ترک ۶ (F-NEW-192 z-order) | فقط با trace اثبات‌شده | ⏳ باز-شرطی |
| CONT-87 ترک ۷ (F-NEW-214 logs-as-data) | PENDING P2 | ⏳ باز |
| CONT-87 ترک ۸ (Canvas field-less diag) | PENDING P2 | ⏳ باز |
| CONT-87 ترک ۹ (AndroidGraphics object graph) | OPEN P1 (پس از F-NEW-387/389) | ⏳ باز |
| CONT-87 ترک ۱۰ (swipe e2 ۶-float payload) | NAMED residual (deltas/velocities درست‌اند) | ⏳ باز |
| CONT-88/89/92 (Telegram end-to-end) | باز — بزرگ‌ترین workstream؛ فاز ۰ truth لازم | ⏳ باز |
| CONT-90 (۵ اپ سفید + ۵ هدف) | باز — نردبان first-divergence لازم | ⏳ باز |
| CONT-91 (WhatsApp artifact verdict → Signal کنترل) | باز — اول حکم آرتیفکت | ⏳ باز |
| CONT-93 (ماتریس ۱۰ بازی + 3D/strategy/farm) | باز — پس از ترک ۲ (GLSL) یا با BLOCKED صادقانه | ⏳ باز |
| R-NEW-456 z.ai Svelte-5 | BLOCKED (وابستگی باندل خارجی) | ❌ رد |
| UPP-001 native parity کامل | CONFIRMED_ADVANCED / مرز اسمی باقی | ⏳ باز |

## ۴. پرسنتاژ
- **این موج (CONT-87 ترک ۱): ۲ تایید (فیکس F-NEW-395 بخش ب + بسته‌شدن بدهی validator) + ۱ رد با شواهد (ادعای handler-match) — ۶۶٪ از ۳ قلم پردازش‌شده؛ هر سه با حکم نهایی.**
- **کیفیت رگرسیون: ۱۳/۱۳ گیت سبز، صفر drift — ۱۰۰٪.**
- **باز مانده روی #364: ترک‌های ۲..۱۰ CONT-87 + کل directiveهای CONT-88..93 (Telegram/messaging/white-batch/ten-game) — لیست بالا دقیقاً همین‌هاست.**

fixtures: `fixtures/cont87_clinit_probe` (com.probe.clinit1) · scripts: `cont87_build_probe.sh`، `cont87_decode_luu.py`، `cont87_registry_update.py`، `cont87_reconcile_registry.py` · evidence: `evidence/cont87/cont87_evidence.json` + `run/cont87/` (clinit_pre/clinit_post2/clinit_post3 A/B)
