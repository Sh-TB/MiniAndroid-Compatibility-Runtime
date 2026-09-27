#!/usr/bin/env python3
"""S111 ticket edit wave — rewrite #353/#354/#355 to the standard structure:
fix methodology + metric tables + rendered images + GIF + Persian summary.
Fixes: outdated JS claim (#353), hotdeath broken link (#354), Telegram->Forkgram
naming (#355), oversized inline image sets (all) — with explicit references to
the evidence comments (knowledge-transfer requirement)."""
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


BODY_353 = f"""# HTML5 / WebView — from white screen to REAL JS execution (Breakout 71 runs its game loop)

Knowledge-transfer report, standard structure: bug-fix methodology → metric
tables → rendered images → GIF → Persian summary. Built on the evidence
comment below (visual verification of the document-load wave) — this update
extends that story to **full JS execution**.

## 1. The bug (and the trap that hid it)

HTML5 games are WebView + JS packages. On this runtime they were **white
screens** (#94 me.lecaro.breakout, `STATE-NOT-LOADED`; audit reopen #74/#205
"requires a WebView"). The first fix (F-085 content model, see the evidence
comment) made the DOCUMENT text render — but that was the **static-HTML
trap**: a header painted from HTML text is NOT HTML5 execution. The honest
frontier: the 1.5 MB JS bundle never executed.

## 2. Bug-fix methodology — ROOT-048 … ROOT-053 (six structural laws)

Each root was found by tracing the engine log to the first divergent call,
then fixed by the AOSP/WHATWG/JDK law — **no package checks, no per-app
patches**:

| root | bug (engine truth) | law applied |
|---|---|---|
| ROOT-048 | console had only log/info/warn/error → `console.debug` in the game's migration runner threw `not a function` → **all 8 migrations failed + main script aborted** (`scripts executed=0`) | Chromium DevTools console contract: debug/trace/dir/dirxml/table + time/timeEnd/count/group/assert/clear all exist as functions |
| ROOT-049 | `getContext('2d')` registered **6 of 30+ members** — the full C++ Canvas2D raster existed but was unreachable from JS (`draw_calls=0`) | WHATWG CanvasRenderingContext2D: full surface (paths/rects/text/transforms/gradients/patterns/getImageData/putImageData) + 8 style attributes, bound to the real raster; `ellipse` via exact scaled-arc; missing `transform` added |
| ROOT-050 | `height:calc(var(--vh,1vh)*100)` resolved to **0** (atof on "calc(") → canvas collapsed to a ~30 px strip | CSS: var(--x, fallback) fallback syntax + unit-aware calc product; body custom-props resync for `var(--background1)` |
| ROOT-051 | page stayed white although body had `--background1:#030c23` | CSS canvas-background law: root/body background propagates to the viewport before children paint |
| ROOT-052 | canvas bitmap initialized **opaque white** → undrawn pixels painted white over the page | WHATWG: resize resets the bitmap to **transparent black** |
| ROOT-053 | `WebView.getCurrentWebViewPackage` probe → generic-miss null → Capacitor apps render "requires a WebView" (#74) | AOSP: a device that ships a WebView answers **non-null** WebViewPackageInfo (+ honest `1.0.0` identity, heap-field seeded) + JDK `Pattern.quote` + quoted-literal split |

## 3. Metric tables (3-run, deterministic)

| metric | BEFORE (static-HTML trap) | AFTER (S111) |
|---|---|---|
| JS bundle | not executed | **1.5 MB executes** |
| migrations | 8 × failed | **8/8 ran** |
| `scripts executed` | 0 | **1** |
| `js_errors` | 1 | **0** |
| canvas draw calls | 0 | **8** (fillRect/arc/bezier/fill…) |
| rAF / timers | 2 / 6 | **3 / 5** (game loop armed) |
| screenshot SHA-16 | — | `568342fb901a75ab` ×3 (**byte-identical 3/3**) |
| errors (crash.log) | 0 | **0** |

## 4. Rendered images — the proof

| BEFORE — text-only header (the trap) | AFTER — the REAL game (JS + canvas) |
|---|---|
| ![before]({RAW}/evidence/s110_tickets/html5_breakout/screenshot.png) | ![after]({RAW}/evidence/s109_webview/breakout_fix52_run1/screenshot.png) |

The AFTER frame is the game's authentic UI rendered by the engine: **☰ menu**
(top-left), **0 $** coin counter (top-right), the **paddle with the ball
resting on it** (canvas paths + fills), and **"Press and hold here to play"**
(fillText) — on the game's own dark theme. Evidence:
`evidence/s109_webview/breakout_fix52_run1..3/`.

Reference (F-Droid official): [reference image]({RAW}/evidence/s110_tickets/html5_breakout/reference_froid.png)

## 5. Web family (animated GIF — real TLS browser)

![Mini Browser loading z.ai over real TLS]({RAW}/docs/evidence/canonical/com.miniandroid.browser.zai.gif)

More: example.com tap-driven state change —
[com.miniandroid.browser.gif]({RAW}/docs/evidence/canonical/com.miniandroid.browser.gif)

## 6. Honest remaining frontier

- **Input gate on the game loop**: touch → JS handler → state change → new
  frame is wired (`dispatch_click` forwards touchstart/pointer/mouse/click)
  but not yet proven on Breakout's canvas (next wave).
- **blidraughts (#74)**: the availability-probe chain now completes (non-null
  identity → version parse → the app's own **"Update required!" dialog**).
  The remaining gate is the app's own Chromium-major policy — the runtime is
  not Chromium and will not forge a version. Classified APP-POLICY.
- Localization strings (resource keys) — tracked with the theme work.

## 7. Help from the evidence comments

The [evidence comment](#issuecomment-5857414802) below (visual inspection of
the document-load state, 99.9% non-white px, dark theme verification) defined
the honest baseline this update builds on: without its trap-warning the JS
wave would have been reported against the wrong proof image.

## خلاصه فارسی (Persian TL;DR)

بازی HTML5 Breakout 71 (همان تیکت #۹۴) حالا **واقعاً اجرا** می‌شود — نه فقط
متن سند، بلکه **باندل ۱.۵ مگابایتی JS کامل اجرا شد** و بوم بازی با پدل و توپ و
منو رندر شد (تصویر AFTER بالا — دستاورد نهم). شیوه‌ی رفع: **۶ قانون ریشه‌ای**
بدون هیچ پچی برای بازی خاص — خانواده‌ی کامل console، سطح کامل Canvas2D (که
کد C++ آن از قبل بود ولی هرگز به JS وصل نشده بود!)، ارزیاب calc()/var()،
انتشار پس‌زمینه‌ی body، شفاف-سیاه بودن بوم، و قانون probe دسترس‌پذیری WebView
+ Pattern.quote. **۳ اجرا بایت‌به‌بایت یکسان** (`568342fb`)، صفر خطای JS.
فرونتیر صادقانه: گیت ورودی روی حلقه‌ی بازی و سیاست نسخه‌ی Chromium در
blidraughts (سیاست خود اپ، نه API گمشده). راهنمای کامنت شواهد پایین،
خط پایه‌ی صادقانه‌ی این موج بود.
"""

BODY_354 = f"""# Native game family — gameplay GIFs, 5 engine-bug laws, verified 3-run titles + the honest audit

Knowledge-transfer report, standard structure: bug-fix methodology → metric
tables → rendered images/GIF → Persian summary. Built on the evidence comment
below (fresh gates + click-dispatch verification).

## 1. The story arc (S79 → S110)

- **S79-S102 — interaction & media:** canonical tap pipeline
  (`--tap` / `--click-test`: DOWN → pressed frame → UP → PerformClick → real
  DEX `onClick`), real GIF decode (stb), the Mini Browser, 10-game full-load
  wave, autonomous gameplay planners (BFS snake, 2048 25-move ~208 pts,
  Minicraft house-building).
- **S106 — the 5 REAL engine bugs** (law-test fences, table below).
- **S107 — Compose pixels:** dooz renders the real Compose MaterialTheme
  surface.
- **S108-AUDIT — the honest correction:** all 128 S107 closures re-verified
  from pixels; **124 reopened as FALSE VISUAL CLOSURE**; **4 survived**
  3 byte-identical runs: bouncy #121, bobball #81, hotdeath #68,
  pinyinfdroid #166.

## 2. Bug-fix methodology — the 5 engine laws (S106)

| # | bug (silent law violation) | law applied |
|---|---|---|
| 1 | stroke-only vector paths drew NOTHING | fill/stroke independence (paths without fill must still stroke) |
| 2 | `Affine2D::pre_rotate` rotated counter-clockwise | `M*R^t` vs `M*R` — AOSP/Skia rotate(90) is clockwise |
| 3 | `layout_text` maxLines off-by-one | one extra empty line removed |
| 4 | `View.requestLayout()` was a silent no-op | layout_dirty traversal flag raised |
| 5 | group `android:alpha` + `state_checked` | group alpha inheritance + state-list pick API + audio module wired |

Plus **2 upstream stb bugs fixed** for real GIF animation (disposal-2
semantics, two_back OOB).

## 3. Verified gameplay evidence (real engine runs)

| bouncy (VERIFIED_3RUN #121) | bobball (VERIFIED_3RUN #81) |
|---|---|
| ![bouncy]({RAW}/docs/evidence/canonical/com.dozingcatsoftware.bouncy.gif) | ![bobball]({RAW}/docs/evidence/canonical/org.bobstuff.bobball.gif) |

| hotdeath (VERIFIED_3RUN #68) | fish.rings (input→state chains) |
|---|---|
| ![hotdeath]({RAW}/docs/evidence/canonical/com.smorgasbork.hotdeath.gif) | ![fishrings]({RAW}/docs/evidence/canonical/eu.veldsoft.fish.rings.gif) |

More gameplay GIFs (linked, not inlined, to keep this ticket light):
2048 (`com.miniandroid.g2048.gif`), Tetris (`com.miniandroid.tetris.gif`),
minicraft, snakeneon, tictactoe, tictactoedeluxe, dodge, nounours,
urlchecker — all in `docs/evidence/canonical/`.

## 4. Fresh gates at HEAD `d6a11ed`

| title | status | errors | shot SHA-16 | note |
|---|---|---|---|---|
| de.georgsieber.ballbreak | **SUCCESS** | **0** | `fe797c19ba1920ed` | byte-identical across **S107 → S111** (five root waves, zero drift) |
| io.github.yamin8000.dooz | SUCCESS | 6 (handled) | `a2ba4a4942152926` | Compose surface, stable |

Click dispatch (per the evidence comment): `GameView$1` listener + XML
`onClick` handlers (`onClickWeb`, `onClickHighscores`) — all DISPATCHED.

| ballbreak render | dooz render |
|---|---|
| ![ballbreak]({RAW}/evidence/s110_tickets/native_games/ballbreak/screenshot.png) | ![dooz]({RAW}/evidence/s110_tickets/native_games/dooz/screenshot.png) |

## 5. The honest state (post-audit)

The 128 reopened titles run (real DEX, deterministic) but their visual closure
needs the near-blank root chain. Contact sheets + per-ticket ledger:
`evidence/audit_s107/` (AUDIT_TABLE.md).

![audit contact sheet]({RAW}/evidence/audit_s107/contact_sheet_1.png)

## 6. Help from the evidence comments

The [evidence comment](#issuecomment-5857414959) supplied the click-dispatch
table and the honest dooz note (Compose taps = known open frontier) — both are
incorporated verbatim in §4 instead of being re-claimed.

## خلاصه فارسی (Persian TL;DR)

بازی‌های native در سه موج ساخته شدن: **پایپ‌لاین لمس واقعی**، **دی‌کد GIF
واقعی** (با رفع ۲ باگ upstream در stb)، و **پیکسل‌های Compose**. **۵ باگ واقعی
موتور** با fence های قانون پیدا و رفع شدن. ممیزی صادقانه: از ۱۲۸ کلوزور فقط
**۴ عنوان بصری تأیید شدن** و ۱۲۴ باز شدن. **گیت امروز:** ballbreak با صفر خطا
و SHA یکسان تا S111 (پنج موج ریشه، صفر رانش). لینک خراب تصویر hotdeath در
نسخه‌ی قبلی این تیکت اصلاح شد و GIF های اضافی به لینک تبدیل شدند.
"""


BODY_355 = f"""# Forkgram (Telegram fork) Classic 12.10.8.0 — errors 32 → 0, REAL login UI view tree, SQLite + serialization live

Knowledge-transfer report, standard structure: bug-fix methodology → metric
tables → rendered images → Persian summary. Naming note: the APK is
**Forkgram Classic** (`org.forkgram.classic`, vc 709208) — a community
**fork of Telegram** (fully-buildable FOSS base, no proprietary SMS/PRP bits);
the ticket previously read "Telegram" and has been corrected. Built on the two
evidence comments below (login-tree verification + the 6→0 zero-error update).

- 5 DEX files, ~41k classes, private JNI natives, private SQLite wrapper,
  desugared coroutine/stream machinery.
- Related: ticket #140 family (S107 measurement), worklog S108–S111.

## 1. Where it started (S107)

44.5k log rows of real `org/telegram` code, then death at
`MessagesController.getInstance` — `requireNonNull(null)` NPE — with **32
uncaught errors** and a flat white window.

## 2. Bug-fix methodology — 31 root laws (ROOT-016 … ROOT-047)

### S108 wave (ROOT-016 … 026) — the init chain

| root | law |
|---|---|
| 016 | `SharedPreferences.getStringSet` miss → **defValues** (killed the `whitelistedBots` stream NPE) |
| 017 | **`org.telegram.SQLite` 20 JNI natives over REAL sqlite3** (ROW→0/DONE→1 convention; INT64 handles were truncated to int32!) |
| 018 | **CLI JNI registration** — `miniandroid run` never registered the JNI bridge (every native of every app was fail-soft!) |
| 019 | J-vs-D primitive overload exact-descriptor law (`accept(J)` resolved to the `accept(D)` thrower → 3,697 ISE/run) |
| 020 | `TimeZone` full family (getDefault null killed ConnectionsManager) |
| 021/021b | `ThreadLocalRandom.current` + `ThreadLocal` OpenJDK law |
| 022 | `java.nio.ByteBuffer` family — OpenJDK buffer algebra |
| 023/024 | `SparseIntArray` family; `PowerManager.newWakeLock` + `AccountManager` |
| 025 | Telegram `NativeByteBuffer` natives (address→oid registry) |
| 018b | **unsupported-native fall-through law** (no handler → shadow, NOT silent 0/null) |
| 026 | `EnumMap/TreeMap/Hashtable` — receiver's runtime class bridges |

### S109 wave (ROOT-027 … 045) — the login UI tree

Drawable family (`getPaint`/`mutate`/`getBounds` never-null), PackageManager
query never-null, `setFragmentStack` stub REMOVED (real DEX fragment stack),
`Bitmap.createBitmap` signature law, SAX family, `AnimationUtils` family,
**AOSP measure-contract completion law** (the whole login tree rendered
0-SIZED before), `ViewGroup.onMeasure` child dispatch, **framework
`TextView.onDraw` TEXT law**, recursive descent measurement.

### S110 wave (ROOT-046, ROOT-047) — zero errors

| root | law |
|---|---|
| 046 | `java.security.KeyStore` family: `getInstance` **never null** (materializes + load/store no-op per AndroidKeyStore contract); `containsAlias` honest **false** → Telegram takes its degraded fingerprint path instead of dying |
| 047 | `Activity.getBaseContext()` **never null** (AOSP: `attach()` binds mBase before onCreate; per-activity base map + application-context fallback) — killed the `q8.z.t` Kotlin Intrinsics NPE + both APP-BOUNDARY escapes |

## 3. Metric table (the full journey)

| metric | S107 | S109 | S110 |
|---|---|---|---|
| uncaught errors | 32 | 6 | **0** (crash.log `[No errors recorded]`) |
| init chain | death at MessagesController | complete | complete |
| database | JNI unsupported (infinite spin) | REAL SQLite (cache4.db) | REAL SQLite |
| stream/coroutine ISE | 3,697/run | 0 | 0 |
| instructions | 44.5k rows | 163,212 / 10,818 heap objs | 163,212 |
| login view tree | none | 30+ nodes measured | **62 render entries intact** (`he1$d` StartMessaging @ y=1656) |
| shot SHA-16 | — | `59fdbfcd60b86a23` ×2 | `59fdbfcd60b86a23` (deterministic) |

## 4. The REAL login UI view tree (Forkgram's own classes)

```
LaunchActivity$w (1080x1920)
└── DrawerLayoutContainer (1080x1920)
    └── ActionBarLayout (1080x1920, 8 children)
        ├── n3 (1080x76)                      — action bar
        ├── ActionBarLayout$l ×4              — real fragment stack
        │   └── ScrollView (1080x1920)
        │       └── he1$a  ← THE LOGIN LAYOUT (6 children)
        │           ├── FrameLayout → TextureView (200x150)
        │           ├── androidx.viewpager b
        │           ├── he1$d  "StartMessaging"  (1080x48 @ y=1656)  ← LOGIN BUTTON
        │           ├── TextView (1080x30 @ y=1596)
        │           ├── FrameLayout → t81 icon (28x28)
        │           └── kj progress (66x5 @ (507,871))
        └── … bottom-sheet yj$v family, LinearLayout headers
```

## 5. Rendered state (honest)

![reference vs current]({RAW}/evidence/s110_tickets/telegram/compare_reference_vs_current.png)

The window paints Forkgram's own themed background (240,240,240); **the widget
pixels are the remaining frontier** — the login tree is measured but not yet
painted (R$styleable theme attrs + text-draw laws, the `C013-ONDRAW ops=0`
markers). A gameplay GIF is not meaningful yet — nothing moves until those
roots land; that is the honest state. The path to the phone-number → SMS code
screen runs through that pixel wave.

## 6. Help from the evidence comments

- [Comment 1](#issuecomment-5857415062): fresh-run table + login-tree dump —
  incorporated in §3/§4.
- [Comment 2](#issuecomment-5857497464): the 6→0 zero-error update
  (ROOT-046/047 with DEX ground truth) — incorporated in §2/§3, regression
  gates included.

## 7. Zero-regression gates

| gate | result |
|---|---|
| ballbreak | SUCCESS 0 errors, `fe797c19…` byte-identical across S107→S111 |
| dooz | `a2ba4a49…` Compose surface, stable |
| HTML5 breakout | `5bcd77b8…` document wave / `568342fb…` S111 JS wave, 3/3 identical |

## خلاصه فارسی (Persian TL;DR)

هدف: اجرای **فورک تلگرام (Forkgram Classic)** — نام تیکت اصلاح شد چون APK
واقعی فورک است. مسیر: **۳۲ خطا → ۶ → ۰ خطای uncaught** با **۳۱ قانون ریشه‌ای**
در چهار موج (S108 init-chain، S109 درخت UI لاگین، S110 KeyStore +
getBaseContext). الان: زنجیره‌ی init کامل، **SQLite واقعی**، لایه‌ی
serialization، و **درخت view واقعی UI لاگین** (۶۲ رندر، دکمه‌ی StartMessaging
با مختصات واقعی). **فرونتیر صادقانه:** پیکسل‌های ویجت‌ها (خانواده‌ی
R$styleable تم) — مسیر تا صفحه‌ی شماره تلفن و کد SMS همین است. رگرسیون صفر با
SHA های بایت‌به‌بایت اثبات شده.
"""

# ── apply ──
issue = gh('issues/353')
gh('issues/353', 'PATCH', {
    'title': '[HTML5-APPS] WebView: white screen → REAL JS execution — Breakout 71 runs its game loop (#94)',
    'body': BODY_353})
print('353 patched')
gh('issues/354', 'PATCH', {'body': BODY_354})
print('354 patched')
gh('issues/355', 'PATCH', {'body': BODY_355})
print('355 patched')
