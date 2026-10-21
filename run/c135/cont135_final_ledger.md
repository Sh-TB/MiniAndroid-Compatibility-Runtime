# CONT-130..135 Ledger — «۶ قطار ادامه» — 6 trains, all pushed, HEAD==origin/main verified after each

**Base:** HEAD `d68f05da`, binary `25578933` (deterministic rebuild #6 after container reset). **Final:** HEAD `1f8126da`, binary `9e755c3dde69510c`, registry **787** (id-unique, main==mirror), final wall **9/9 anchors byte-identical + selftest rc=0 + negatives 19/19**.

## قطار ۱ — CONT-130 · F-NEW-471 ROOT-CAUSED-FIXED (push `31cd2262`)
حقیقت بایتی تازه (ابزار مستقل `cont130_dex_truth.py`): walk کلاس‌دیتای موتور **بایت‌دقیق** است؛ خود dex اعلان `AndroidApplication.onCreate` را ندارد (VM diffs از 1183 می‌پرد به 1185) در حالی که `method_ids[1184]` به آن ارجاع می‌دهد — **method_ids استخر ارجاع است، نه جدول اعلان‌ها**. فرضیهٔ CONT-127 (blob desync/GLES30) پس گرفته شد. اصلاح: قانون super-chain (`try_recursive_invoke_on_super`, ART JVMS 5.4.3.3) بعد از miss کلاس دقیق و قبل از shadow bridge؛ قانون بلند slice-1 بازطبقه‌بندی شد. tictactoe بایت‌پایدار (face `b5a7a35d`, exc 6→6).

## قطار ۲ — CONT-131 · F-NEW-472 CLASSIFIED (push `05cd91b2`)
سم place-then-reset دوز زنده گرفته شد: FIELD-TRACE `Ld61;.i` → هر سلول: `0` → `2319282340800` (=packInts(540,960) placeholder مرکز measure) → `0` در پاس placement واقعی. بازتاب بایت‌به‌بایت: محاسبهٔ دوم **kotlin EmptyMap singleton** را می‌خواند (`Ln20;` = Map impl، static `e`؛ ۹ سایت sget، **صفر sput**) — مسیر publish وضعیت هرگز اجرا نمی‌شود. نوشتن صفرها ریاضیِ درست روی وضعیت خالی است، باگ موتور نیست (بدون پچ app-specific). اهرم بعدی: ردیابی setter نگهدارندهٔ state.

## قطار ۳ — CONT-132 · بازطبقه‌بندی صادقانهٔ خانوادهٔ default-bg (push `0ee5b568`)
بررسی متقاطع aapt2: `stopwatch_6` **هیچ عنصر `<activity>` ندارد** (اپ QS-tile فقط: ۲ TileService + provider + receiver) — face پیش‌فرض آن **اثر faithful آرتیفکت** است، نه مرز draw-op (NO_LAUNCHER_ACTIVITY). لانچرهای telegram/forkgram از طریق قانون alias (EXP-038) درست resolve می‌شوند (لایو تأیید شد: `LaunchActivity`؛ CATEGORY_LAUNCHER روی ۲ activity-alias — aapt2 badging از alias سر در نمی‌آورد، موتور می‌آورد). خانوادهٔ واقعی draw-op frontier: klondike/tripeaks/fishrings/tictactoe. بدون تغییر موتور.

## قطار ۴ — CONT-133 · PARTIAL batch wave 1 (push `dd71ecb1`)
۳۰ ردیف در HEAD: **۲۵ VERIFIED-CORRECT** (مکانیزم‌ها در سورس دوباره لنگر شدند)، **۵ صادقانه PARTIAL ماندند** (R-NEW-001/061/062/079/080). همهٔ یادداشت‌ها با wall تاریخ‌دار شدند.

## قطار ۵ — CONT-134 · موج UNPROVEN — همهٔ ۹ ردیف terminal (push `1f8126da`)
`R-NEW-137` ROOT-CAUSED-FIXED (پارسر metadata فرود آمد + لایو تأیید: `[371-MD] metaData entries=3`)؛ `R-NEW-133` CONFIRMED_OPEN_GAP (صفر ارجاع InMemoryDexClassLoader — اثبات سورسی)؛ `R-NEW-140` BLOCKED (آرتیفکت resource-shrunk در کورپوس نیست — صادقانه)؛ `R-NEW-247` CLASSIFIED (کلاس‌های RecyclerView در dex notes/memory تأیید شد)؛ 018/019/084/040/281 CLASSIFIED. **UNPROVEN صفر شد.**

## قطار ۶ — CONT-135 · wall نهایی
9/9 anchors بایت‌یکسان (dooz `d602648e`، klondike `31ddd4d5`، unote `90a67cc1`، chess `a0319686`، telegram `20ac8cbbbb`، tower3d `11a38a5a`، opencalc `d5f3c7b5`، microtimer `bbd350b6`، sudoku `be640e39`) + selftest rc=0 + negatives 19/19.

## وضعیت رجیستری (۷۸۷ ریشه)
ROOT-CAUSED-FIXED **۲۹۵** · VERIFIED-CORRECT ۸۸ · VERIFIED-FIXED ۵۰ · خانوادهٔ تعمیرشده جمعاً **۳۶۷/۷۸۷ (۴۶.۶٪)** · PARTIAL ۸۷ · CLASSIFIED ۲۱ · UNPROVEN ۰ · BLOCKED ۲ (آرتیفکت‌محور: resource-shrunk، Signal).

**اهرم‌های بعدی:** مسیر publish state-map دوز (F-NEW-472)، InMemoryDexClassLoader (R-NEW-133)، پروب‌های Parcel (R-NEW-018/019)، ۸۷ PARTIAL.
