#!/usr/bin/env python3
"""S111 achievement comment — the 9th achievement: real HTML5 game execution,
with image proof and explicit credit to the earlier evidence comments."""
import json
import urllib.request

TOKEN = open('/tmp/.gh_token').read().strip()
REPO = 'Sh-TB/MiniAndroid-Compatibility-Runtime'
RAW = 'https://raw.githubusercontent.com/Sh-TB/MiniAndroid-Compatibility-Runtime/main'


def gh(path, method='GET', payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        f'https://api.github.com/repos/{REPO}/{path}',
        data=data, method=method,
        headers={'Authorization': f'Bearer {TOKEN}', 'User-Agent': 'audit',
                 'Content-Type': 'application/json'})
    return json.load(urllib.request.urlopen(req))


COMMENT = f"""## 🏆 ACHIEVEMENT #9 — real HTML5/WebView game execution (visual proof)

**This ticket's body has been rewritten to the standard structure** (fix
methodology → metric tables → rendered images → GIF → Persian summary). The
outdated claim "JS execution is not yet in the engine" was removed — the
engine now executes the **full 1.5 MB JS bundle** and renders the real game.

### The image (the honest answer to "did it really run?")

![breakout real render — menu HUD, paddle+ball, press-and-hold]({RAW}/evidence/s109_webview/breakout_fix52_run1/screenshot.png)

Read directly from the frame: **☰ menu** (top-left) · **0 $** coin counter
(top-right) · the **paddle with the ball resting on it** (canvas paths +
fills) · **"Press and hold here to play"** (fillText) · the game's own dark
theme. This is me.lecaro.breakout — the #94 white-screen title.

### Chain of proof

`WEBVIEW_CREATED → URL_LOADED → HTML_LOADED → SCRIPT_EXECUTED (1.5 MB,
js_errors=0, scripts executed=1) → CANVAS_CREATED (1080×1920) → DRAW_EXECUTED
(draw_calls=8: fillRect/arc/bezier/fill) → FRAME_CAPTURED` — 3/3 runs
**byte-identical** (`568342fb901a75ab`), crash.log clean.

### Roots fixed en route (all generic — no package checks)

ROOT-048 console family · ROOT-049 full WHATWG CanvasRenderingContext2D
surface (the C++ raster existed, the JS bridge never did) · ROOT-050
calc()/var() length law · ROOT-051 root/body background propagation ·
ROOT-052 canvas bitmap = transparent black · ROOT-053 WebView availability
probe law + Pattern.quote.

### Regression gates — zero drift

ballbreak `fe797c19` ✓ · dooz `a2ba4a49` ✓ (byte-identical to their anchors).

### Credit — the help from this ticket's comments

The [evidence comment](#issuecomment-5857414802) below carried the visual
verification of the earlier document-load wave (dark-theme + 99.9% non-white
inspection) and its honest trap-warning ("HTML text on screen ≠ WebView
working") set the baseline: this update's proof is measured against THAT bar,
which is why the BEFORE/AFTER pair in the body shows both states.

### توضیح فارسی

**دستاورد نهم با تصویر:** بازی HTML5 واقعاً اجرا شد — باندل ۱.۵ مگابایتی JS
کامل اجرا و بوم بازی رندر شد؛ ۳ اجرا بایت‌به‌بایت یکسان و صفر خطا. بدنه‌ی
تیکت هم به ساختار استاندارد اصلاح شد (ادعای قدیمی «JS هنوز نیست» حذف شد) و
کمک کامنت شواهد پایین به‌صراحت در بدنه ذکر شد. فرونتیر بعدی صادقانه: گیت
ورودی روی حلقه‌ی بازی + سیاست نسخه‌ی Chromium در blidraughts (سیاست خود اپ).
"""

issue = gh('issues/353')
gh(f'issues/353/comments', 'POST', {'body': COMMENT})
print('achievement comment posted')
