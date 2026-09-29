#!/usr/bin/env python3
"""s121_post_comments.py — post the S121 full-load wave report to GitHub.

Run ONLY when a valid PAT is available in /tmp/.gh_token (the S121-supplied
token was rejected: 401 Bad credentials). English-only per the repo law.
Targets: issues #354 (native-games wave) and #353 (runtime wave ledger).
"""
import json
import sys
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
TOKEN = open("/tmp/.gh_token").read().strip()

BODY = """## S121 wave — the six games must FULLY load: results

**Verdict per game (rules: full load + agent play + HUD/pixel authority + determinism):**

| Game | Full load | Agent play verified | Notes |
|---|---|---|---|
| tripeaks | YES | **YES — full loop** | draw -> capture -> capture -> draw, every HUD counter proven |
| gmdice | YES | **YES** | 5 rolls, 5 result states; 3D20 renders three values "15 - 2 - 4"; 2x identical |
| opmt | YES | **YES (interactions)** | selection ring + rules-engine rejection + AI path, all rendered |
| fishrings | YES | **YES** | ring rotation per tap, 1860 state-change px, 2x identical |
| bouncy | menu only | no | Start Game root-caused: Box2D native .so frontier (hard) |
| dooz-compose | **FAIL (blank)** | no | Compose runtime missing — architectural frontier, documented |

**Flagship: TriPeaks full session ledger (all counters read from the HUD):**
draw 9d (-5 winings, Cards Remaining 23->22) -> capture 8c onto 9d (+1) ->
capture 7h onto 8c (+2, Current Streak 2) -> draw 6s (-5, remaining 21) ->
net **-7** — exactly the app's streak economy (-5 flat per draw, +1/+2/...
per capture streak). S120's "click->card mapping offset" is RESOLVED: the
mapping is 1:1; the confusion came from lobby-state runs + HUD crop
misalignment. 3-run frame determinism: IDENTICAL.

**Three generic runtime laws shipped (zero package checks):**
1. **R-NEW-409** — `RelativeLayout.LayoutParams.addRule(int[,int])` bridge:
   programmatic rules stored as `rl_rule_<N>` heap fields and transferred to
   the ViewNode rel_* booleans in the addView/setLayoutParams capture (AOSP:
   one rule array for XML + programmatic rules).
2. **R-NEW-410** — Start/End layout alias family in the inflater
   (`layout_alignParentStart/End`, `layout_alignStart/End`,
   `layout_toStartOf/End`, `layout_marginStart/End` -> LTR left/right).
   Ground truth: OPMT's board anchors its right column with
   `layout_alignParentEnd`; those buttons collapsed to x=0 over their left
   twins (view-tree: id40/41 both at (0,394)). Post-law: 9 buttons spread
   symmetrically around the wheel.
3. **R-NEW-411** — `setBackgroundResource(resid)` REPLACES the drawable:
   the render-stage resolve-once cache is now invalidated when the resid
   changes (AOSP View.java law). OPMT re-skins all 9 board buttons on every
   tap; before this law the re-skin never painted (stale first drawable).

**bouncy — exact root cause (hard frontier):** Start Game dies in
`BouncyActivity.<clinit>` -> `Box2D.init` ->
`SharedLibraryLoader.loadFile` -> `SharedLibraryLoadRuntimeException`
(APK ships `libgdx-box2d.so` for 4 ABIs; this runtime executes DEX
bytecode and cannot execute ARM native code), plus a secondary
JSONUtils/FieldLayoutReader cascade. Same family as the S118 libGDX .so
ledger entry.

**dooz-compose — honest FAIL:** blank frame; the app unwinds through the
Compose runtime (`La;` unwound `Lzs;.m` / `Lte1;.f` / `Lse1;.s` / `Lg;.q`
/ `Lg;.h` / `Lat;.a`, depth 10-17). Rebuilding Compose (Recomposer,
SlotTable, Applier, AndroidComposeView) is a subsystem-scale effort, not a
single law — documented as the deepest open frontier.

**Evidence:** `evidence/s121_full_sessions/` — 7 small English-only JPGs,
including the TriPeaks full-session HUD ledger sheet and the honest
dooz-compose blank-fail frame. Drivers: `scripts/autoplay/s121_*.py`,
calibration + session + matrix scripts `scripts/s121_*.py`.
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
