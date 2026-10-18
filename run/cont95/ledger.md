# CONT-95 RESULT — #364: درخواست‌ها استخراج شد · ریشه‌ی مرگ بوت تلگرام (F-NEW-397) رفع شد · قانون واقعی SAX

**Wave:** CONT-95 · **directive:** «ادامه» (trace `1a14dd41533e98b9`) — استخراج → نمایش → لیست کاری → اجرا (تلگرام اولویت اول) · **HEAD:** `95dd9bf7` → `e55ffcb1` · **binary:** `7cf6fe7f3d6abb81` → `aa9ade61b147c12b` · **registry:** 703 → 704 روت

---

## ۰. استخراج درخواست‌های #36۴ (۵۵ کامنت — طبق دستور: استخراج → لیست → نمایش → اجرا)

بعد از ledger CONT-94 (کامنت `6246750013`) **هیچ درخواست جدیدی نیامده**. بک‌لاگ باز همان CONT-87..93 است:

| # | کامنت | عنوان | وضعیت |
|---|-------|-------|-------|
| 1 | 6245477077 | **CONT-88** — REAL APP EXECUTION | T3 (bounds/offset) + T4 + T6 باز |
| 2 | 6245481160 | **CONT-89** — TELEGRAM FORENSIC ۷ صفحه | صفحه ۱ partial؛ ۲..۷ باز |
| 3 | 6245481420 | **CONT-90** — WHITE APP RECOVERY | باز |
| 4 | 6245481662 | **CONT-91** — WHATSAPP PARITY | حکم NOT_AVAILABLE بسته شد؛ بقیه باز |
| 5 | 6245501827 | **CONT-92** — SOURCE-GROUNDED | باز |
| 6 | 6245531086 | **CONT-93** — TEN-GAME MATRIX | باز |
| 7 | 6245430786 | **CONT-87** — ده فیکس | Track 1 بسته؛ Track 2..10 باز |

**لیست کاری (تلگرام اول):** R1=T3 bounds/offset (P0) · R2=T4 RecyclerView · R3=T6 string-resource (LOC_ERR) · R4=native/billing/firebase boot boundaries · R5=صفحات ۲..۷ · R6=CONT-90 · R7=CONT-93 · R8=CONT-87 tracks.

## ۱. کشف موج — مرگ بوت تلگرام STATE-DEPENDENT بود، نه پایدار

اجراهای مجدد با باینری **بدون تغییر** `7cf6fe7f3d6abb81`: تلگرام/فورکگرام فقط status bar (۱۴۳۱ px) — نه چهره‌های آرشیو CONT-94 (۸۷۲۱/۱۵۵۹۹ px). هم data-root تازه و هم بازیابی prefs ثبت‌شده همین را داد → نه leftover-state، نه drift باینری.

**diff معنایی stderr:** فایل `mainconfig.xml` ثبت‌شده حاوی `theme=Night` است — **در طول اجرای آرشیو CONT-94 نوشته شده** (اسنپ‌شات ۲۱-موردی = state وسط اجرا). پس re-boot ها مسیر wallpaper **Night** را می‌روند؛ چهره‌ی آرشیو بوت Day-path بود. **درس روش‌شناختی: چهره‌های آرشیو state-وسط-اجرا هستند؛ state-dependence مسیرهای بوت اپ حالا بعد ماشه‌شماری درجه-یک است.**

## ۲. زنجیره‌ی مرگ (Night path) — decode از ground truth

`af/u1` runnable → `yc0` (MotionBackgroundDrawable) → **SvgHelper** pattern decode → `o6.I` unit 951: `Bitmap.createBitmap(w,h,ARGB_8888)` با w/h از `yc0.u.getWidth()/getHeight()` → **createBitmap(0,0)** → IAE (قانون AOSP درست) → **RAW DEX TRY-TABLE PARSE** (`scripts/cont95_raw_try_generic.py` — مستقل از wrapper وندور): `o6.I` هشت try دارد که همه ≤ unit 873 بسته می‌شوند (سایت createBitmap 951 پوشش ندارد)؛ `LaunchActivity.onCreate` unit 1375 هم پوشش ندارد → APP-BOUNDARY → مرگ بوت → قاب سفید. **مسیریابی استثنای ران‌تایم در همه‌ی گام‌ها درست بود؛ صفرِ بالادستی باگ بود.**

## ۳. ریشه (F-NEW-397) — registry مرده

`XMLReader.parse(InputSource)` بایت‌های سند را از `s109_stream_bytes` می‌خواند — **ground truth با rg: یک اعلان + دو خواندن، هیچ سایت نوشتنی در کل موتور وجود ندارد.** پس هر parse روی stream: ۰ event به ContentHandler خودِ اپ (چهره‌ی لاگ: `parse: no handler (yes) or bytes (0)`) و parse() بی‌صدا void برمی‌گشت. SvgHelper (کلاینت SAX جاوای خود تلگرام) ۰ event گرفت → bitmap pattern degenerate (`yc0.u` non-null ولی ۰×۰) → همان createBitmap(0,0).

## ۴. فیکس — یک قانون، صفر شرط اپ

وقتی registry خالی بود، `XMLReader.parse` حالا stream را از **قانون یک-بایت asset** حل می‌کند (`resolve_asset_stream` → `cached_asset_bytes`) — همان قانونی که `InputStream.read` سرو می‌کند (GATE A کلیدهای `apk-entry:` می‌سازد). tokenizer و dispatch موجود به اپ دست‌نخورده اجرا می‌شود؛ **موتور هیچ معناشناسی SVG اضافه نمی‌کند** (AOSP: org.xml.sax قرارداد عمومی است).

## ۵. اثبات — fixture + APK واقعی

### fixture `com.probe.sax1` (sha16 `2d8c7e72afbb2229`، aapt2/ECJ/D8 واقعی با res/raw)
| باینری | ردیف [SAX1] |
|---|---|
| قبل `7cf6fe7f3d6abb81` | `events=0/0 root=?x? names= verdict=FAIL` ❌ |
| بعد `aa9ade61b147c12b` | `events=6/6 root=1080x1920 names=svg,g,path,path,rect,circle verdict=PASS` ✅ |

### تلگرام رسمی (۱۲.۱۰.۵ vc71059)
- قبل: `parse: no handler (yes) or bytes (0)` + createBitmap(0,0) IAE → مرگ APP-BOUNDARY در onCreate
- بعد: **`parse OK: 746 elements -> SvgHelper$SVGHandler (507258 bytes)`** — ۴.۷M فراخوانی API از کار واقعی DEX اپ؛ IAE غایب؛ بوت به onStart/onResume می‌رسد؛ ۶ uncaught (فقط مرزهای شناخته‌شده‌ی billing/native/firebase)؛ ۰ WALL-STOP در ۲۴۰ ثانیه

## ۶. رگرسیون — صفر drift روی `aa9ade61b147c12b`

**wall 12/12 MATCH** (dooz `31ddd4d5b8e6d18e` ×3، opencalc `f25b754c4565c38b` ×3، unote `90a67cc1ddda57b7` ×3، microtimer `bbd350b6c14fbd52` ×3) · **goldens 4/4** (helloworld `83720c1028f832d0`) · **negatives 19/19** · **reinstall 8/8** · **MG-310 7/7** · **MG-150 3/3** · **c72priv ۱۳ ردیف 0-BAD** · **selftests 13/13** · **F-NEW-376 70/70** · c74esc containment OK · clock1 **4/4** · swipe1 OK · **as2048_47: 0 uncaught**

## ۷. باقی‌مانده‌های نام‌گذاری‌شده (صداقت)

1. **THROUGHPUT** — parse الگوی ۵۰۷KB = ۱۲.۶M+ دستورالعمل مفسر DEX (حلقه‌های کاراکتری `SvgHelper$ParserHelper`)؛ گیت ۳۰-ثانیه‌ای canonical آن را با **F084 wall-stop صادقانه** قطع می‌کند؛ در ۲۴۰ ثانیه بوت کامل می‌شود. این چهره‌ی مشخص فرانتیر CONT-87 Track 3 است — همین موج رفعش نکرد.
2. F084 در حلقه‌ی parse per-check دوباره شلیک می‌کند (۳۱۹ ردیف VME در run ۳۰ ثانیه) — ثبت شد، تغییری نکرد.
3. **T3** (bounds/offset محتوای login) و **T6** (`LOC_ERR` string resources) تغییری نکردند — باز.
4. بعد از فیکس، state اپ: صفحه‌ی sheet «Low power» با view tree واقعی (مسیر Night/pref) یا pre-login (fresh) — هر دو صادقانه ثبت شدند.

## ۸. پرسنتاژ

- **این موج: ۱ ریشه‌ی P0 کامل (کشف → decode → فیکس → fixture A/B + APK واقعی → باتری کامل)** — ۱۰۰٪ تایید؛ رگرسیون ۱۳/۱۳ گیت سبز صفر-drift = ۱۰۰٪.
- **دستاورد ساختاری:** قانون SAX حالا واقعی است — هر APKی که XML/SVG را با SAX خودش پارس می‌کند (تلگرام، فورکگرام، هر app با SVG asset) از این قانون بهره می‌برد.

fixtures: `fixtures/cont95_sax_probe` · scripts: `cont95_build_probe.sh`، `cont95_registry_update.py`، `cont95_battery.sh`، `cont95_raw_try_generic.py` (+ decode suite) · evidence: `evidence/cont95/` · runs: `run/cont95/`
