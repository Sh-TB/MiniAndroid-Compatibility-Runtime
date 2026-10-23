#!/usr/bin/env python3
"""CONT-13 — post the batch-3 ledger to GitHub Issue #387 (Persian, per task)."""
import json, subprocess, sys

BODY = r"""
# CONT-13 — پوشش ۲۰ قطار (باتچ ۳ دستور ۲۰تایی) — مشکل مشترک خانواده‌ی Fossify حل شد ✅

**مشکلش حل شد.** باتچ ۳ (۲۰ عنوان) روی HEAD واقعی `856261cf` (بعد از CONT-12) اجرا شد. نکته‌ی مهم: کانتینر دوباره به اسنپ‌شات قدیمی CONT-10 برگشته بود (اِVENT ثبت‌شده در b0620f75) — با `git fetch` تشخیص داده شد (۳۰۹ کامیت عقب‌تر)، ریست به origin/main و بیلد از درخت واقعی قبل از هر ران.

## ترکیب باتچ (۲۰ عنوان، استور تازه، پنجره ۹۰ ثانیه)

- **A. بازمانده‌های چتر Object.getClass (۱۳):** prism، wocheneinkauf، matewave، sparkledns، aurora، awagam، webstack، compose_stopwatch، notepad، k9، audiobook، goodtime، netguard
- **B. خانواده‌ی Fossify (۴):** fossify_math / notes / clock / calendar (استخر F-NEW-515)
- **C. خانواده‌ی List.size (۳):** dmfs_tasks، surgeengine، bouncy

هارنس: `scripts/cont13_batch20.py` (قانون سرشماری: استور تازه → install → ران با هویت نصب‌شده → امضای uncaught نهایی + متریک پیکسل). نتایج: `evidence/cont13/batch20_census.json`.

## ریشه‌ی تکرارشونده‌ی این باتچ — F-NEW-518

هر چهار عنوان Fossify روی **یک لنگر مشترک** مردند:
`PackageManager$NameNotFoundException` (org.fossify.thankyou) در `Lo5/f;.U pc=12` → unwind دفرشده → **مرگ APP BOUNDARY** در `SplashActivity.onCreate`.

زنجیره‌ی ریشه (ماشین-اثبات‌شده):
- حقیقت DEX (با `scripts/cont9_dexdump.py` روی base.apk نصب‌شده): `Lo5/f;.U(Landroid/content/Context;)Z` **try-table دارد** که invoke را می‌پوشاند و یک هندلر تایپ‌دار `Ljava/lang/Exception;` → pc=17 (`return false` = الگوی Kotlin `catch (e: Exception) { false }`). یعنی catch اپ **قانونی** است.
- حقیقت موتور: `is_exception_subtype(NameNotFoundException, Exception)` → **FALSE** — کلاس نه در `kBuiltinExcParent` بود، نه در `class_to_superclass_` (کلاس فریم‌ورک)، و ردیف `AndroidException → Exception` پشت گیت آزمایش F-NEW-368 حبس بود.
- فکت AOSP: `PackageManager.NameNotFoundException extends android.util.AndroidException` و `AndroidException extends java.lang.Exception`.

**فیکس (عمومی، غیرشرطی):** دو ردیف والد در `kBuiltinExcTable` (+ ردیف همتای `ApplicationNotFoundException`) با پیشینه‌ی FIX-D12-ADJACENT: زنجیره‌ی استثناهای پلتفرم فکت AOSP است، نه آزمایش‌گیت‌پذیر.

## اثر سرشماری (قبل → بعد، همان ۲۰ عنوان)

| عنوان | قبل | بعد |
|---|---|---|
| fossify_math | مرگ قبل از لود | **رندر UI واقعی MainActivity** — آیکون‌های تولبار، ۱۳٬۰۷۱ پیکسل محتوا (`evidence/cont13/fossify_math_post_f518.png`) |
| fossify_calendar | مرگ قبل از لود | **رندر UI واقعی** ۱۲٬۳۳۶ px |
| fossify_notes | مرگ قبل از لود | از splash گذشت → MainActivity (چهره‌ی بعدی: NPE `ColorStateList.getDefaultColor`) |
| fossify_clock | مرگ قبل از لود | از splash گذشت (چهره‌ی بعدی: NSM غیرکشنده‌ی FitWindows — upstream خودش می‌گیرد: «Oh well») |
| netguard | — | ۲۷٬۳۳۵ px محتوا |
| bouncy | — | rc=0، ۷۲٬۶۲۲ px |

قبل: ۱/۲۰ با محتوای واقعی → بعد: **۴/۲۰ رندر محتوای واقعی**؛ خانواده‌ی Fossify از «کرش قبل از لود» به «UI رندرشده» رسید — معیار «حداقل صفحه‌ی لود» برای خانواده محقق شد.

## چهره‌های باقی‌مانده (صادقانه ثبت شد، بدون بستن کاذب)

1. NPE `ColorStateList.getDefaultColor` (notes + batterymonitor در سرشماری — تکرار ×۲، کاندیدای فیکس بعدی)
2. CNF/NSM لودر compose-locals (matewave/sparkledns — همان کلاس AndroidCompositionLocals)
3. ENOENT اولین-خواندن DataStore (awagam/compose_stopwatch — باید به هندلر زنجیره‌ی کوروتین برسد؛ چهره‌ی مرزی F-NEW-515)
4. تک‌چهره‌های null-contract (prism/wocheneinkauf/aurora/webstack/audiobook/goodtime/dmfs/surgeengine) — استخر F-NEW-516
5. k9: چهره‌ی Koin (NoDefinitionFoundException)

## راستی‌آزمایی

| گیت | نتیجه |
|---|---|
| لنگرها | ۵/۵ **رانش صفر** prefix-یکسان با رکوردهای rebased: chess `a0319686` / opencalc `63020bc7` / microtimer `bbd350b6` / unote `7481e9b4` / tower3d `11a38a5a` |
| negatives | **۱۹/۱۹** (بعد از بازتولید پروب‌استور در مسیر هارنس s41 یعنی `run/gatea/probe_store` — عدد قبلی ۹/۱۹ آرتیفکت استور کهنه بود، ریشه‌یابی شد، رگرسیون ران‌تایم نبود) |
| selftest | ۱۳/۱۳ PASS |
| رجیستری | ۸۳۲ → **۸۳۳** (F-NEW-518 ROOT-CAUSED-FIXED، id-unique، بدون تورم) |

شواهد: `evidence/cont13/CONT13_BATCH3_LEDGER.md` + `batch20_census.json` + دو اسکرین‌شات. موج بعدی: ColorStateList null-producer (تکرار ×۲)، خانواده‌ی لودر compose-locals، چهره‌ی مرزی DataStore؛ سپس باتچ ۴.
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
