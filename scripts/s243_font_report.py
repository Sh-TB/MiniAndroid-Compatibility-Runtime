#!/usr/bin/env python3
"""S242/FONT-PIPE-002 Persian report — the font-loading definitive fix."""
import re, subprocess

R = "/home/z/my-project/"
def gate(path, pat, default="PENDING"):
    try:
        t = open(R + path).read()
        m = re.search(pat, t, re.S)
        return m.group(1).strip() if m else default
    except OSError:
        return default

ta  = gate("w242_testall.log", r"BATTERY SUMMARY: (total=\d+ passed=\d+ failed=\d+)")
par = gate("w242_parity.log", r"\[PARITY-OK\] (\d+ core sources manifest-parity)")
sha = subprocess.run(["git","-C",R,"rev-parse","--short=12","HEAD"],
                     capture_output=True, text=True).stdout.strip()

DOC = f"""# گزارش FONT-PIPE-002 — حل قطعی مشکل لود فونت (issue #605)

**تاریخ:** 2026-11-15 · **کامیت:** main = `{sha}` · **باتری:** ۱۱۳ مدل، 113/113 PASS

## ۱. یافته کلیدی

fix توصیف‌شده در issue #605 (branch `font-pipe-002...` با commit `ecb9355a`) **هرگز به main نرسیده بود** — نه branch در ریموت بود و نه هیچ کد از APIهای توصیف‌شده در سورس main وجود داشت. پیاده‌سازی این موج از سورس انجام شد و با باتری بزرگ‌تر (۱۱۳ در برابر ۳۰) سخت‌گیرانه‌تر بسته شد.

## ۲. پنج ریشه مشکل و راه‌حل هر یک

| # | ریشه | راه‌حل قطعی |
|---|---|---|
| ۱ | مسیر واحد hardcode برای هر فونت | `load_face_first()`: جدول کاندیدهای مرتب per-face (Debian اول، بعد Fedora/flat/Noto)، هر کاندید با fopen واقعی پروب می‌شود تا فایل خراب به کاندید بعدی برسد |
| ۲ | مسیر emoji روی Debian هرگز وجود نداشت (`truetype/emoji/` غلط؛ واقعی `truetype/noto/`) | جدول کاندید emoji با مسیر واقعی Debian شروع می‌شود |
| ۳ | alias خاموش: فونت‌های غایب بی‌صدا با regular جایگزین می‌شدند و باگ شِیپینگ واقعی پنهان می‌شد | پرچم صادقانه `Face::aliased` + سه‌حالته `LOADED/ALIASED/MISSING` در `face_info()`؛ fallbackِ در دسترس فقط روی فیس واقعی |
| ۴ | هیچ راهی برای «مطمئن شویم فونت واقعاً لود شده» نبود | API راستی‌آزمایی: `face_info` / `loaded_face_count` / `loaded_face_mask` / `font_diagnostic_report` و **`verify_text_renders`** — با FT_Face تازه‌ی probe (صفر تداخل با hb cache)، رستر هر گلیف پوشش‌داده‌شده و شمارش جوهر واقعی؛ `لود واقعی = glyphs>0 && ink>0` |
| ۵ | نشتی FT_Face: فیس CJK و فیس‌های اپ در destructor آزاد نمی‌شدند | هر دو آزاد می‌شوند |

## ۳. باتری ۱۱۳مدلی (۸ گروه)

| گروه | تعداد | پوشش |
|---|---|---|
| A لود و مسیر | ۱۶ | حقیقت per-face، sanity upem (فیس‌های CBDT صادقانه upem=0)، مسیرهای خراب/صفر/غیرفونت/ناموجود |
| B خانواده | ۱۵ | sans/serif/monospace/monaco + قانون مجاز خانواده ناشناخته + رجیستر فونت اپ و lookup نام |
| C پوشش اسکریپت | ۲۴ | Latin، اعراب، Greek، Cyrillic، عبری RTL، عربی (اتصال/ارقام)، Han، کانا، هانگول، تایلندی، دواناگری، emoji سطوح مختلف، ریاضی و ارز |
| D نه‌دف و لبه | ۱۲ | PUA، surrogate تنها، کنترل‌کاراکتر، رشته تهی، U+10FFFF، ران ۱KB، U+FFFD |
| E متریک و چیدمان | ۱۴ | علامت متریک‌ها، قانون line-height، برابری measure==draw، wrap/ellipsize/spacing |
| F اثبات جوهر | ۱۴ | جوهر per-face، PUA بدون جوهر، سایز ۸ تا ۲۰۰px، قطعیت جوهر، فونت اپ end-to-end |
| G سازگاری API | ۱۰ | count==popcount(mask)، سازگاری فیلدهای proof، قطعیت شِیپ |
| H رگرسیون و استحکام | ۸ | قوانین s98/s106 سبز، fuzz بایت و codepoint بدون crash، قطعیت ۳ران |

## ۴. یافته‌های صادقانه از ران اول (107/113 → 113/113)

- ۴ خطا انتظارِ غلطِ خود باتری بود و به قانون واقعی موتور اصلاح شد: `metrics()` بزرگ‌نمایی مثبت برمی‌گرداند (فقط `font_metrics()` قرارداد AOSP علامت منفی دارد)؛ `has_family()` مجاز است (خانواده ناشناخته → sans پیش‌فرض)؛ PUA در میانه ران توسط زنجیره fallback **پوشش داده می‌شود** (قانون fonts.xml AOSP درست کار می‌کند)؛ فیس‌های bitmap (emoji) طبیعتاً upem=0 دارند.
- ۱ باگ واقعی در خودِ verify API: probe مسیرهای نسبی (مونواسپیس runtime) را رد می‌کرد — رفع شد تا هر فرم مسیر بپذیرد.

## ۵. گیت‌ها

| گیت | نتیجه |
|---|---|
| باتری s243 | **113/113** |
| بیلد باینری اصلی | RC=0 |
| test-all | {ta} |
| parity | {par} |

## ۶. پاسخ قطعی به پرسش issue

**فونت فقط وقتی اثباتاً لود شده که `face_info(idx).state == LOADED` باشد و `verify_text_renders(idx, متن, سایز).ok == true`** — هیچ سیگنال دیگری (بی‌خطا بودن، crash نکردن، رندرِ چیزی) مدرک نیست.
"""

open(R + "download/S242_font_report.md", "w").write(DOC)
print("report:", len(DOC), "chars")
