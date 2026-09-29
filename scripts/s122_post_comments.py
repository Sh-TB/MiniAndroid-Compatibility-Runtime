#!/usr/bin/env python3
"""s122_post_comments.py — post the S122 harder-games wave report to GitHub.

English-only per the repo law. Targets: #354 (games family) and #353
(HTML5/runtime ledger).
"""
import json
import sys
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
TOKEN = open("/tmp/.gh_token").read().strip()

BODY = """## S122 wave — TWO HARDER games: chess 10.6.0 + Klondike solitaire

User directive: try two harder games. Picks (never played before, heavier
stacks): **jwtc.android.chess 10.6.0** (vc298 — full chess rules engine + AI,
R8-renamed androidx appcompat + RecyclerView) and **eu.veldsoft.free.klondike**
(vc3 — full Klondike rules engine, CardStack/DealDeck/AcePile model, programmatic
card board).

**Six new generic runtime laws shipped (zero package checks):**

1. **R-NEW-412** — M3-19 cycle-guard identity refinement: static AND instance
   invoke keys now append up to 2 PRIMITIVE argument values after the object
   identities. The R8-renamed androidx ResourceManagerInternal delegation
   chain `.e(ctx,R,checkSetup=true) -> .d -> .e(ctx,R,false)` (calls differing
   ONLY in the boolean flag) was stubbed as a same-key cycle, the manufactured
   null tripped the vector-setup gate, and chess died with ISE "This app has
   been built with an incorrect configuration. Please configure your build for
   VectorDrawableCompat." Different primitive identities = legal nested dispatch.
2. **R-NEW-413** — vector-XML drawables carry the platform
   `android.graphics.drawable.VectorDrawable` class label (AOSP Resources.getDrawable:
   a `<vector>` XML materializes as the platform vector on API 21+). The bare
   `Drawable` base label failed appcompat's `getClass().getName()` gate probe.
   The label now follows the inflated XML root element (AxmlParser).
3. **R-NEW-414/414b** — instance field-initializer defaults: a field whose
   `<init>` initializer is `new T` (javac `new-instance T vN ... iput-object vN`
   pattern, scanned lazily from the DEX) is NEVER NULL on a real instance; a
   heap read that would answer null/missing/stale materializes an empty T
   instead (chess: ContentFrameLayout `mDecorPadding` Rect → Rect.set NPE),
   and for non-heap VIEW-NODE receivers (content frame id 800100) the answer
   is cached per (node id, field) for identity stability.
4. **R-NEW-415** — `Resources.getInteger(int)` resolves the REAL integer from
   resources.arsc (AOSP Resources law). The 0-stub made chess build
   `new GridLayoutManager(this, getInteger(R.integer.x))` with span 0 →
   IAE "Span count should be at least 1. Provided 0". Now resolves 2 (the
   chess board's real span count).
5. **R-NEW-416** — `Window.findViewById(int)` delegates to the DECOR tree
   (AOSP PhoneWindow law), with the ActivityShadow content-view fallback.
   The null stub made every androidx-window-routed findViewById answer null
   (chess board RecyclerView) and left setLayoutManager dispatching on null.
6. **R-NEW-417/418** — (417) a DEX-defined view whose class chain overrides
   `onTouchEvent` is a touch target (AOSP dispatchTouchEvent delivers to the
   deepest view under the point; no listener registration required) with the
   full DOWN→UP `onTouchEvent(MotionEvent)` dispatch arm — the custom-game-
   board family was tap-dead before; (418) `getWindowManager()` returns the
   WindowManagerImpl singleton (AOSP attach law) — the null stub NPE'd
   klondike's `resizeImageViews` ("getDefaultDisplay on null") and killed the
   card-view resize + listener registration section.

**Results per game (full load + agent play + render evidence):**

| Game | Full load | Agent play | Notes |
|---|---|---|---|
| chess 10.6.0 | **YES — 0 errors** | menu/board infra only | onCreate completes, decor + toolbar painted (23k px), RecyclerView inflated/measured; content paint waits on the adapter→relayout traversal (next frontier, root-caused) |
| klondike | **YES — 0 errors** | **YES — menu → New Game → board → deck tap → deal state change** | button click dispatched (MenuActivity$1), GameActivity launched, deck ImageView hit (target=143), card faces render (aces with suit symbols) |

**Evidence:** `evidence/s122_harder_games/` — 4 small English-only JPGs:
chess full-load frame, klondike menu, klondike table+deck, klondike after the
deck tap (aces up). Drivers: `scripts/s122_harder_games.py`,
`scripts/s122_klondike_session.py`, packaging `scripts/s122_package.py`;
DEX tooling `scripts/s122_dexdump.py`.

**Honest open frontiers (root-caused, next wave):** chess content paint needs
the setAdapter→requestLayout→re-measure traversal; klondike full-rule play
(move validation across CardStack columns) needs the drag/tap-2 pipeline on
the card ImageViews.
"""


def post(issue_no):
    url = f"https://api.github.com/repos/{REPO}/issues/{issue_no}/comments"
    req = urllib.request.Request(
        url,
        data=json.dumps({"body": BODY}).encode(),
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "miniandroid-ci",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as r:
        out = json.load(r)
        print(f"issue #{issue_no}: comment {out.get('id')} html={out.get('html_url')}")


if __name__ == "__main__":
    for n in (int(a) for a in (sys.argv[1:] or ["354", "353"])):
        post(n)
