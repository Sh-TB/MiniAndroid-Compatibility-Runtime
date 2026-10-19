# CONT-112 LEDGER — issue #364

**Wave:** CONT-112 (elephant batch) · **Base:** origin/main `96bcb963` (CONT-111) · **Final binary:** `623827ee2ffd3829` (lineage: pre-fix bracket `62df609a70fcf488` = fresh worktree at origin/main, zero fix code) · **Registry:** 768 → **773** id-unique (main == mirror) · **Evidence:** `evidence/cont112/evidence.json`

## مأموریت
لِوِر ۱ از «گام بعدی» CONT-111 (کامنت 6273185386): **F-NEW-448 لایهٔ ۲** — seeding `android:min*` برای نماهای DEX-ساخته — تا ریشه‌یابی-و-رفع کامل، با کشفِ **پنج ریشهٔ انباشته** در مسیر دیکد. لِوِرهای ۲/۳ (F-NEW-449 / CONT-110 P0) برای موج بعد.

## زنجیرهٔ دیکد (fixture-first، هر گام با شاهد)
1. **دیکد DEX:** `Toolbar;.onMeasure` (R8: `(I I)V`) در @1126 `getSuggestedMinimumHeight()` و در @1134 با آن max() می‌کند → قانون لایهٔ ۱ (CONT-111) درست است؛ نود هرگز seed نگرفت. (`scripts/cont112_toolbar_disasm.py`)
2. **دیکد layout:** تگ Toolbar در `abc_screen_toolbar` شطرنج `style=?0x7f040540` (toolbarStyle) دارد.
3. **دیکد theme:** `toolbarStyle` → REFERENCE `0x106000d` — که در **هیچ** جدولی (app یا framework) style نیست: **aapt2 اثبات کرد 0x0106xxxx رنگ است** — resolve_attribute رفرنسِ style را مثل VALUE deref کرده بود (آیتم اولِ بگ = یک رنگ).
4. **بعد از رفع deref:** style به `@style/Widget.Material3.Toolbar` (raw) رسید → بگ + زنجیرهٔ parent → `android:minHeight=?attr/actionBarSize` — ولی ID کلید بگ `0x01010140` بود نه `0x01010151` (CONT-111 اشتباه؛ **aapt2 ground truth: minWidth=0x0101013F، minHeight=0x01010140**).
5. **بگ رفع شد، lp مسموم ماند:** `LayoutParams.<init>` با `getLayoutDimension` slot نوع-ATTRIBUTE را RAW پاس داد (`0x7f040006` → height=2130968582) → قانون deref جدید.
6. **پروب c449 سه ردیف اول را زد:** رسیورِ Context-typed به ActivityShadow نمی‌رسید (dispatch از نوع static) + نصب recs درست بود ولی producer مرحلهٔ ۲ را هرگز نمی‌دید (**ترتیب scan**: استخراج xml-style قبل از scan اجرا می‌شد — برای هر APK مرده بود) + اتریبیوت ns-less `style` به‌کلی از recs افتاده بود.

## پنج ریشهٔ جدید — ROOT-CAUSED-FIXED
- **F-NEW-454:** routing بگِ style پکیج-framework (apply_style table-parametric) + قانون raw برای رفرنس-style در Theme.resolve_attribute (بگ = value نیست).
- **F-NEW-455:** قانون deref خوانندهٔ TypedArray: slot های REFERENCE/ATTRIBUTE قبل از تبدیل به dimension پایانی deref می‌شوند (≤8 hop).
- **F-NEW-456:** dispatch مجازی از **کلاس runtime** گیرنده شروع می‌شود (نه نوع static مرجع).
- **F-NEW-457:** scan رکوردهای AttributeSet در producer **قبل از** استخراج xml-style (مرحلهٔ ۲ از CONT-55 برای همیشه مرده بود).
- **F-NEW-458:** IDهای واقعی `android:minWidth/minHeight` (0x0101013F/0x01010140، با aapt2 دو بار تأیید) + قانون id اتریبیوت `style` (0x01010000).

## پروب c449 (fixtures/cont112_lawderef، aapt2/ECJ/D8 واقعی، sha16 `90420f5a2d87ba20`) — ۴/۴
FLOOR-MIN 168 (زنجیرهٔ style-parent ?attr→@dimen) · FLOOR-MEASURE 168 (max(content, suggestedMinimum) زیر AT_MOST) · DEREF-REF 168 (slot REFERENCE @dimen) · DEREF-ATTR 168 (slot ATTRIBUTE ?attr). **براکت A/B:** باینری پیش-فیکس **۰/۴** → فیکس **۴/۴**.

## براکت اپ شطرنج — F-NEW-448 لایهٔ ۲ بسته شد
پیش-فیکس (worktree تازه از origin/main، `62df609a`): Toolbar **1080x0**، چهرهٔ `b270ff040b3601dc` (پایخ CONT-111). فیکس (`623827ee`): Toolbar **1080x168** با متن نسخهٔ 10.6.0 به‌عنوان فرزند، چهرهٔ `a0319686d56ff5c0`. اکسپشن در-flight از قبل موجود (`371-GETXML-NOTFOUND`) در هر دو براکت یکسان است — رگرسیون نیست.

## باتری کامل — سبز در `623827ee2ffd3829`
wall **۱۲/۱۲ MATCH بایت‌یکسان** (dooz `d602648e` ×۳ / opencalc `d5f3c7b5` ×۳ / unote `90a67cc1` ×۳ / microtimer `bbd350b6` ×۳) · c448 **۷/۷** (رجرسیون CONT-111) · c74esc **۷ ردیف OK** · c106a/c106b2 سبز · goldens rc=0 · negatives+reinstall rc=0 · MG-310/MG-150 rc=0 · selftests rc=0.

## نرخ موفقیت
- **۱۰/۱۰ واحد کاری terminal** · **۶ بسته‌شدن کامل** (۴۴۸ لایهٔ ۲ + ۵ ریشهٔ جدید) · وزن‌دار ≈ **۸۵٪** (هر فیکس پروب یا براکت دارد، باتری کامل سبز، صفر دریفتِ ناموجَّه)
- **صادقانه:** لیست بورد RecyclerView شطرنج هنوز خالی است (children=0) — مرز لایهٔ محتوا، جدا از این زنجیره. F-NEW-376 (۷۰/۷۰) این موج re-run نشد؛ خانوادهٔ selftest سبز است.

## گام بعدی (levers نام‌گذاری‌شده)
1. **F-NEW-449:** دیکد متادیتای MessageInfo (protobuf-lite) — مرز بعدی تلگرام.
2. **CONT-110 P0:** جفت‌گزارش first-divergence چهار-کارا/پنج-سفید (#366) در HEAD فعلی.
3. **شطرنج لایهٔ محتوا:** چرا RecyclerView فرزند نمی‌سازد (adapter/ViewHolder مسیر DEX).
