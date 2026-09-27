#!/usr/bin/env python3
"""S112: post the ACHIEVEMENT #9 generalization-wave comment on #353."""
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


COMMENT = f"""## 🏆 ACHIEVEMENT #9 — GENERALIZATION WAVE: the HTML5 engine runs OTHER apps too (2nd APK proof + image)

The [Breakout 71 real-render proof](#issuecomment-5858470298) stands (image
there — menu HUD, paddle+ball, 3/3 byte-identical). Per the follow-up
directive ("does it affect OTHER Android apps/games — does it run them
too?"), this wave ran the WebView family BEYOND Breakout. Honest answer:
**yes for the app family — image below; the next Capacitor game reached
Bridge init and is the open frontier.**

### Proof APK #2 — MyKanji (io.github.hathibelagal.mykanji, plain WebView app)

![mykanji HTML5 document render — real text, 224 unique colors]({RAW}/evidence/s112_html5_generalization/mykanji_run1/screenshot.png)

| run fact | value |
|---|---|
| WebView | created (`o146`), `loadUrl(file:///android_asset/index.html)` → **engine ok, 3406 bytes** |
| JS | **scripts executed=3, js_errors=0**, raf_pending=2 |
| pixels | 1080×1920, **224 unique colors**, black text body + gray UI — the real document, not a blank frame |

Same engine, same WebView path as Breakout, ZERO per-app patches.

### Proof APK #3 (in progress) — blidraughts (com.vovagorodok.blidraughts, Capacitor game, audit reopen #74)

Progress this wave — its own startup gate is now BEATEN and the Capacitor
Bridge builds:

1. **ROOT-054** — WebView provider identity = platform build metadata
   (`com.android.webview`, API-34-era `120.0.6099.144`): the app's own
   `parseInt(versionName.split(".")[0]) < MIN_VERSION` gate now PASSES —
   the "Update required!" dialog is GONE.
2. **ROOT-055** — `View.getLayoutParams` never-null parent-type law:
   the real-DEX `CoordinatorLayout.prepareChildren` NPE is dead; the
   `no_webview` fallback no longer triggers.
3. **ROOT-056** — `findViewById(NO_ID)` law: no more phantom root matches.
4. **ROOT-057** — `CookieManager.getInstance()` singleton law: the
   Capacitor/Cordova cookie chain survives Bridge build.

Current blocker (honest): inside R8-transformed androidx.webkit, the
feature-registry lookup finds zero name matches and throws its own
`RuntimeException("Unknown feature WEB_MESSAGE_LISTENER")` at APP-BOUNDARY
— **ROOT-058** is the open root (app-DEX static-init gap for
R8-de-enum'd androidx registries; ground truth read from the real
classes.dex). The frame is still blank — no render claim made.

### Regression gates — zero pixel drift through all 4 root fixes

breakout `568342fb` ✓ · ballbreak `fe797c19` ✓ · dooz `a2ba4a49` ✓
(byte-identical to their anchors)

### The 3-ticket knowledge transfer — did it help?

Yes, measurably: #353's evidence comment set the visual-verification bar
("HTML text on screen ≠ WebView working") and its BEFORE/AFTER trap
warning is exactly what this wave re-applied to mykanji/blidraughts; #354's
5 engine laws + honest-audit method shaped the reopen #74 handling; #355's
error-chain discipline (count → root → law) is the loop used for all four
roots above. The comments are credited in each ticket's dedicated section.

### توضیح فارسی

**پاسخ سوال «آیا برای بقیه هم کار می‌کند؟»:** بله — اپلیکیشن HTML5 دوم
(MyKanji) با همین موتور و بدون هیچ پچ اختصاصی رندر شد: WebView ساخته شد،
`index.html` لود شد، ۳ اسکریپت JS اجرا شد، صفر خطای JS، و متن واقعی سند
روی تصویر است (۲۲۴ رنگ واقعی، نه فریم خالی). بازی blidraughts هم جلو
رفت: گیت «Update required» خودِ اپ رد شد، کرش‌های Layout و Cookie رفع شد
(۴ قانون جدید ROOT-054..057) و Bridge کاپاسیتور تا لود پلاگین‌ها ساخت شد؛
تنها مانده باگ داخلی androidx.webkit (ROOT-058) که ثبت شده است. هر سه
گیت رگرسیون بایت‌به‌بایت بدون تغییر مانده‌اند. تصویر Breakout در کامنت
دستاورد نهم بالا همین تیکت هست.
"""

issue = gh('issues/353')
gh('issues/353/comments', 'POST', {'body': COMMENT})
print('generalization comment posted')
