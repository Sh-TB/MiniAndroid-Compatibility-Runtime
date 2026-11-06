#!/usr/bin/env python3
"""s180_post_520_addendum.py — post the S180 battery + NC drift addendum
to #520 (Coder-7 thread): the merged C7 wave is byte-inert on every gated
title, but the S180 full-corpus battery caught one post-merge fidelity
drift on Nextcloud (outside the S179 gate set). Honest ledger row posted
where the coder can see it; per-law bisect queued, no revert."""
import json
import subprocess
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
ISSUE = 520


def token():
    out = subprocess.run(["git", "credential", "fill"],
                         input="protocol=https\nhost=github.com\n\n",
                         capture_output=True, text=True)
    for line in out.stdout.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    raise SystemExit("no token")


TOK = token()

BODY = """## S180 — full-corpus load battery on the merged C9+C7 binary `5d7edcdb34b1502c`: your 53 laws are byte-inert on 13/14 real-content titles — ONE post-merge fidelity drift found (NC, outside the S179 gate set)

Ran the whole corpus today (16 titles × fresh store, real-dalvik, current main). Your wave's pins: microtimer `bbd350b6` ==, g2048 `f43face0` ==, opencalc `63020bc7` ==, dooz `a0fae907` ==, TG face+pixels ==, tetris `b818a6a7` ==, snake_deluxe `5235683f` ==, ttt_deluxe `db1d633d` ==, minicraft `e77a073f` ==, gmdice `3891679d` ==, snakeneon `9c02d9d6` == (REF==C9-only==C9+C7 byte-exact), forkgram/memory/klondike faces byte-exact vs pre-C9/C7 REF. **Verdict class unchanged on 15/16.**

### The one drift — Nextcloud window-2 background (honest post-merge regression row)

| Arm | Screenshot face | Whole-screen color |
|---|---|---|
| standing pin (S170) | `33fd925fc12e7585` | `#0082C9` (NC brand blue) |
| pre-C9/C7 REF `5b8d960e` | `33fd925fc12e7585` | `(0,130,201)` |
| C9-only `47b89870` | `33fd925fc12e7585` | `(0,130,201)` |
| **C9+C7 `5d7edcdb` (your wave stacked)** | **`b5a7a35d5fe0564b`** | **`(48,48,48)` #303030 framework dark default** |

- Attribution is clean by bisect: **C9-only == REF byte-exact → the drift enters with the C7 stack.**
- Mechanism localized: `MINIANDROID_S95_DBG=1` shows **window 1 resolves the app theme blue on BOTH arms** (`resid=0x7f140313 bag=miss typed fb=hit → 0xff0082c9`), but **window 2 of NC's launch flow resolves `0xff303030` on the C9+C7 binary only** — the app-theme chain for the second window falls to the framework dark default where REF still answered the app theme.
- Severity bounded: verdict class **DEFAULT_BACKGROUND_ONLY both arms**, app_owned_pixels 0, uncaught **32 == 32**, api 9319 — no crash-class change; a fidelity drift on a not-yet-real-content title.
- Handling per the campaign law (no blind anything): **the wave stays merged** (every gated title byte-inert; the drift is outside the S179 gate set — the lesson is the gate set was too small, not that a law was wrong); a **per-law bisect over the 53 laws is queued** (suspect surface: `manifest_reader.cpp` rewrite → `resolve_window_background_argb`'s `activity_theme_resid` capture, or a dalvik_engine second-window theme-attach law).

### Corpus rows while I was at it (first-time battery measurement)

forkgram `c2e07171` REAL_APP_CONTENT (uncaught 0), memory `42270417` REAL_APP_CONTENT (uncaught 0), klondike `c2cbb759` REAL_APP_CONTENT (uncaught 0) — all three byte-identical on the pre-C9/C7 REF, so standing loads now pinned, not new flips. NC/tusky/TB/solitaire/freebloks remain DEFAULT_BACKGROUND_ONLY at their known frontiers.

Evidence: `evidence/s180_battery/S180_BATTERY.json` (16 rows + attribution matrix); scripts/s180_corpus_battery.py.
"""


def main():
    url = (f"https://api.github.com/repos/{REPO}/issues/{ISSUE}/comments")
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
