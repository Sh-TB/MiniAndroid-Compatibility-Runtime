# CONT-158 — «۳۶۴ رو کامل بکن؛ ۱۰ از بازی و ۱۰ تا از گیم‌ها رو بررسی کن؛ ببین این همه تغییرات اثری داشته یا نه؛ اگر نداشته مشکلاتشون رو حل کن»

**پایه:** HEAD `fd4a1c89` (CONT-157) — سشن روی اسنپ‌شات کهنه باز شده بود (۲۹۹ کامیت عقب، صفر کامیت محلی) → ریست به origin/main. باینری با بازسازی قطعی: `22578fcb03e0cd15` بایت‌یکسان.
**پایان:** HEAD جدید، باینری `b7b193b541735991` (فقط F-NEW-497)، رجیستری **۸۱۳ ریشه** (id-unique، main==mirror).

## ۱) باتری ۲۰ سطری بازی‌ها — پاسخ با رقم و عدد

۲۰ سطر = **۱۸ بازی واقعی** (dooz ×۲ واریانت، bouncy ×۲ واریانت، tictactoe، gmdice، fishrings، memory، tower3d، tripeaks، chess، chessclock، flappycow، klondike، sudoku، ۲۰۴۸، snake-deluxe، tetris) + **۲ سطر مرجع با برچسب صادقانه** (stopwatch، opencalc — ابزار، نه بازی).

| وضعیت | قبل از فیکس | بعد از فیکس |
|---|---|---|
| محتوای واقعی | ۱۰/۱۸ | **۱۳/۱۸** |
| صورت‌های خالی | ۸ (فقط ۳ امضای مشترک) | ۵ |

**بله — تغییرات اثر داشته؛ با شواهد per-app:** bouncy منوی کامل (Select Table/Start Game/High scores)، gmdice تاس‌ریز («Roll it!» + 3D20/1d20/1d6/1d8+4)، chessclock ساعت 10:00، flappycow صفحه عنوان با PLAY، sudoku شبکه، g2048/snake/tetris کامل قابل‌بازی‌نما، opencalc کیپد کامل — همه روی باینری فعلی، صفر رانش انکر.

## ۲) رمزگشایی سه‌گانه b5a7a35d (صورت خالی مشترک) و یک فیکس عمومی

- **fishrings و tripeaks:** WebView اسپلش → `loadUrl(assets/banner.html)` → «asset MISSING». راستی‌آزمایی با unzip: **هر دو APK اصلاً پوشه assets/ ندارند** — این ۴۰۴ وفادار به آرتیفکت است، باگ موتور نیست. گذار واقعی اپ، **تایمر ۵ ثانیه‌ای اسپلش** است: `[QUEUE] Timer.schedule delay=5000ms` — و `runnables_fired=0` در همه فریم‌ها چون ۵ فریم × ۳۰۰ms = **۱۵۰۰ms مجازی ≪ ۵۰۰۰ms**. کپچر اپ را در ثانیه ۱.۵ زندگی‌اش خشک کرده بود.
- **F-NEW-497 ROOT-CAUSED-FIXED — POST-CAPTURE DRAIN-TO-DEADLINE:** بعد از حلقه فریم‌ها، تا وقتی کار آینده‌دار در صف هست و ساعت مجازی < بودجه اعلام‌شده (`--max-seconds`): پیشروی poll-timeout (پاریتی AOSP MessageQueue.next)، تخلیه و اجرای Runnable ها از همان مسیر قانونی، pump بامزه per-boundary، و مصرف `pending_intent` در **هر** مرز (نسخه اول آبشار GameActivity را بعد از اسکرین‌شات رها می‌کرد — اصلاح شد). قطعی (صفر ساعت دیواری)، یکنواخت (بدون چک اپ‌خاص)، قرارداد launch-frame دست‌نخورده. سقف §18: ۵۱۲ دور / ۶۴ دور بی‌پیشرفت.

## ۳) نتیجه: سه عبور جدید واقعی

| بازی | صورت قبل | صورت بعد | مدرک روی پرده |
|---|---|---|---|
| fishrings | `b5a7a35d` تک‌رنگ | `a341e3ad` — **۳۳۱۰ رنگ** | صفحه‌ی واقعی بازی حلقه‌ها |
| tripeaks | `b5a7a35d` تک‌رنگ | `e2a290ab` — ۱۳۰ رنگ | «Welcome to the Tri Peaks Solitaire for Android!» + دکمه‌های New Game/About Us/Help/Exit |
| klondike | `31ddd4d5` سفید | `a77038da` — ۱۳۶ رنگ | منوی واقعی: New Game / View Help / About Game / Check for Updates / Exit |

## ۴) دیوار و منفی‌ها — همه سبز با توضیح صادقانه

- **دیوار ۹/۹:** ۸ MATCH — از جمله unote در انکر واقعی خودش `7481e9b4` (مدخل `90a67cc1` در لیست من از دوره c129 کهنه بود — اصلاح صادقانه)؛ **klondike re-base مستند** `31ddd4d5→a77038da` (عبور REAL_APP_CONTENT؛ همان مقوله CONT-157 برای dooz/telegram).
- **منفی‌ها ۱۹/۱۹:** اجرای اول ۹/۱۹ بود — علت: state سشن probe_store بعد از ریست اسنپ‌شات غایب بود (قانون CONT-156: «session-state re-run»)؛ بعد از ران مجدد probe → ۱۹/۱۹. **این رگرسیون فیکس نبود.**
- **سلف‌تست ۱۳/۱۳.**

## ۵) رجیستری ۸۱۰→۸۱۳

- **F-NEW-497** ROOT-CAUSED-FIXED (پست-کپچر drain-to-deadline).
- **F-NEW-498** CLASSIFIED — مرز libGDX/native تیک‌تک‌تو: libgdx.so واقعی (x86_64، ۲۶۰۶۹۶B) استخراج ولی dlopen داخل لودر SIGSEGV؛ سپس NPE روی Gdx.app نال در AndroidLauncher.onCreate. اهرم‌های نام‌گذاری‌شده: قانون probe لودر (خانواده UPP-001) + خانواده سایه GLSurfaceView/EGL.
- **F-NEW-499** CLASSIFIED — شکاف rebind تم در relaunch اکتیویتی (memory: متن‌ها یکسان، پس‌زمینه 28→48 خاکستری).
- game_registry.json: GAME-016 PARTIAL→OBSERVED + یادداشت‌های CONT-158 برای GAME-014/015/088/011/091.

## ۶) کاشی موزایکی بازی‌ها

`run/c158/cont158_mosaic.png` — شبکه ۲۰ کاشی از **فیس‌های واقعی ران‌ها** (سبز=محتوا، زرد=جزئی، قرمز=تک‌رنگ/سفید). برچسب‌ها انگلیسی (PIL شیکر RTL ندارد — عدد زبان مشترک است).

## ۷) مرز صادقانه باقی‌مانده (۵ سطر)

dooz + dooz_top در مرز draw-op `31ddd4d5` (۱۰۸۰×۱۹۲۰ اندازه‌گیری، ۱۹۴۷ عملیات ثبت‌شده — ارائه پشت دیوار throughput ترسیم F084 = کوهورت F-NEW-481)؛ tictactoe = F-NEW-498؛ chess = زنجیره `Resources$NotFoundException(0xFFFFFFFF)` XML در AppCompat (رمزگشایی بعدی)؛ tower3d سیاه یکنواخت (رمزگشایی بعدی).
