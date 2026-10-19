# CONT-106 LEDGER — issue #364

**Wave:** CONT-106 (batch) · **Base:** origin/main `236df145` (CONT-105) · **Final binary:** `f72413b74525d3b0` (post-fix; entry rebuild reproduced `afaad5bd4f56f9d3` byte-identically) · **Registry:** 760 → **764** (F-NEW-446..449 + F-NEW-445 refresh) · **Evidence:** `evidence/cont106/evidence.json`

## بازیابی کانتینر
کپی محلی دوباره snapshot کهنه بود (`e99c2fbd`، که پیشِ‌نیازِ origin است — fast-forward خالص). بازسازی کامل باینری `afaad5bd4f56f9d3` را **بایت‌یکسان** بازتولید کرد. #364 خوانده شد: **۷۱ کامنت؛ صفر کامنت جدید بعد از baseline 6259475660** — مأموریت = فهرست مالکیتِ اعلام‌شده‌ی CONT-105.

## نتیجه‌ی مرکزی موج — F-NEW-445/446: ریشه‌ی P1 تلگرام بسته شد (fixture-first تمام‌قد)

**دیکد (androguard، هر ۴ dex):**
- `o6.u1` فقط **یک نویسنده** دارد: متد استاتیک `o6.P(Context)`؛ callerهای P = `o6.R` / `Cells.r4.<init>` / `CheckBoxSquare.<init>` (هیچ‌کدام قبل از crash اجرا نشده بودند)
- `o6.k` (callerها: P بعد از تخصیص — امن؛ `n1` بدون گارد) با `sget k0; if-nez k0,+3; return-void` شروع می‌شود (0x0..0x8)

**ریشه:** قانون `S123-CLINIT-MAT` engine (گیت `attempted || stored_null`) روی `sget` اولِ یک Paint استاتیکِ هرگز-تخصیص-نیافته از کلاسی با clinit **سالم**، شیء جعل می‌کند → گارد سنتینل `o6.k` رد می‌شود → `iput xj0.Y:Z` روی `u1` نال → NPE @pc=46. AOSP: sget باید همان null را برگرداند.

**پروب** `fixtures/cont106_clinitsentinel` (c106a، aapt2/ECJ/D8 واقعی، `fe29697e17cbc6c4`):

| Row | PRE (`afaad5bd`) | POST (`f72413b7`) | AOSP |
|---|---|---|---|
| SENTINEL guardEscaped | **true (باگ)** | **false** | false |
| FACTORY ordering | true | true | true |
| CLINITFAIL (رفتار clinit-شکست) | sget-throw=ISE | sget-throw=ISE (بدون تغییر) | ثبت صادق |
| INVOKE (با factory) | NO-EXC | NO-EXC | NO-EXC |
| INVOKE2 (بدون گارد) | NO-EXC (باگ دوم) | NO-EXC ← **ROOT-059 جدا** → F-NEW-447 | NPE |

**فیکس (عمومی، بدون نام اپ):** گیت S123 → `failed_clinit_classes_` (نقشه‌ی شواهد F-NEW-215) — فقط clinit واقعاً-شکست‌خورده مادی‌سازی می‌شود؛ هدف اصلی S123 (rectTmp فورکگرام) دقیقاً حفظ شد (`Broken.rectTmp clinit_failed=true` در POST).

**اثبات روی تلگرام واقعی:** S123 = **۰ بار**؛ `o6.k` با Paintهای **واقعی کارخانه** اجرا شد (`recv=6740/6747 @pc=13/24`)؛ `xj0.<clinit>` OK؛ `xj0.Q` اجرا شد؛ چهره‌ی NPE حذف شد؛ run تا `LaunchActivity.onCreate invoke_pc=1375` پیش رفت و فقط با خانواده‌ی شناخته‌شده‌ی **F084 pacing** تمام شد (F084: ۵۹۹ در برابر ۴۸۴ِ PRE — پیشرفت).

## باتری کامل — صفر دریفت در `f72413b74525d3b0`
wall **۱۲/۱۲ بایت‌یکسان ×۳** (dooz `d602648e` / opencalc `f25b754c` / unote `90a67cc1` / microtimer `bbd350b6`) · goldens **۴/۴** · negatives **۱۹/۱۹** (بعد از تعمیر مستند کانتینر-تازه: gate_a_probe `628ce8e8` + install+run کانونی — پیشینه‌ی cont98) · reinstall **۸/۸** · MG-310 **۷/۷** · MG-150 **۳/۳** · skill **۱۳/۱۳** · F-NEW-376 **۷۰/۷۰** · c104i **۴/۴** · c74esc **۵/۵**

## واحدهای دیگر (هر یک با وضعیت پایانی)
- **F-NEW-448** (چس): f141=0 پایدار؛ چهره‌ی جدید: `Toolbar.onMeasure` دوبار `Ll/m3;.a == 0` می‌خواند → Toolbar **1080x0** — استاتیکِ height مشتق از theme هرگز مقدار نگرفته → CONFIRMED_OPEN_GAP با lever مشخص (probe یِ theme-dimension، موج بعد)
- **F-NEW-449** (n2.r play_billing): دیکد مرز دقیق OOB — خواندن مرزی حلقه‌ی rotated در `0x568` (`aget-object v29, v24, v10` با `v10 == v24.length` بعد از `add-int/lit8`)؛ ناسازگاری count آرایه‌ی entries در برابر شمارنده‌ی walk؛ قانون reflection-count باید دو منبع را موافق کند → CONFIRMED_OPEN_GAP + پروب c106b
- **باستان‌شناسی stale-.o**: REJECTED_WITH_REASON — توسط F-NEW-443 مفتومن است (بازسازی کامل بایت-قطعی است؛ bisect یک lineage حذف‌شده ارزش اقدام ندارد)
- **مرز draw کامپوز dooz** و **UPP-001**: صادقانه حمل شدند (BLOCKED_NEEDS_EVIDENCE / BLOCKED)
- Registry: main == mirror == **764**، id-unique

## نرخ موفقیت
- **۱۵/۱۵ واحد به وضعیت پایانی رسیدند** · **۸/۱۵ کاملاً بسته (۵۳٪)** · وزن‌دار ≈ **۸۰٪** (یک فیکس P0 با اثبات real-app + سه دیکد با lever + دو carry صادق + registry/push)
- حکم‌های جدید: ۴ (۱ ROOT-CAUSED-FIXED، ۳ CONFIRMED_OPEN_GAP با lever) + ۱ refresh (445→بسته)

## مالکیت موج بعد
پروب‌های آماده: **F-NEW-447** (A/B مسیر ROOT-059 با ردیف پروب موجود) · **F-NEW-448** (پروب theme-dimension → قانون استاتیک action-bar height) · **F-NEW-449** (c106b: توافق دو منبعِ count بازتاب) · مرز draw: قانون ساخت AndroidCanvas bridge
