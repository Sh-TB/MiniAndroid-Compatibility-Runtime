#!/usr/bin/env python3
"""CONT-14-B4 — post the batch-4 ledger to GitHub Issue #387 (Persian, per task)."""
import json, subprocess, sys

BODY = r"""
# CONT-14-B4 — پوشش ۲۰ قطار (باتچ ۴) — چهره‌ی تکرارشونده‌ی ×۲ حل شد ✅

**مشکلش حل شد.** چهره‌ای که باتچ ۳ ثبت کرده بود (NPE «ColorStateList.getDefaultColor روی null» در `PagerTitleStrip.<init> pc=138` — تکرار ×۲: fossify_notes + batterymonitor) ریشه‌یابی و به‌صورت **عمومی** فیکس شد: F-NEW-519. سشن قبلی از اسنپ‌شات CONT-10 شروع شده بود؛ با `git fetch` تشخیص و روی HEAD واقعی `717e0058` سینک شد (۰ کار محلی از دست نرفت).

## ریشه — داستان دو-مظنونه‌ای

پیام خطا مظنون اشتباهی را نام می‌برد. **حقیقت DEX** (ماشین-اثبات‌شده از بایت‌های APK با `scripts/cont14_pager_dex_truth.py`):

```
0x10c: invoke-virtual TextView;->getTextColors()   ← سازنده‌ی null اینجاست
0x114: invoke-virtual ColorStateList;->getDefaultColor()  ← NPE اینجا
```

`0x114` بایت = **۱۳۸ واحد ۱۶بیتی** — پس pc=138 سرشماری دقیقاً همین‌جاست. یعنی گیرنده‌ی null، **خروجی `TextView.getTextColors()`** است که در موتور هیچ قانونی نداشت → null. قانون CSL خودِ موتور سالم بود.

قانون AOSP (TextView.java، سورس-محور): مقداردهی اولیه‌ی فیلد `mTextColor = ColorStateList.valueOf(0xFF000000)` تضمین می‌کند `getTextColors()` هرگز null برنگرداند؛ `setTextColor(int)` آن را با `valueOf(color)` جایگزین می‌کند؛ `setTextColor(ColorStateList)` خودِ آبجکت را ذخیره می‌کند.

**فیکس (فقط سمت خواندن، بدون تغییر setter، بدون کوپلینگ رندرر):**
1. آبجکت CSL ثبت‌شده (arm دوم setter) هنوز زنده → بازگشت **همان آبجکت** (قرارداد هویت)؛
2. وگرنه arm `valueOf`: رنگ ثبت‌شده (explicit یا style-resolved — پاریتی رندرر با قانون F-NEW-301) → `csl_wrap_single`؛ unset → مشکی پیش‌فرض فیلد / سفید خانواده‌ی Button.

## اثر (قبل → بعد)

| عنوان | قبل | بعد |
|---|---|---|
| batterymonitor | rc=1 در ۱.۹ ثانیه، NPE در pc=138، صفر نود | **درخت UI واقعی ساخته شد**: LinearLayout → ViewPager → PagerTitleStrip children=3 با عناوین واقعی **HISTORY / CURRENT STATE / ALARMS** — PARTIAL SUCCESS |
| fossify_notes | چهره‌ی CSL سرشماری + هالت‌های F084 | **۰ استثنای uncaught** در ۹۰ و ۳۰۰ ثانیه، پایدار پس از splash (چهره‌ی بعدی: مرز draw-path سراسری — صادقانه ثبت شد) |

چهره‌های بعدی batterymonitor غیرکشنده و لجرد شدند: Shizuku/Sui provider init + NNFE مربوط به `AppLocalesMetadataHolderService` که androidx خودش می‌گیرد (لاگ «Service not found» — زنجیره‌ی F-NEW-518 کار می‌کند) و ISE قانونی AOSP را rethrow می‌کند؛ در این APK مانیفست ادغام‌شده آن سرویس را ندارد و مسیر androidx برای همین طراحی شده — موتور اکنون همان بقا را آینه می‌کند.

## سرشماری باتچ ۴ (همان ۲۰ عنوان باتچ ۳، باینری پس‌فیکس)

- محتوای واقعی حفظ شد: **۴/۲۰** — bouncy ۷۲٬۶۲۲ / netguard ۲۷٬۳۳۵ / fossify_math ۱۳٬۰۷۱ / fossify_calendar ۱۲٬۳۳۶ پیکسل
- **رانش صفر: هر ۲۰ اسکرین‌شات SHA بایت-یکسان با باتچ ۳** — قانون فقط-خواندن چیزی را که به این چهره نخورده جابه‌جا نمی‌کند
- چهره‌های نام‌دار باتچ ۳ بدون تغییر (صادقانه): لودر compose-locals (matewave/sparkledns)، ENOENT اولین-خواندن DataStore (awagam/compose_stopwatch)، استخر f141، Koin k9، NO_ROOT (goodtime/surgeengine)

## راستی‌آزمایی

| گیت | نتیجه |
|---|---|
| باینری بازسازی‌شده | SHA بایت متفاوت (۳۳۰۳۸c78) — **صادقانه ثبت شد**؛ لنگرها اثبات وفاداری: ۵/۵ EXACT قبل از فیکس |
| لنگرها پس از فیکس | ۵/۵ **رانش صفر** (chess `a0319686` / opencalc `63020bc7` / microtimer `bbd350b6` / unote `7481e9b4` / tower3d `11a38a5a`) |
| باتچ ۲۰ | ۲۰/۲۰ بایت-یکسان |
| negatives | **۱۹/۱۹** (پروب‌استور در `run/gatea/probe_store` بازتولید شد) |
| selftest | ۱۳/۱۳ PASS |
| رجیستری | ۸۳۳ → **۸۳۴** (F-NEW-519 ROOT-CAUSED-FIXED، id-unique) |

پوش: `578c63d9`. شواهد: `evidence/cont14/CONT14_BATCH4_LEDGER.md` + `batch20_census_v2.json` + `batterymonitor_view_tree.json` (درخت UI واقعی) + `wave_faces_{prefix,postfix}.json`. موج بعدی: خانواده‌ی لودر compose-locals (S102) + مسیریابی ENOENT داده‌استور؛ سپس باتچ ۵ از ۲۰.
"""

def gh_token():
    out = subprocess.run(["git", "credential", "fill"],
                         input="protocol=https\nhost=github.com\n\n",
                         capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return None

def main():
    token = gh_token()
    if not token:
        print("NO TOKEN"); sys.exit(1)
    r = subprocess.run([
        "curl", "-s", "-X", "POST",
        "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/387/comments",
        "-H", f"Authorization: token {token}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"body": BODY}),
    ], capture_output=True, text=True)
    try:
        resp = r.json()
        print("posted:", resp.get("id"), resp.get("html_url"))
    except Exception:
        print("FAIL", r.stdout[:300])

if __name__ == "__main__":
    main()
