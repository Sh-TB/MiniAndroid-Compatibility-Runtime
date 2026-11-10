#!/usr/bin/env python3
"""S207 — post the game-loop verdicts: #557 (full L-07 verdict) + #536 (central)."""
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

L07 = """# [L-07 VERDICT] tictactoe FULL GAME LOOP PROVEN — X-win + O-win (red lines drawn) + stalemate + restart-with-score-persistence, all on the rebuilt post-C9 binary; PLUS a real finding: the post-C9 binary moved the input hit geometry

Verified on the REBUILT canonical binary `e6287d1a2c175cf0` (clean `make` on HEAD `fcaf91ba` tree; byte-identical to the pre-rollback rebuild — reproducible build confirmed), evidence `docs/evidence/s207_ttt_gameloop/` (commit `bdb01a6d`), scripts `scripts/s207_{gate,gameloop*,calibrate,taplaw}.py`.

**0. Baseline first (§9):** before any game-loop work the full gate battery was re-run on the rebuilt binary: goldens 3/3 (bouncy `8a6c24ac8a7d718e` / unote `3b8dcb0adbbc17a9` / dooz `a0fae9072313e2d1` — the ORIGINAL pins, no re-pins), gmdice `3891679d` rerun-identical ×2, microtimer 0-uncaught `b39665f6`, tictactoe no-tap deterministic ×3 `7354c1b231cd581d` — **ALL HOLD** (`evidence/s207/runs/S207_GATE.json`).

**What worked (EXECUTED on the real app, END-TO-END):**
- **X-win**: `X@2 O@0 X@4 O@1 X@6` → the anti-diagonal 2-4-6 completes and **the app draws its own red win line** through the three cells. Face `db2db9f5b176eb28` deterministic ×2, 0 uncaught. (x_win.jpg)
- **O-win**: `X@0 O@2 X@1 O@4 X@3 O@6` → O takes the 2-4-6 diagonal, **red line drawn by the app's own judge**. Face `0f60d3eec4e7c497` ×2, 0 uncaught. (o_win.jpg)
- **Stalemate**: 9-tap fill `X@0 O@4 X@2 O@5 X@3 O@6 X@7 O@1 X@8` → full board, **NO line** (the stalemate branch renders correctly). Face `cd6202ac23ea8b0b` ×2, 0 uncaught. (stalemate.jpg)
- **Restart-after-win**: the 5 X-win moves, then a 6th tap → `GameData.getEnded() → restart()` fires: **board CLEARED** (empty grid face `a5ae21eeb4f19bed` ×2) **and the score row persists 1|0** — the X side's "1" (narrow glyph) verifiably present vs the fresh 0|0 face; pixel ink 26175 vs 29198 blue in the score band, glyph-shape diff visible. (restart_score_1_0.jpg)
- Every recipe: deterministic ×2, **0 uncaught exceptions** across all 20+ runs this wave.

**What did not hold (honest negatives):**
- My first recipe batch (v1) was built on the S204/S206-era tap coordinates — and they **no longer land** on the post-C9 binary. The exact S206 two-tap invocation `(10,540,760),(16,250,480)` that rendered two pieces on `4f5c5b9a11a8b9d2` renders **only one piece** on `e6287d1a2c175cf0`. Root cause of the mismatch: the **C9 density/font stack moved the input hit geometry**, not the renderer (pieces still render where the hit-test says). This is a REAL finding for every future tap recipe, not a rendering regression.
- v1 'restart_after_win' had my own arithmetic error (X={4,6,8} is not a line) — the app CORRECTLY refused a win and continued turns; recorded as an accidental positive control of the win judge.

**What was decoded (the new tap law, `S207_TAPLAW.json` + `S207_CALIBRATION.json`):**
- Visual grid ink centers: **cols x = 287/539/791, rows y = 648/972/1296** (spacing 252/324).
- Hit law on `e6287d1a2c175cf0`: a tap lands the cell whose row band contains tap_y, band floor y=486 (taps at y=480 miss entirely — the old recipes' failure), rows band-split at 810/1134; **tap_y = row_center + 112 is the safe canonical form**; tap_x = col center (snapping verified 250→287, 830→791).
- First-tap-swallow does NOT exist: single-tap runs land (proven by p_center/p_r3/q_row3) — the v1 misses were pure geometry.

**What was integrated:** nothing new merged — this wave is pure verification + decode on the already-integrated C9 stack; the only tree change is curated evidence + scripts (`bdb01a6d`). No app-specific behavior added anywhere: the recipes drive the APK through its own input path.

**What improved in a real APK:** emmanuelttt on the post-C9 binary went from "board + 2-tap interaction" to **FULL GAME LOOP**: win judging (both sides), win-line rendering, stalemate branch, restart with score persistence — i.e., the complete GameData state machine exercised through real dispatched touches, all reproducible on one binary.

**What remains:** (1) the winner TEXT glyphs (SpriteBatch text sampling wall — still the named wall from L-06; the line renders, the word "O won!"/"X won!" is the remaining unreadable layer); (2) re-annotate the standing pins whose recipes depend on tap coordinates with the binary's hit-geometry identity (the §4 pin-hygiene task, now with concrete evidence it matters); (3) optional: 'restart' mid-game (without a win) + double-restart score accumulation.

**What exact test to perform next:** (1) re-run the SAME four recipes on the next binary that touches the density/font/input stack — if any face pin moves, the hit-geometry identity annotation (item 2) must catch it; (2) after the text wall falls, the same 4 faces must show readable winner text — same taps, no new recipe needed; (3) keep `s207_taplaw.py` as the calibration harness for ANY future tap recipe before its first run."""

CENTRAL = """# [S207 RECORD] tictactoe full game loop PROVEN + tap-law decoded on the rebuilt post-C9 binary `e6287d1a2c175cf0`; full gate battery HOLD; sweep verdict posted earlier this session

- **Rebuild**: workspace rollback hit mid-session; `git pull` + clean `make` reproduced the binary byte-identical (`e6287d1a2c175cf0`) — reproducible-build check PASSED.
- **Gate (§9, before new work)**: goldens 3/3 (bouncy 8a6c24ac / unote 3b8dcb0a / dooz a0fae907 — original pins), gmdice 3891679d rerun-identical, microtimer 0-uncaught b39665f6, ttt no-tap det-×3 7354c1b231cd581d. ALL HOLD. `S207_GATE.json`.
- **Game loop (L-07, verdict on #557)**: X-win 2-4-6 red line `db2db9f5b176eb28` ×2 / O-win 2-4-6 red line `0f60d3eec4e7c497` ×2 / stalemate 9-piece no-line `cd6202ac23ea8b0b` ×2 / restart-after-win cleared board + score 1|0 `a5ae21eeb4f19bed` ×2. All 0-uncaught. Evidence JPGs `docs/evidence/s207_ttt_gameloop/` (commit `bdb01a6d`).
- **Real finding**: post-C9 binary moved the input hit geometry (S206-era tap coords no longer land; exact replica run renders 1 piece instead of 2). Decoded law recorded in `S207_TAPLAW.json`: cols 287/539/791, rows 648/972/1296, band floor 486, canonical tap_y = row_center+112. Every future tap recipe must calibrate against its binary first.
- **Sweep**: full paginated re-sweep of 15 issues = 0 unreviewed, 0 coverage gaps (#536 c=6749467865).
- **Next**: winner-TEXT glyphs remain the named wall; pin-hygiene annotation (hit-geometry identity per pin) upgraded to concrete task; same 4 recipes re-run after any density/font/input change."""

if __name__ == "__main__":
    ids = {}
    ids["557_s207_l07_gameloop_verdict"] = post(557, L07)
    ids["536_s207_gameloop_record"] = post(536, CENTRAL)
    p = "/home/z/my-project/evidence/s200/posted_comment_ids.json"
    d = json.load(open(p))
    d.update(ids)
    json.dump(d, open(p, "w"), indent=1)
    print("LEDGER UPDATED:", ids)
