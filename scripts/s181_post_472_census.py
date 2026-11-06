#!/usr/bin/env python3
"""s181_post_472_census.py — post the S181 minimal-app battery + root-problem
map to the master tracker #472 so every coder sees the families."""
import json
import subprocess
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
ISSUE = 472


def token():
    out = subprocess.run(["git", "credential", "fill"],
                         input="protocol=https\nhost=github.com\n\n",
                         capture_output=True, text=True)
    for line in out.stdout.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    raise SystemExit("no token")


TOK = token()

BODY = """## S181 — minimal-app battery (13 titles) + root-problem map: where simple apps actually die

Directive: «۱۲ اپ/بازی خیلی کم‌حجم و ساده تست کن، ببینم مشکل کجاست» + 3 user-named APKs (fetched at the exact pinned versions). Binary = current main `5d7edcdb34b1502c` (C9+C7). Fresh store per title, real-dalvik, trace on.

### Results — 7/13 REAL_APP_CONTENT

| Title | Size | Class | App px | uncaught |
|---|---|---|---|---|
| opmt (game) | 100 KB | **REAL_APP_CONTENT** | 1,263,099 | 0 |
| unote (notes) | 163 KB | **REAL_APP_CONTENT** | 136,080 | 0 |
| fishrings (game) | 399 KB | **REAL_APP_CONTENT** | 105,061 | 0 |
| tripeaks (game) | 418 KB | **REAL_APP_CONTENT** | 559,818 | 0 |
| balance | 730 KB | **REAL_APP_CONTENT** | 500,130 | 5 nonfatal (BankRules.normalize NPE) |
| terminightor_12 (user-named) | 2.0 MB | **REAL_APP_CONTENT** | 11,025 | 3 nonfatal (AlarmItemListFragment.onCreate NPE) |
| tangram_90001 (user-named) | 3.2 MB | **REAL_APP_CONTENT** | 376,488 | 0 |
| just24hoursplus_10400 (user-named) | 3.1 MB | PARTIAL — SYSTEM_CHROME_ONLY | 12,320 | 0 |
| stopwatch | 738 KB | PARTIAL — NO_ROOT | 0 | 0 |
| bmi | 1.3 MB | PARTIAL — DEFAULT_BACKGROUND_ONLY | 0 | 0 |
| sunpiano | 2.5 MB | PARTIAL — DEFAULT_BACKGROUND_ONLY | 0 | 32 |
| sopadeletras | 2.5 MB | PARTIAL — DEFAULT_BACKGROUND_ONLY | 0 | 32 |
| sparkledns | 1.9 MB | PARTIAL — DEFAULT_BACKGROUND_ONLY | 0 | 0 |

### The root-problem map (evidence, not guesswork)

**Family 1 — Compose runtime init (3 of 6 failures + the standing tusky blocker):**
- stopwatch: renderer COMPOSE, `[UC009-ATTACH-DIAG] ComposeView NOT in class index` → no window content root (VIEWTREE divergence, MEASURE never reached).
- sparkledns: compose census 298 rows + `kotlin.reflect.jvm.internal.ReflectionFactoryImpl` ClassNotFoundException.
- tusky (standing S170 pin): the Compose paint-color 31ddd4d5 black-on-black frontier.

**Family 2 — androidx lifecycle/coroutines init NPE storms (2 titles, likely ONE root):**
- sunpiano: NPE storm unwinding `Lj4/b;.<clinit>` → `Landroidx/lifecycle/s0;` (LifecycleRegistry minified chain), depth 47 — fires right AFTER `F058 onActivityPostCreated 2/2 observers executed`.
- sopadeletras: NPE + IAE storm through `qh1/ph1/se/ts0`, depth 51, same post-created fan-out point.

**Family 3 — missing framework classes at claimed API level (cheap per-law wins):**
- bmi: `android.support.v7.widget.DrawableUtils;.<clinit>` → **`android.graphics.Insets` ClassNotFoundException** — we report `SDK_INT=35` but don't ship `android.graphics.Insets`. Tiny Parcelable (left/top/right/bottom + `of(...)`); one honest implementation should unstick the whole support-v7 clinit chain.

### Hypotheses DISPROVEN with data (while I was at it)

- «those that fully load are HTML5»: the full-loaders have **0** WebView refs in dex (microtimer/g2048/opencalc/dooz/tetris/ttt_deluxe) or incidental refs only; the user-named **terminightor + tangram load REAL_APP_CONTENT as native apps**.
- «graphics don't load»: 7 minimal titles render 100K–1.26M app-owned pixels.
- «fonts don't load»: real text renders in every REAL title; **zero** font-family failures in any failure stack.

The recurring BASIC blocker is **not** classic graphics/fonts/layout — it is (1) Compose runtime, (2) androidx lifecycle/coroutines init nulls, (3) a short list of missing framework classes.

Evidence: `evidence/s181_minimal/S181_MINIMAL.json` (13 rows + family map); scripts/s181_minimal_battery.py.
"""


def main():
    url = f"https://api.github.com/repos/{REPO}/issues/{ISSUE}/comments"
    req = urllib.request.Request(
        url, data=json.dumps({"body": BODY}).encode(),
        headers={"Authorization": f"token {TOK}",
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "integration-verifier"})
    with urllib.request.urlopen(req) as r:
        out = json.load(r)
    print("posted ->", out.get("html_url"), "id", out.get("id"))


if __name__ == "__main__":
    main()
