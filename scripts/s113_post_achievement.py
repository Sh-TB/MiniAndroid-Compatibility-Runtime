#!/usr/bin/env python3
"""S113 — post the full-GUI achievement update (with images) on #353."""
import json, urllib.request

TOKEN = open("/tmp/.gh_token").read().strip()
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
RAW = "https://raw.githubusercontent.com/Sh-TB/MiniAndroid-Compatibility-Runtime/main"

body = f"""## 🏆 ACHIEVEMENT #9 — UPGRADE: HTML5/WebView FULL-GUI RENDER (not just execution)

**Honest correction first:** the S112 comment below claimed mykanji "rendered" — under the render law that was a **false visual closure**. The S112 image showed raw unstyled text blocks (224 colors, zero layout). The user was right: *loading is not the criterion — the complete graphical interface must run*. This wave (S113) rebuilt the engine to actually render it.

### The proof — mykanji (io.github.hathibelagal.mykanji), complete GUI:

![mykanji full GUI]({RAW}/evidence/s113_fullgui/mykanji_final/screenshot.png)

Everything in this frame is CSS-layout-engine rendered: pink `#ffeef8` page, flex-column **centering**, the white rounded card with pink border, the **mirrored cat PNG** decoded from the APK, `@font-face` Noto Serif JP, 🔥/🌸 **pseudo-element content**, `linear-gradient` buttons with rounded borders, inline-span merge ("0 / 106 kanji seen" on one line).

**Metrics:** 1953 unique colors (S112 jumble: 224) · 3 scripts / 0 js-errors · layout engine: block + flex-column, box model, media queries · pixel metric table below.

### Breakout-71 (the 9th-achievement anchor, still intact)

![breakout]({RAW}/evidence/s113_fullgui/gates/breakout/screenshot.png)

Canvas content **0.000% pixel drift** vs the S111/S112 anchor (only the top decor strip changed — improved by the WindowInsets fix).

### Generalization: 2 MORE plain-WebView HTML5 apps tested (user directive)

| App | Result | Evidence |
|---|---|---|
| io.github.hathibelagal.mykanji | ✅ **FULL GUI** (3rd generalized APK with image) | screenshot above |
| org.asafonov.blockbuster | ⚠️ **real game frame** (title, green paddle with border+shadow, field; 106 CSS rules, 0 errors) — some positioning gaps remain | ![blockbuster]({RAW}/evidence/s113_fullgui/blockbuster_run1/screenshot.png) |
| org.asafonov.accelerace | ⚠️ partial — CSS applied (dark bg), UI not yet visible (JS builds the menu; needs more DOM depth) | — |
| blidraughts | ⏳ unchanged from S112 (ROOT-058 open: R8-de-enum'd androidx feature registry) | — |

**Does the HTML5 fix affect other apps? YES — the capability is generic** (zero package checks): every WebView-family APK routes through the same layout+paint engine. 4 HTML5 APKs exercised this wave.

### What was built (root-cause laws, not patches)

- **S113 layout engine**: CSS box model (padding/margin/border/radius shorthands, auto-centering, max-width, %-sizes), block + flex-column subset (align-items/justify-content center), max-content shrink + block fill laws, inline-merge (spans fold into parent text), whitespace-only text renders nothing, media queries (`@media max/min-width`, nested-brace parse), `::before/::after` content, gradients, rounded rects, border rings, background images (contain + mirror), text/box shadows, `@font-face` → FreeType app-font registration, `position:fixed/absolute` overlays.
- **ROOT-059**: WindowInsets materialization law — androidx `Impl.<clinit>` built `CONSUMED` via `Builder.build().consumeDisplayCutout()…` and NPEd 21× because R8 outlines hit a `WindowInsets$Builder` REC-MISS (null `mPlatformInsets`). New `WindowInsetsShadow` + F-141 guard routing for shadow-claimed classes. Insets NPE family: **21 → 0** (mykanji now: 3 non-fatal Toolbar-family errors — new ROOT-061 frontier).
- **ROOT-060**: `HTMLMediaElement.play()/pause()` (promise-returning, silent-resolution) + `getElementsByClassName`.
- **querySelectorAll** now uses the real selector matcher (compound + descendant) — the old tag-only collect answered EMPTY for `.choice-button`, so game.js registered **zero** click listeners (buttons tap-dead). Now: click → browser events → JS listener fires, game logic mutates state, 0 js-errors.
- **WebView touch law**: WebView IS a touch target; the tap *point* (view-local) drives the browser hit-test (was: view center).

### Regression gates (byte-identical)

| Gate | SHA | Verdict |
|---|---|---|
| dooz | `a2ba4a49` | ✅ byte-identical |
| ballbreak | `fe797c19` | ✅ byte-identical |
| breakout | `568342fb` → canvas-only | ✅ 0.000% content drift |

### Did the 3 tickets + comments help? YES.

#353's WebView content-model map and the Breakout-71 precedent (from the evidence comments) were the working plan for S109→S113: the static-HTML trap called out in #353 is exactly what the execution frontier killed first, and this wave closes the *render* frontier the tickets exposed. The tickets also caught the outdated "no JS engine" claim, the Telegram→Forkgram naming, and the oversized image sets — all fixed in S111.

### Open frontiers (honest)

- **ROOT-061**: post-click appcompat drain (`invalidatePanelMenu → postOnAnimation → WindowDecorActionBar.<init>`) segfaults in the DEX engine — the success-dialog *paint* is captured in game logic but not yet as a frame.
- accelerace UI depth; blidraughts ROOT-058; Telegram login pixels (R$styleable + text-draw).

---

**TL;DR (فارسی):** دستاورد نهم ارتقا یافت — برنامه‌های HTML5/WebView دیگر فقط «اجرا» نمی‌شوند، **رابط گرافیکی کامل** رندر می‌شود. mykanji الان واقعاً کامل لود شده: پس‌زمینه صورتی، کارت سفید گردگوشه با حاشیه، عکس گربه، دکمه‌های گرادیانی با متن چپ‌چین، فونت اختصاصی — با تصویر بالا اثبات شده. بازی Breakout هم تصویرش همین‌طور هست و پیکسل‌هایش ذره‌ای تغییر نکرده. دو برنامه HTML5 دیگر هم تست شد: Block'Buster فریم واقعی بازی را رندر می‌کند، accelerace نیمه‌کاره است (صادقانه گزارش می‌شود). تیکت‌های سه‌گانه خیلی کمک کردند — نقشه راه همین موج از همان‌جا آمد.
"""

def api(method, url, data):
    req = urllib.request.Request(url, data=json.dumps(data).encode(),
                                 method=method,
                                 headers={"Authorization": f"Bearer {TOKEN}",
                                          "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req) as r:
        return json.load(r)

res = api("POST", f"https://api.github.com/repos/{REPO}/issues/353/comments",
          {"body": body})
print("posted:", res.get("html_url"))
