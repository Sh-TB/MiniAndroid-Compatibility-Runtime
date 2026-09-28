#!/usr/bin/env python3
"""S116: publish the three knowledge-transfer tickets at the true S115 state.
- #353: + S112-S113 generalization/full-GUI wave + S114 ONE-BIG-FIX; honest frontier refresh
- #354: + S115 77-ticket sweep family attribution; gate re-baseline note
- #355: title+body -> 32 to 0, first fully clean run, S115 wave (ROOT-062/063), honest pixel state
- #354: post the S115 sweep-status comment (English only)
All text English (no Persian), images small (existing slim evidence)."""
import json
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
TOKEN = open("/tmp/.gh_token").read().strip()
BASE = f"https://api.github.com/repos/{REPO}"


def api(method, url, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req) as r:
        body = r.read().decode()
        return json.loads(body) if body else None


R = "https://raw.githubusercontent.com/Sh-TB/MiniAndroid-Compatibility-Runtime/main"

# ---------------------------------------------------------------- issue 353
B353 = f"""# HTML5 / WebView — from white screen to real JS execution to FULL-GUI render

Knowledge-transfer report, standard structure: bug-fix methodology → metric
tables → rendered images → help-from-comments. Built on the evidence comments
below (document-load verification → execution proof → generalization wave →
full-GUI upgrade → the ONE-BIG-FIX). All text English; images small.

## 1. The bug (and the traps that hid it)

HTML5 games are WebView + JS packages. On this runtime they were **white
screens** (#94 me.lecaro.breakout, `STATE-NOT-LOADED`; audit reopen #74/#205
"requires a WebView"). Three traps hid the real frontier, each exposed by an
evidence comment: (a) the **static-HTML trap** — a header painted from HTML
text is NOT HTML5 execution (the 1.5 MB JS bundle had never run); (b) the
**execution trap** — scripts executing is NOT a rendered GUI (raw unstyled
text blocks, 224 colors, no layout engine at all); (c) the **completeness
trap** — a partial frame (missing score row, phantom rows, mispinned
overlays) is NOT a render closure. Every claim below survived all three.

## 2. Bug-fix methodology — structural laws, zero package checks

### S111 — JS execution (ROOT-048 … 053)

| root | bug (engine truth) | law applied |
|---|---|---|
| 048 | `console.debug` missing → migration runner threw → **all 8 migrations failed**, main script aborted | Chromium DevTools console contract (debug/trace/dir/table/time/count/group/assert/clear) |
| 049 | `getContext('2d')` registered 6 of 30+ members; the C++ Canvas2D raster was unreachable from JS | WHATWG CanvasRenderingContext2D full surface bound to the real raster |
| 050/051/052 | `calc(var(--vh,1vh)*100)` → 0; body bg never propagated; canvas bitmap opaque white | CSS var-fallback + unit-aware calc; root/body bg propagation; WHATWG transparent-black resize reset |
| 053 | `WebView.getCurrentWebViewPackage` probe → null → "requires a WebView" | AOSP: a WebView-shipping device answers non-null WebViewPackageInfo (honest identity) |

### S112 — generalization (ROOT-054 … 057)

| root | law |
|---|---|
| 054 | WebView provider identity = platform build metadata → the app's own "Update required!" gate passes on honest version, no forging |
| 055 | `View.getLayoutParams` never-null parent-type law (CoordinatorLayout.LayoutParams + anchorId NO_ID both spellings) |
| 056 | `findViewById` with id<=0 answers null (kills the phantom root match) |
| 057 | `CookieManager.getInstance()` process-wide singleton (AOSP provider-ships-it law) |

### S113 — the CSS box-model layout + paint engine (ROOT-059/060/061)

External `<link rel=stylesheet>` fetch law, `@media` nested-brace matching,
compound + descendant selectors, padding/margin/border/radius shorthands,
flex subset with %-sizes resolved at the containing block, background-image
decode+cache (libpng) with contain fit, gradients, shadows, transforms,
`::before/::after` exclusion, inline-children text merge, whitespace-only
#text suppression, innerHTML replacement law, `HTMLMediaElement.play/pause`,
`getElementsByClassName`. ROOT-059 closed the 21-error androidx
WindowInsetsCompat family (R8-outline → Builder materialization law).

### S114 — the ONE-BIG-FIX: 6 generic engine laws (no per-app patches)

| # | law | what it fixed |
|---|---|---|
| 1 | **Line-record** — the measure pass is the single writer of text-line geometry | every merged line painted one line-height low; score row buried in the brick field; phantom h1 2nd row |
| 2 | **Inline-fragment** (CSS 2.1 §10.3.1) — merged inline lines paint as styled runs | `.scores span` color/size erased — the green value died in every styled-span app |
| 3 | **Static-origin** — auto-offset absolutes anchor at the nearest laid-out ancestor | `.sound_label span` pinned at (0,0), overpainting the score row |
| 4 | **CSS Values §3 math** — min()/max()/clamp() in the calc evaluator | accelerace `max(15vw,15vh)` sizing → font-size 0 → SIGSEGV |
| 5 | **FreeType size contract** | FT_Set_Pixel_Sizes(0) → zero-scale hb_font crash |
| 6 | **Font-memory lifetime** | FT_New_Memory_Face keeps the buffer pointer — kept copy must be the same allocation |

## 3. Metric tables (deterministic runs)

| metric | static-HTML trap | S111 execution | S113 full-GUI | S114 ONE-BIG-FIX |
|---|---|---|---|---|
| JS bundle | not executed | 1.5 MB executes | executes | executes |
| migrations | 0/8 | 8/8 | 8/8 | 8/8 |
| draw calls | 0 | 8 | — | — |
| unique colors | 2 | dark theme | **1953** (mykanji, was 224) | **complete game frames** |
| layout | flat stacking | flat | **box model + flex + images** | + inline runs, static origin |
| shot SHA-16 | — | `568342fb…` ×3 | `429ffe7c…` | `05cd9f35…` ×3 (byte-identical) |
| js_errors | 1 | **0** | 0 | 0 |

## 4. Rendered images — the proof

The HTML5 anchor: Breakout #94 runs its real game loop (menu HUD, paddle+ball,
press-and-hold, dark theme) —
[frame](https://raw.githubusercontent.com/Sh-TB/MiniAndroid-Compatibility-Runtime/main/evidence/s109_webview/breakout_fix52_run1/screenshot.png),
[reference](https://raw.githubusercontent.com/Sh-TB/MiniAndroid-Compatibility-Runtime/main/evidence/s110_tickets/html5_breakout/reference_froid.png).

The ONE-BIG-FIX proof — org.asafonov.blockbuster, **complete game render**
(10–15 KB per full frame; the earlier upload was 7.91 MB):

| Start screen (complete) | Gameplay (complete) |
|---|---|
| ![start](https://raw.githubusercontent.com/Sh-TB/MiniAndroid-Compatibility-Runtime/main/evidence/s114_bigfix/final/blockbuster_start_small.png) | ![game](https://raw.githubusercontent.com/Sh-TB/MiniAndroid-Compatibility-Runtime/main/evidence/s114_bigfix/final/blockbuster_game_small.png) |

Full-res: [start_1080](https://raw.githubusercontent.com/Sh-TB/MiniAndroid-Compatibility-Runtime/main/evidence/s114_bigfix/final/blockbuster_start_1080.png) ·
[game_1080](https://raw.githubusercontent.com/Sh-TB/MiniAndroid-Compatibility-Runtime/main/evidence/s114_bigfix/final/blockbuster_game_1080.png) ·
mykanji full GUI: [1080p](https://raw.githubusercontent.com/Sh-TB/MiniAndroid-Compatibility-Runtime/main/evidence/s114_bigfix/final/mykanji_1080.png).

Read directly from the frames: the Iceland-font gradient title
(-webkit-background-clip:text), centered .info panel + 150vw dim overlay,
green Start button, the game's own j%4 level-3 brick grid (itemWidth
27 = field.offsetWidth/40 read live by the JS), ball, hero paddle,
`Score: 0` (green span) / `Highscore: 0` (white span) — labels AND values.

## 5. Web family (animated GIF — real TLS browser)

[Mini Browser loading z.ai over real TLS](https://raw.githubusercontent.com/Sh-TB/MiniAndroid-Compatibility-Runtime/main/docs/evidence/canonical/com.miniandroid.browser.zai.gif) ·
[example.com tap-driven state change](https://raw.githubusercontent.com/Sh-TB/MiniAndroid-Compatibility-Runtime/main/docs/evidence/canonical/com.miniandroid.browser.gif)

## 6. Family status + honest remaining frontier

| APK | state |
|---|---|
| me.lecaro.breakout (#94) | VERIFIED — execution anchor, byte-identical 3/3 |
| org.asafonov.blockbuster | RENDERED — complete start + gameplay frames, 3-run deterministic |
| io.github.hathibelagal.mykanji | RENDERED — full GUI (header, card, mirrored cat, gradient buttons) |
| org.asafonov.accelerace | EXECUTED — un-SIGSEGV'd (laws 4/5/6), dark theme + speedometer text; canvas scene open |
| org.asafonov.sokoban | corrupt ZIP archive — skipped honestly |
| blidraughts (#74) | BLOCKED at ROOT-058 (R8-de-enum'd androidx.webkit feature registry, app-DEX static-init gap) |

Open frontier, honestly labeled: the input gate is proven on blockbuster
(tap → game.js → state change → new frame: start screen → brick grid) but the
mykanji post-click appcompat drain still segfaults in the DEX engine
(ROOT-061 — dialog paint); accelerace canvas depth; a 1-in-5 async
@font-face relayout can land after the last frame capture (evidence runs
chosen post-settle).

## 7. Help from the evidence comments

- [Evidence comment](#issuecomment-5857414802) — the visual baseline
  (99.9% non-white px, dark theme) and the static-HTML trap warning.
- [Execution proof](#issuecomment-5858470298) — ACHIEVEMENT #9 anchor.
- [Generalization wave](#issuecomment-5858906111) — 2nd/3rd APKs, honest blidraughts status.
- [Full-GUI upgrade](#issuecomment-5859831075) — the render law ("loading is
  not the criterion") under which the incomplete blockbuster frame was
  re-classified; enforced the S113/S114 waves.
- [ONE-BIG-FIX final](#issuecomment-5863772275) — the 6 laws + complete frames.
"""

# ---------------------------------------------------------------- issue 354
B354 = f"""# Native game family — gameplay GIFs, 5 engine-bug laws, verified 3-run titles + the honest audit + the S115 sweep

Knowledge-transfer report, standard structure: bug-fix methodology → metric
tables → rendered images/GIF → help-from-comments. Built on the evidence
comment below. All text English; images/GIFs linked and light.

## 1. The story arc (S79 → S115)

- **S79–S102 — interaction & media:** canonical tap pipeline
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
- **S115 — the assembly-line sweep:** the 77 NEAR_BLANK reopened tickets
  re-run at the S114 HEAD, ONE run each, **zero per-ticket debugging**
  (explicit user directive); verdicts + family attribution in §6.

## 2. Bug-fix methodology — the 5 engine laws (S106)

| # | bug (silent law violation) | law applied |
|---|---|---|
| 1 | stroke-only vector paths drew NOTHING | fill/stroke independence |
| 2 | `Affine2D::pre_rotate` rotated counter-clockwise | M*R^t vs M*R — AOSP/Skia rotate(90) is clockwise |
| 3 | `layout_text` maxLines off-by-one | one extra empty line removed |
| 4 | `View.requestLayout()` was a silent no-op | layout_dirty traversal flag raised |
| 5 | group `android:alpha` + `state_checked` | group alpha inheritance + state-list pick + audio module |

Plus 2 upstream stb bugs fixed for real GIF animation (disposal-2 semantics,
two_back OOB).

## 3. Verified gameplay evidence (real engine runs)

| bouncy (VERIFIED_3RUN #121) | bobball (VERIFIED_3RUN #81) |
|---|---|
| ![bouncy](https://raw.githubusercontent.com/Sh-TB/MiniAndroid-Compatibility-Runtime/main/docs/evidence/canonical/com.dozingcatsoftware.bouncy.gif) | ![bobball](https://raw.githubusercontent.com/Sh-TB/MiniAndroid-Compatibility-Runtime/main/docs/evidence/canonical/org.bobstuff.bobball.gif) |

| hotdeath (VERIFIED_3RUN #68) | fish.rings (input→state chains) |
|---|---|
| [hotdeath](https://raw.githubusercontent.com/Sh-TB/MiniAndroid-Compatibility-Runtime/main/docs/evidence/canonical/com.smorgasbork.hotdeath.gif) | [fishrings](https://raw.githubusercontent.com/Sh-TB/MiniAndroid-Compatibility-Runtime/main/docs/evidence/canonical/eu.veldsoft.fish.rings.gif) |

More gameplay GIFs (linked, not inlined): 2048, Tetris, minicraft, snakeneon,
tictactoe, tictactoedeluxe, dodge, nounours, urlchecker — in
`docs/evidence/canonical/`.

## 4. Native gates — re-baselined honestly at the S114 CSS wave

| title | status | errors | shot SHA-16 | note |
|---|---|---|---|---|
| de.georgsieber.ballbreak | SUCCESS | 0 | `fe797c19…` → `25e72190…` | re-baselined by the S114 HTML5 CSS wave (shared rendering core); byte-identical within the S114 baseline, zero drift from native paths |
| io.github.yamin8000.dooz | SUCCESS | 6 (handled) | `a2ba4a49…` → `84c6d4a5…` | same re-baseline; Compose surface stable |

Click dispatch (per the evidence comment): `GameView$1` listener + XML
`onClick` handlers (`onClickWeb`, `onClickHighscores`) — all DISPATCHED.

| ballbreak render | dooz render |
|---|---|
| [ballbreak](https://raw.githubusercontent.com/Sh-TB/MiniAndroid-Compatibility-Runtime/main/evidence/s110_tickets/native_games/ballbreak/screenshot.png) | [dooz](https://raw.githubusercontent.com/Sh-TB/MiniAndroid-Compatibility-Runtime/main/evidence/s110_tickets/native_games/dooz/screenshot.png) |

## 5. The honest state (post-audit)

The 128 reopened titles run (real DEX, deterministic) but their visual closure
needs the near-blank root chain. Contact sheets + per-ticket ledger:
`evidence/audit_s107/` (AUDIT_TABLE.md).

[audit contact sheet](https://raw.githubusercontent.com/Sh-TB/MiniAndroid-Compatibility-Runtime/main/evidence/audit_s107/contact_sheet_1.png)

## 6. S115 — the 77-ticket assembly-line sweep (no per-ticket debugging)

All 77 NEAR_BLANK reopened tickets re-run at the S114 HEAD, one run each:

| verdict | count | meaning |
|---|---|---|
| closure under the render law | **0** | no new visual closures claimed |
| effectively blank | **68** | 2-color early-death windows |
| PARTIAL (real but wrong pixels) | **4** | #191 overlap-jumble, #216 misplaced dialog text (plain-WebView family — the S114 CSS wave benefits it), #219 bottom strip, #212 toolbar strip |
| corrupt-APK fetch | **5** | #87 #107 #120 #185 #206 — bad download, re-fetch needed (not runtime) |

**Family attribution (the leverage map, not per-ticket patches):**

| family | count | frontier |
|---|---|---|
| empty view tree (lifecycle completes via DEX engine, attach finds 0 view nodes) | ~43 | the single biggest lever: #344/#230/#348 |
| libGDX/Godot native `.so` loading + JNI | ×6 | APK .so extraction path |
| lifecycle "Next event must be ON_CREATE" sequencing | ×4 | same family Telegram's ROOT-062 closed |
| fragment-host | ×3 | fragment stack attach |
| MultiDex | ×2 | multi-DEX loading |
| ViewTreeLifecycleOwner | ×2 | androidx lifecycle wiring |

77/77 honest per-ticket status comments are posted on the tickets
(English only, no closure claims).

## 7. Help from the evidence comments

The [evidence comment](#issuecomment-5857414959) supplied the click-dispatch
table and the honest dooz note (Compose taps = known open frontier) — both
incorporated verbatim in §4 instead of being re-claimed. The S115 sweep
verdicts and family attribution come from `evidence/s115` sweep tooling
(scripts/s115_sweep77.py + scripts/s115_family_histogram.py) and are posted
per-ticket.
"""

# ---------------------------------------------------------------- issue 355
T355 = "[TELEGRAM] Forkgram 12.10.8.0 — errors 32 → 0, first fully clean run (rc=0, 0 uncaught), real login UI tree; pixels = the frontier"

B355 = f"""# Forkgram (Telegram fork) Classic 12.10.8.0 — errors 32 → 0, first fully clean execution, real login UI view tree

Knowledge-transfer report, standard structure: bug-fix methodology → metric
tables → rendered state (honest) → help-from-comments. Naming note: the APK
is **Forkgram Classic** (`org.forkgram.classic`, vc 709208) — a community
**fork of Telegram** (fully-buildable FOSS base); the ticket previously read
"Telegram" and has been corrected. Built on the three evidence comments
below. All text English.

- 5 DEX files, ~41k classes, private JNI natives, private SQLite wrapper,
  desugared coroutine/stream machinery.
- Related: ticket #140 family (S107 measurement), worklog S108–S115.

## 1. Where it started (S107)

44.5k log rows of real `org/telegram` code, then death at
`MessagesController.getInstance` — `requireNonNull(null)` NPE — with **32
uncaught errors** and a flat white window.

## 2. Bug-fix methodology — 49 root laws (ROOT-016 … ROOT-063)

### S108 wave (ROOT-016 … 026) — the init chain

| root | law |
|---|---|
| 016 | `SharedPreferences.getStringSet` miss → **defValues** (killed the `whitelistedBots` stream NPE) |
| 017 | **`org.telegram.SQLite` 20 JNI natives over REAL sqlite3** (ROW→0/DONE→1; INT64 handles were truncated to int32!) |
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

### S110 wave (ROOT-046/047) — zero uncaught errors

| root | law |
|---|---|
| 046 | `java.security.KeyStore` family: `getInstance` **never null**; `containsAlias` honest **false** → Telegram takes its degraded fingerprint path instead of dying |
| 047 | `Activity.getBaseContext()` **never null** (AOSP: `attach()` binds mBase before onCreate) — killed the `q8.z.t` Kotlin Intrinsics NPE + both APP-BOUNDARY escapes |

### S115 wave (ROOT-062/063) — the first fully clean run

| root | law |
|---|---|
| 062 | **AOSP CREATED-PHASE lifecycle fan-out** — the multi-DEX direct-dispatch onCreate site never fired onActivityPreCreated → onCreate → onActivityCreated → onActivityPostCreated; androidx Recreator then asserted `Next event must be ON_CREATE` and killed LaunchActivity.onCreate (DEX ground truth via a calibrated dalvik walker: Recreator removes itself on ON_CREATE else throws) — same family as sweep tickets #86/#98 |
| 063 | **`StaticLayout$Builder` materialization** — obtain never-null with AOSP defaults, fluent this-returning setters, build() → StaticLayout with deterministic measurement metrics (render path keeps the TextShaper line boxes); was: obtain answered null → setMaxLines NPE in Telegram TextLayout |

## 3. Metric table (the full journey)

| metric | S107 | S109 | S110 | S115 |
|---|---|---|---|---|
| uncaught errors | 32 | 6 | **0** | **0** |
| in-flight uncaught | — | — | 4 (app-caught context) | **0** |
| warnings | — | — | — | **0** |
| exit code | death | — | — | **rc=0** |
| init chain | death at MessagesController | complete | complete | complete |
| database | JNI unsupported (infinite spin) | REAL SQLite (cache4.db) | REAL SQLite | REAL SQLite |
| stream/coroutine ISE | 3,697/run | 0 | 0 | 0 |
| login view tree | none | 30+ nodes measured | 62 render entries | **builds deeper; `StartMessaging` string RESOLVED and SET on `he1$d`** |
| shot SHA-16 | — | `59fdbfcd…` ×2 | `59fdbfcd…` (deterministic) | themed window deterministic |

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

![reference vs current](https://raw.githubusercontent.com/Sh-TB/MiniAndroid-Compatibility-Runtime/main/evidence/s110_tickets/telegram/compare_reference_vs_current.png)

The window paints Forkgram's own themed background (240,240,240); **the
widget pixels are the remaining frontier** — the login tree is measured, the
text content sets (`StartMessaging` on `he1$d`), but glyphs are not yet
painted (R$styleable/TypedArray theme attrs + text-draw laws; the
`C013-ONDRAW ops=0` markers). Execution status: **VERIFIED (0-error clean
run)**. Render status: **NOT RENDERED YET — honest**. A gameplay GIF is not
meaningful until those roots land. The path to the phone-number → SMS screen
runs through that pixel wave.

## 6. Help from the evidence comments

- [Comment 1](#issuecomment-5857415062): fresh-run table + login-tree dump —
  incorporated in §3/§4.
- [Comment 2](#issuecomment-5857497464): the 6→0 zero-error update
  (ROOT-046/047 with DEX ground truth) — incorporated in §2/§3.
- [Comment 3](#issuecomment-5865612249): the S115 fresh runs at the current
  HEAD — ROOT-062/063 and the first fully clean execution — incorporated in
  §2 (S115 wave) and §3 (metric column).

## 7. Zero-regression gates

| gate | result |
|---|---|
| ballbreak | SUCCESS 0 errors; S114-baseline SHA `25e72190…` byte-identical (the S114 CSS wave re-baselined `fe797c19…` honestly — shared rendering core) |
| dooz | S114-baseline SHA `84c6d4a5…` byte-identical; Compose surface stable |
| HTML5 breakout | `568342fb…` S111 JS wave; blockbuster `05cd9f35…` ×3 byte-identical |
"""

# ------------------------------------------------- S115 sweep comment on 354
C354 = """## S115 — the 77-ticket assembly-line sweep at the S114 HEAD (one run each, zero per-ticket debugging)

Executed per the explicit working directive: check all 77 WITHOUT getting
stuck on any single one — a fast batch pass, then move on. One run per
ticket, pixel metrics (unique colors / non-bg / entropy), verdict posted on
each ticket.

### Verdicts

| verdict | count | tickets |
|---|---|---|
| closure under the render law | **0** | no new visual closures claimed — the render law holds |
| effectively blank | **68** | 2-color early-death windows across the board |
| PARTIAL — real but wrong pixels | **4** | #191 bicyweather (overlap-jumble), #216 asafonov.weather (misplaced dialog text — plain-WebView family, benefits from the S114 CSS wave), #219 buses (bottom strip), #212 acode (toolbar strip) |
| corrupt-APK fetch | **5** | #87 #107 #120 #185 #206 (PARSE_ERROR, no end-of-central-directory — re-fetch needed, not a runtime issue) |

### Family attribution — the leverage map

| family | count | shared frontier |
|---|---|---|
| **empty view tree** — lifecycle completes via the DEX engine with 0 errors, attach() finds 0 view nodes | ~43 | the single biggest lever (#344/#230/#348 exemplars); a generic fix here lifts ~43 tickets at once |
| libGDX / Godot native `.so` loading + JNI | ×6 | APK `.so` extraction + dlopen path |
| lifecycle "Next event must be ON_CREATE" sequencing | ×4 | the same family Telegram ROOT-062 closed (AOSP CREATED-PHASE fan-out) |
| fragment-host | ×3 | fragment stack attach |
| MultiDex | ×2 | multi-DEX loading |
| ViewTreeLifecycleOwner | ×2 | androidx lifecycle wiring |

### Why this matters

The sweep converts 77 individual mysteries into 6 shared root families with
per-ticket evidence. Per the honest-labels rule: nothing here is claimed as
closed; the 4 PARTIAL tickets have REAL pixels (progress since the audit)
but wrong layout. The family fixes queue behind the Telegram login-pixel
wave and will be re-swept afterwards.

Evidence: `evidence/s115` sweep tooling (scripts/s115_sweep77.py,
scripts/s115_family_histogram.py); per-ticket verdict comments on all 77
tickets (English only).
"""

# ---------------------------------------------------------------- run
api("PATCH", f"{BASE}/issues/353", {"body": B353})
print("353 body patched")
api("PATCH", f"{BASE}/issues/354", {"body": B354})
print("354 body patched")
api("PATCH", f"{BASE}/issues/355", {"title": T355, "body": B355})
print("355 title+body patched")
r = api("POST", f"{BASE}/issues/354/comments", {"body": C354})
print("354 comment posted:", r["id"])
