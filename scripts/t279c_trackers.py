#!/usr/bin/env python3
"""T279 CONT-3 — post per-app tracker updates (#473/#475/#487/#489) with the
T279 verified findings. Token from git credential helper; never printed."""
import json
import subprocess
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
BASE = "https://api.github.com/repos/" + REPO


def get_token():
    p = subprocess.run(["git", "credential", "fill"],
                       input="protocol=https\nhost=github.com\n\n",
                       capture_output=True, text=True)
    for line in p.stdout.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    raise RuntimeError("no token")


TOKEN = get_token()


def comment(issue, body):
    req = urllib.request.Request(f"{BASE}/issues/{issue}/comments", method="POST",
        headers={"Authorization": f"Bearer {TOKEN}",
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "t279-agent",
                 "Content-Type": "application/json"})
    data = json.dumps({"body": body}).encode()
    with urllib.request.urlopen(req, data) as r:
        return json.load(r)


T279 = ("T279 two-run campaign, 2026-11-28: engine commits 344774e66 (base) "
        "-> f9e1d3314 (MeasureSpec getMode AOSP fix), binaries "
        "9c5e456b4790299e / 1a21be9fc9f6b016, v0.0.6.2+HEAD.")

POSTS = {
    473: f"""## T279 verification — GameMasterDice INTERACTIVE on the current engine ({T279})

**Two independent runs, BYTE-IDENTICAL face `3891679dff449331` — now proven across THREE engine builds** (S182 2026-11-06, recheck 2026-11-27 @ 96878de83, T279 2026-11-28 @ 344774e66): the strongest determinism class in the corpus.

- **Status: INTERACTIVE.** Click-test runs (identical deterministic sequence ×2) changed the frame: face `3891679dff449331` → `7ee46dd3692bb3d3`, app-owned pixels 182,535 → 753,437 (ct1==ct2). Dice UI visually verified 2026-11-28 ("Roll it!" + dice-type bar).
- uncaught 0 / NDFE 0 in every run; wall ~1.1s.
- Registry row: VERIFIED + `t279_status=INTERACTIVE`; evidence `evidence/t279/shots/gmdice_*.png` (tracked on main @ f1312668f) + raw logs in the session store.
- The APK remains the original release `de.duenndns.gmdice_8.apk` (SHA256 `1621eda11b5dbc0c…`, F-Droid).
""",
    475: f"""## T279 verification — honest CURRENT status correction ({T279})

**Current engine verdict: DEFAULT_BACKGROUND_ONLY (px 0, uncaught 0), face `b5a7a35d5fe0564b`, r1==r2==ct1==ct2** — this is a REGRESSION vs the registry's historical VERIFIED claim (the historical evidence stands; the current status is now corrected in the registry row with `t279_status=PARTIAL`, historical claim preserved in notes — no erasure).

- The click-test census found 0 clickable views at dispatch time; no frame change.
- Next blocker is not yet profiled for this title (game viewtree attach path; the app shares the S182-generation UI stack with stack.tower3d which shows the same default-background class).
- Recorded conservatively: PARTIAL, first divergence `DEFAULT_BACKGROUND_ONLY (game content never drawn)`.
""",
    487: f"""## T279 verification — PF Dicer CURRENT-REPRODUCIBLE ({T279})

**Two independent runs, BYTE-IDENTICAL face `31ffa499c59e3e41` == the S182 2026-11-06 historical face.** Dice UI face rendered (px 1,041, 163 distinct colors).

- uncaught 12 in every run — nonfatal: `SavedStateHandleAttacher.onStateChanged` IllegalArgumentException (androidx lifecycle), recorded as the first divergence; rendering unaffected.
- Click-test: **0 clickable views at the dispatch census** — the roll button's listener registers after the census point, so interaction is NOT yet proven by frame change (kept honest: status stays CURRENT-REPRODUCIBLE, not INTERACTIVE).
- Registry row registered (was one of the 6 S182 titles absent from the registry until the T279 reconciliation).
""",
    489: f"""## T279 verification — itsfrz TicTacToe PARTIAL, listener gap named ({T279})

**Two independent runs, face `d55056a8928a26ff` (== the S27 wall face), DEFAULT_BACKGROUND_ONLY px 0, uncaught 10, r1==r2.**

- The custom-cell click-listener registration gap from S23 is confirmed at the current engine: `setOnClickListener`-registered custom cells report **0 clickable views** at the dispatch census.
- Per-app next blocker: custom-view clickability census + the listener registration path (recorded in the registry row `t279_status=PARTIAL`).
""",
}


def main():
    for issue, body in POSTS.items():
        r = comment(issue, body)
        print(f"posted #{issue}:", r["html_url"])


if __name__ == "__main__":
    main()
