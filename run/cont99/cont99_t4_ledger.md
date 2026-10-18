# CONT-99 T4 RESULT — «Button/control bounds, state and click target» بسته شد (F-NEW-407) · ۴ اجرای جفت‌شده · صفر drift

**Wave:** CONT-99 (واحد ۲) · **HEAD:** `6c0b6faa` → `da1909fd` (== origin/main) · **binary:** `4dd92ae1371569e4` → `3b89722589ff5af7` · **registry:** 718 → **719** روت

---

## CONT-99 T4 — قرارداد دکمه/کنترل → **تایید (ROOT-CAUSED-FIXED، F-NEW-407)**

**fixture-first:** `fixtures/cont99_btn_probe` (`c99btn.apk` sha16 `bf5c938e7ddc1c6c`، V1-C99BTN) — btnA `300x100` قرمز + btnB `200x80` سبز **مجاور با اندازه‌های متفاوت** در یک ردیف ۱۲۰px (hit regionهای غیر-همپوشان)، btnC `200x80` با `setEnabled(false)`، ردیف‌های bounds + شمارنده‌های onClick per-button + dump وضعیت.

**۴ اجرای جفت‌شده (یک tap قطعی در هر run):**

| اجرا | PRE روی `4dd92ae1371569e4` | POST روی `3b89722589ff5af7` |
|---|---|---|
| `--click-test` | **A=1 B=1 C=1 — تخلف قانون DISABLED**: onClick دکمه‌ی `setEnabled(false)` اجرا شد | `[CLICK-TEST] view 25 skipped: disabled` + **A=1 B=1 C=0** |
| `--tap 150,50` (مرکز btnA) | A=1 فقط ✓ | A=1 فقط ✓ |
| `--tap 700,60` (بین دو دکمه — منفی) | A=0 B=0 C=0 ✓ | A=0 B=0 C=0 ✓ |
| `--tap 100,190` (مرکز دکمه‌ی معادل) | A=0 B=0 C=0 ✓ | A=0 B=0 C=0 ✓ |

**یافته‌ها:** خط لوله‌ی `--tap` از قبل **hit-test را روی bounds واقعی چیده‌شده** انجام می‌دهد و قانون enabled را رعایت می‌کند (ردیف‌های bounds همگی OK: btnA `(0,0,300,100)`، btnB `(300,0,200,80)`، btnC `(0,120,200,80)` — کنترل‌های مجاور با اندازه‌های متفاوت، cross-axis top-aligned طبق قانون T1). **تنها ریشه:** شاهده‌ی `--click-test` خط لوله‌ی touch را دور می‌زد و listener «هر» کاندیدایی را آتش می‌زد — AOSP `View.onTouchEvent` ابتدا `ENABLED_MASK` را چک می‌کند: نمای معادل فشار را رد می‌کند (بدون pressed، بدون performClick، بدون onClick). یک شاهده باید همان قانونی را ببیند که خط لوله‌ی واقعی اجرا می‌کند.

**فیکس (F-NEW-407):** هر دو حلقه‌ی dispatch در `stage_click_test` (listener + XML `android:onClick`) اکنون `node->enabled` را چک می‌کنند؛ کاندیداهای معادل با `disabled_skipped=true` در report ثبت می‌شوند + خط stderr بلند (شواهد صادقانه، نه حذف بی‌صدا).

**رگرسیون — صفر drift:** wall **۱۲/۱۲ MATCH بایت‌برابر** (dooz `31ddd4d5b8e6d18e` · opencalc `f25b754c4565c38b` · unote `90a67cc1ddda57b7` · microtimer `bbd350b6c14fbd52` ×۳) · goldens **۴/۴** · negatives **۱۹/۱۹** · reinstall **۵/۵ identity ALL PASS** · MG-310 **۷/۷** · MG-150 **۳/۳** · selftests **۱۳/۱۳** · F-NEW-376 **۷۰/۷۰** · perf1 جمع‌ها بایت‌برابر (3688000/31744000/14534196240/14569628240). تغییر محدود به مرحله‌ی opt-in `--click-test` است؛ باتری به‌هرحال دوباره اجرا شد.

**نکات صادقانه:** رندر visual وضعیت pressed (drawable `state_pressed`) در این واحد ممیزی نشد — residual نام‌گذاری شد؛ ردیف‌های STATE معناشناسی وضعیت را اثبات می‌کنند نه رندر drawable فشرده.

## وضعیت CONT-99 پس از این موج: **۲/۱۰ ترک بسته (T1، T4) · هر کدام یک تسک مجزا**

**باقی‌مانده:** T3 (ImageView scaleType) · T2 (transforms/density/insets) · T5..T10 · CONT-98 (۹ ترک) · CONT-89/92/93 · F-NEW-381.

**Evidence:** `evidence/cont99/evidence.json` (بخش t4) · commits `67a4d401` + `da1909fd` · registry **719** روت.
