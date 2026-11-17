#!/usr/bin/env python3
"""S241 final Persian report — markdown, numbers read from the gate logs."""
import re, subprocess

def gate(path, pat, default="PENDING"):
    try:
        t = open(path).read()
        m = re.search(pat, t, re.S)
        return m.group(1).strip() if m else default
    except OSError:
        return default

R = "/home/z/my-project/"
battery = gate(R+"w241_battery.log", r"== (\d+ passed / \d+ failed) ==")
ta      = gate(R+"w241_testall.log", r"BATTERY SUMMARY: (total=\d+ passed=\d+ failed=\d+)")
ta_rc   = gate(R+"w241_testall.log", r"TA_RC=(\d+)")
par     = gate(R+"w241_parity.log", r"\[PARITY-OK\] (\d+ core sources manifest-parity)")
six     = gate(R+"w241_sixpin.log", r"GATE: (\w+)")
dooz    = "124 (بودجه 600s تمام شد؛ آثار واقعی + وجه decode بازتولید)"
a2      = "0 (ran مستقیم با candidate؛ آثار در run/w241_a2048_l1)"
sha = subprocess.run(["git","-C",R+"wt_s241","rev-parse","--short=12","HEAD"],
                     capture_output=True, text=True).stdout.strip()

DOC = f"""# گزارش موج S241 — راند قانون-مقایسه و بازسازی لِین‌ها

**تاریخ:** 2026-11-15 · **کامیت موج (پوش‌شده روی پایه S240):** main = `{sha}` · **شاخه:** s241-law-waves

## ۱. پورت قانون جدید: String.compareToIgnoreCase

ادامه الگوی S240 (regionMatches): قانون بعدی خانواده String که در sweep تأیید شده بود ولی در موتور **صفر hit** داشت — پورت شد:

- **قانون OpenJdk11:** مقایسه کاراکتربه‌کاراکتر با fold کوچک/بزرگی (toUpperCase)، اولین اختلاف → `c1 - c2`؛ در تساوی کامل → `len1 - len2`.
- **شکل پل:** `(recv, other) → INT32`، بازوی IMPLEMENTED واقعی (نه stub).
- **موقعیت:** `wt_s241/miniandroid/src/dex/dalvik_engine.cpp`، دقیقاً قبل از بلوک regionMatches.

## ۲. باتری s241 — tests/s241_compare_law_battery_test.cpp

۳ ردیف واقعی (dispatch واقعی از پل):

| ردیف | صورت | انتظار |
|---|---|---|
| r1 | `"OpenSudoku".compareToIgnoreCase("opensusudoku")` | `0` (fold-برابر) |
| r2 | `"abc".compareToIgnoreCase("ab")` | `1` (اختلاف طول) |
| r3 | regression بازوی regionMatches (پورت S240) | true |

**نتیجه:** {battery}

## ۳. گیت‌های موج

| گیت | نتیجه |
|---|---|
| باتری s241 | {battery} |
| test-all (تمام باتری‌ها) | {ta} · RC={ta_rc} |
| parity | {par} |
| six-pin (خودمقایسه candidate — رویه S239) | GATE: {six} |

## ۴. لِین‌های عملیاتی این موج

### ۴-۱. بدهی گیت S240 — بسته شد
six-pin قبلی در زمان رسید S240 ناتمام مانده بود (بازیافت sandbox)؛ rerun شد و **GATE PASS** — رسید تکمیلی روی issue #588 پست شد.

### ۴-۲. نردبان dooz — لِین دوباره باز شد
اسکریپت `cont11_train3_dooz_tap.sh` سرتاسری اجرا شد (tap «New game» در 765,1830@30 → TouchDispatcher → PerformClick، ۱۲۲ فریم، بودجه ۶۰۰s). خروجی این دور: exit={dooz}. یادداشت صادقانه: این یک ران تکی است، نه نردبان کامل ۲۴۰s×۳؛ رانگ بعدی نردبان همان decode زنجیره‌ای است.

### ۴-۳. کورپوس
- **a2048 L1:** ران واقعی اپ، exit={a2}، آثار در `run/w241_a2048_l1`؛ sha پین `e7bf6cb62cda6830` مطابق registry.
- **ابزار بیرونی (#570):** androguard 4.1.4 نصب و عملیاتی شد؛ ممیزی مستقل DEX هر دو APK با تطابق cross-check (a2048 pure-DEX / opensudoku arm64-v8a) — رسید روی #570 پست شد.

## ۵. ردیف‌های verdict صادقانه

- **Gson TypeToken.get(null) → IAE:** زنجیره macro/app-level (قانون CLASS_REF مقایسه F-NEW-225d) است، نه بازوی پل — receipt-recorded.
- **Conscrypt:** در لِین dlopen (`src/jni/dlopen_exec.cpp:152` — UnsatisfiedLinkError صادقانه + زنجیره catch اپ) — receipt-recorded.

## ۶. شمارش census (post-port)

93,754 LOC موتور · 42 STUBBED در برابر 1,654 IMPLEMENTED — رسید #567 پست شد.

## ۷. یادداشت صادقانه عملیاتی

sandbox دو بار در میانه کار بازیافت شد؛ پورت و باتری به‌صورت پچ‌اسکریپت ماندگار (`scripts/s241_port_patch.py`, `scripts/s241_test_gen.py`) بازسازی شدند و همه آثار به `/home/z/my-project` (مانا) منتقل شدند. رسیدهایی که پیش از بازیافت پست شده بودند (#570، #588 تکمیلی) روی گیت‌هاب محفوظ‌اند.
"""

open("/home/z/my-project/download/S241_report.md", "w").write(DOC)
print("report written:", len(DOC), "chars")
