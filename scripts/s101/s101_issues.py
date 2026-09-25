#!/usr/bin/env python3
"""s101_issues.py — S101 issue-per-problem lifecycle (evidence comments).

Posts the wave's root-cause evidence to the open frontier tickets and the
master wave thread. Token comes from MINIANDROID_GH_TOKEN env (env-only
law — never stored in files).
"""
import json
import os
import sys
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
TOKEN = os.environ.get("MINIANDROID_GH_TOKEN", "")
if not TOKEN:
    print("MINIANDROID_GH_TOKEN not set", file=sys.stderr)
    sys.exit(1)


def post_issue_comment(number, body):
    url = f"https://api.github.com/repos/{REPO}/issues/{number}/comments"
    data = json.dumps({"body": body}).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    with urllib.request.urlopen(req) as r:
        out = json.load(r)
        return out.get("html_url", "")


COMMENT_348 = """## S101 recall sweep — chain advanced 2 laws deep, new blocking stage

Fresh full-load re-run on the S101 tree (61 titles, identical S99 protocol)
re-derives this family from live evidence. Two permanent laws landed:

**1. REAL-CLASS-IDENTITY (Toolbar inflate law).** The inflater mapped
`androidx.appcompat.widget.Toolbar` → platform `Landroid/widget/Toolbar;` —
a class that does not exist in any appcompat APK's dex (verified:
ballbreak contains `Landroidx/appcompat/widget/Toolbar;` and NOT the
platform one). App dex code
`ActionBarOverlayLayout.getDecorToolbar` type-checks
`view instanceof androidx Toolbar` → FALSE → the exact reported ISE
`Can't make a decor toolbar out of Toolbar`. Fixed: the Toolbar inflates
under its REAL descriptor (+ `kFrameworkViews` seed for
non-appcompat APKs). Verified: ballbreak Toolbar dex `<init>` now executes
its real styleable walk (`Toolbar_titleMargin*` SGET trace).

**2. Resources$Theme.obtainStyledAttributes producer law.** Next stage of
the same chain: `ActionBarOverlayLayout.init` (APK dex) runs
`getTheme().obtainStyledAttributes(ATTRS)` — the F-093/F-NEW-175 producer
only existed on the Activity/Context shadow side, so a Theme-typed receiver
answered NULL → `TypedArray.getDimensionPixelSize` NPE at init pc=15.
The engine-side producer now materializes the same F-036 array + presence
bit convention; the existing F-093b/F-NEW-175 reader answers reads.

**Current blocking stage (this ticket remains OPEN):** with both laws in,
the chain advances to `WindowDecorActionBar.getDecorToolbar` answering
**null** — `decor.findViewById(R.id.action_bar)` finds no Toolbar because
the sub-decor (abc_screen_toolbar) is inflated but the app content attach
model puts `setContentView` content directly under the window decor, so
the ActionBarContainer/Toolbar subtree is not reachable from the decor
root at WindowDecorActionBar.init time. Downstream gaps on the same run:
`Resources.getLayout` → null XmlPullParser (SupportMenuInflater.parseMenu
NPE, caught by appcompat), `WindowInsets.inset` null receiver
(WindowInsetsCompat$Impl29), `MarginLayoutParamsCompat.getMarginStart`
null receiver. Flips so far in this family: mykanji FAIL→PARTIAL
(theme-gate → decor machinery, matching the ticket's expected next stage);
ballbreak's own chain now reaches WindowDecorActionBar (was: die at
getDecorToolbar instanceof).

Wave context: docs/API_NEED_LEDGER.md (per-title classes/APIs), census
FAIL 14→7 vs S99."""

COMMENT_344 = """## S101 recall sweep — root cause for the WebView subset + WEBVIEW-ASSET-RENDER law

Fresh full-load re-run (S101 tree) re-classified this family. The
"rc=0, draws nothing" mass is NOT one root — it splits:

**WebView-content family (6-7 titles):** klondike, tri.peaks, blackjack,
kingpong, accelerace, counting, memory render a full-screen
`Landroid/webkit/WebView;` whose content is the app's real UI loaded from
`file:///android_asset/...`. The old law recorded the URL alone and
rendered the honest empty placeholder → L0 blank.

**Fixed (WEBVIEW-ASSET-RENDER law):** `file:///android_asset/` and
`file:///android_res/` URLs now extract the entry through the canonical
ResourceRuntime parser and run the same F-085 HTML→visible-text pipeline
as loadData. Evidence:
- com.kingalex.kingpong FAIL → **RENDERED-L2+** ("King Pong HD" title
  painted, first L2 in the family)
- eu.quelltext.memory, eu.quelltext.counting, org.asafonov.accelerace
  FAIL → PARTIAL (content extracted and painted)
- crypto.o0o0o0o0o.games.blackjack: 4,226 B index.html → 430 chars
  extracted are whitespace-only — the UI is built by JavaScript at load
  time. Honest boundary: static render is correct; playable blackjack
  needs a JS engine (WEB-001 DESIGNED tier — no JS engine in this
  runtime, `evaluateJavascript` stays record+drop by law).

**Remaining in this ticket (still OPEN):** eu.veldsoft.free.klondike and
eu.veldsoft.tri.peaks load only `banner.html` (ad script, no visible
text); their game surface never loads a document in the observed window —
needs the per-title nav-chain walk (SplashActivity → GameActivity
transition), filed as the follow-up frontier. io.github.ebraminio.bouncy
(rc=0, L0, obfuscated `Lk;` root view) remains the multidex family #227.

Corpus-wide: FAIL census 14 (S99) → 7 (S101 tree); +1 RENDERED-L2+."""

COMMENT_MASTER = """## S101 RECALL SWEEP — wave report

Mandate: review everything left behind; register every bug as
per-title class/API needs; fix small items with big fan-out; more games
loaded.

**Forgotten-item catches (environment debt):**
- `DroidSansMono.ttf` (G32 monospace law font) was missing from the
  gitignored virtual system image on every run since the container reset —
  24/61 titles logged the loud MISSING diagnostic. Restored (AOSP
  data/fonts, SHA-pinned `db19a1fd…`), fetch added to
  `bootstrap_toolchain.sh`, documented in docs/SYSTEM_FONTS.md.
- The S99 full-load report was STALE relative to the S100 fixes — re-ran
  the identical 61-title protocol on the current tree (resume-safe runner
  scripts/s101/s101_rerun_full_load.py).

**Permanent registry (per-title class/API needs):** docs/API_NEED_LEDGER
.{json,md} — for every PARTIAL/FAIL title: missing classes (CNFE/NDF),
exception signatures with sites, inflate-unresolved counts, family
classification, families ranked by distinct-title fan-out. This is the
"which classes/APIs does each app need" ledger, evidence-first (every
need carries its log line).

**Runtime laws landed (3):**
1. REAL-CLASS-IDENTITY — androidx Toolbar inflates under its real dex
   descriptor (instanceof fix; decor-toolbar #348 chain).
2. Resources$Theme.obtainStyledAttributes producer — Theme-typed receivers
   no longer answer null TypedArray (ActionBarOverlayLayout.init chain;
   ballbreak/memory/mancala family).
3. WEBVIEW-ASSET-RENDER — file:///android_asset|android_res URLs render
   through the F-085 pipeline (WebView-UI family).

**Measured outcome (61 titles, identical protocol):**
| census | S99 | S101 |
|---|---|---|
| INTERACTIVE-EVIDENCE | 13 | 13 |
| RENDERED-L2+ | 1 | **2** |
| PARTIAL | 33 | **39** |
| FAIL | 14 | **7** |

7 up-flips: kingpong FAIL→L2+; counting/memory/accelerace FAIL→PARTIAL
(WebView law); mykanji/dooz/no.thanks FAIL→PARTIAL (S100+S101 chains).
No title regressed.

Battery/gates: canonical battery re-run on this tree (see thread tail for
the certification line); hygiene + secret gates at close. Evidence:
run/s101/full_load, docs/API_NEED_LEDGER.*."""


def main():
    which = sys.argv[1]
    if which == "348":
        print(post_issue_comment(348, COMMENT_348))
    elif which == "344":
        print(post_issue_comment(344, COMMENT_344))
    elif which == "master":
        print(post_issue_comment(233, COMMENT_MASTER))
    else:
        raise SystemExit("unknown target")


if __name__ == "__main__":
    main()
