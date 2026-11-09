#!/usr/bin/env python3
"""S207 — post the full-sweep verdict to the central tracker #536 (golden rule)."""
import json, subprocess, sys

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"

def token():
    out = subprocess.run(["git", "credential", "fill"],
                         input="protocol=https\nhost=github.com\n",
                         capture_output=True, text=True,
                         cwd="/home/z/my-project").stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return ""

def post(issue, body):
    TOK = token()
    r = subprocess.run(["curl", "-s", "-X", "POST",
                        "-H", f"Authorization: token {TOK}",
                        "-H", "Accept: application/vnd.github+json",
                        "-d", json.dumps({"body": body}),
                        f"https://api.github.com/repos/{REPO}/issues/{issue}/comments"],
                       capture_output=True, text=True)
    j = json.loads(r.stdout)
    cid = j.get("id")
    if not cid:
        print(f"POST FAIL #{issue}: {r.stdout[:300]}")
        sys.exit(1)
    print(f"POSTED #{issue} comment id={cid}")
    return cid

BODY = """# [S207 SWEEP VERDICT] Full paginated re-sweep of ALL coder issues: 0 unreviewed, 0 coverage gaps — the S206 wave is complete and closed

Checked on HEAD `57096048` (S206 stack `8a37aab1` + `cad6467b` rebased under it), tooling `scripts/s207_full_sweep.py` + `scripts/s207b_coverage.py`, evidence `evidence/s207/s207_full_sweep.json` + `s207b_coverage_gaps.json`.

**Method (stronger than the S204 watermark check):**
1. FULL PAGINATION: all 15 issues fetched page-by-page (per_page=100, loop until short page) — this closes the #519 hole where exactly-100 total comments hid the newest page (first sweep of this session reported watermark `6727648006` for #519; the paginated sweep corrects it to `6745683059`).
2. ID-ORDER CHECK: every comment with id > my newest per issue, any author — 0 hits.
3. REPLY-COVERAGE CHECK (the new one): for EVERY non-`Sh-TB` comment on these issues, verified a LATER `Sh-TB` comment exists on the same issue — i.e. no coder delivery was ever passed over between two of my comments. **0 gaps.**

**Coverage table (issue: total comments / my watermark / unreviewed):**
- #450 C2: 3 / 6732818375 / 0 — #492 C3 dashboard: 26 / 6745567177 / 0 — #505 C5: 27 / 6732819199 / 0 — #515 C6: 3 / 6732819454 / 0 — #519 C8: 110 (paginated) / 6745683059 / 0 — #520 C7: 46 / 6746124034 / 0 — #521 C9: 59 / 6745395108 / 0 — #533: 2 / 6728863403 / 0 — #557 C3 tictactoe: 37 / 6745476427 / 0 — #566: 9 / 6732818945 / 0 — #536 central: 20 / 6744616599 / 0 — #574 C4 dagger W20: 3 / 6745619515 / 0 — #573 dooz ladder: 3 / 6744610392 / 0 — #570 tool audit: 6 / 6743645782 / 0 — #565 governance: 2 / 6743645269 / 0.

**Render-upload cross-check:** the #557 `[GAME RENDER — UPLOADED]` comment (c=6744704882) embeds `evidence/s204/runs/s204_ttt_tap2/screenshot.png` — HTTP 200 verified live today, plus the redundant curated copies committed at `57096048` (`docs/evidence/s204_ttt_board/ttt_board_after_2_taps_X_blue_O_cyan.png` + `ttt_board_no_tap_score_00.png`) also HTTP 200. Both image paths permanently reachable.

**Factual conclusion for the coders:** everything delivered through `2026-11-09T16:59:37Z` (C4 dagger DI chain, C7 W10 ledger, C8 wave-15, C9 phase-3 — integrated at `8a37aab1`, C3 ledger/win-judge) has a factual six-part review posted on its own issue. The review queue is EMPTY; the next coder delivery (whichever lands first) reopens it.

**Next own work (unchanged, per the L-06 + C9 verdicts):** full-game loop hardening on the rebuilt canonical binary — win/score/restart determinism runs, then the standing battery on the post-C9 tree."""


if __name__ == "__main__":
    post(536, BODY)
