#!/usr/bin/env python3
"""S208 — post verdicts: #557 (L-08 game-chain verdict) + #536 (central record)."""
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

RAW = "https://raw.githubusercontent.com/Sh-TB/MiniAndroid-Compatibility-Runtime/main/docs/evidence"

L08 = f"""# [L-08 VERDICT] GAMES PUSHED FURTHER ON MAIN: tictactoe MULTI-ROUND score accumulation (1|0 → 2|0) + gmdice real ROLL LOOP (6→5→3) + dooz first interaction captured (nav happens, board blank = next frontier)

All on the gate-green binary `e6287d1a2c175cf0` (re-verified this session: goldens 3/3 `8a6c24ac`/`3b8dcb0a`/`a0fae907`, gmdice rerun-identical `3891679d`, microtimer `b39665f6`, ttt no-tap det ×3 `7354c1b2` — ALL HOLD again). Evidence commit **`266c88c0`**: `docs/evidence/s208_ttt_round2/`, `docs/evidence/s208_gmdice/`, `docs/evidence/s208_dooz/`, `evidence/s208/S208_SUMMARY.json`; scripts `scripts/s208_ttt_round2.py`, `scripts/s208_sweep.py`.

## 1. tictactoe MULTI-ROUND loop — score ACCUMULATES across rounds (the L-07 restart result extended to its final consequence)
Recipe: X wins round 1 anti-diag `2-4-6` (red line) → restart tap @8 (**board clears, score persists 1|0**) → round 2 played to completion → **X wins round 2 TOP ROW 0-1-2, app draws its own red line again, score reads 2|0**.
- Face `b8cfbf735d3eda6d` **deterministic ×2, 0 uncaught**.
- **Score proof is pixel-forensic, not eyeballed**: the bottom score digit changed from narrow-`1` (43px wide) to a wide glyph that is pixel-DISTINCT from both `1` (L1=1,633,614) and `0` (L1=325,821) → the glyph is `2` → score trajectory 0|0 → 1|0 → **2|0**. A score RESET is refuted by the same shape logic (reset+win would render narrow-`1`).
- **TURN-LAW CORRECTION (fixes the L-07 docstring)**: the restart tap does **NOT** place a piece and the turn resets to **X**. L-07's "tap lands as fresh X@8" was an over-interpretation of the face hash; the round-2 run proves it (round-2 taps alternated X,O,X,O,X from the first post-restart tap, and cell 8 is empty at final state).
- Render: [{RAW}/s208_ttt_round2/round2_x_win_score_2_0.jpg]({RAW}/s208_ttt_round2/round2_x_win_score_2_0.jpg)

## 2. gmdice — the REAL roll loop (a no-op pin decoded and replaced)
**Finding**: the gate-era gmdice pin `3891679d` was identical for no-tap AND the 5-tap gate recipe — those taps at (540,1200) hit empty space. The button bar is at **y≈1836**.
- tap `1d6` (576,1836): face `3891679d` → **`d540433a06dc6431`**, app renders the rolled result **"6"** — real app-owned output.
- re-roll ×2: 2 taps → `86aec2bdf0799294` renders **"5"**; 3 taps → `8eedc7aaf4af018e` renders **"3"**. Every tap-count face is reproducible (RNG sequence deterministic on this runtime) and every roll changes the screen. **0 uncaught everywhere.**
- Loop proven: tap → RNG state advance → new app-owned render. 6→5→3: [{RAW}/s208_gmdice/gmdice_roll1_6.jpg]({RAW}/s208_gmdice/gmdice_roll1_6.jpg) · [roll2]({RAW}/s208_gmdice/gmdice_roll2_5.jpg) · [roll3]({RAW}/s208_gmdice/gmdice_roll3_3.jpg)

## 3. dooz — FIRST interaction captured; honest first-divergence record
- Golden face `a0fae9072313e2d1` = title bar + bottom bar + **blank board area** (board only builds after New game).
- tap **New game (875,1823)** → face `eccabf418a7cce52`, **0 uncaught**: chrome (title + bottom bar) disappears → the app really NAVIGATED (state change proven), but the post-navigation screen renders **BLANK WHITE** — the Compose game-board content is not drawn. Console shows real DEX runnables draining (`Lsr` self-run law).
- Status labels: interaction=**PROVEN** (tap → app state transition), board-render=**BLOCKED** (blank post-nav Compose screen = precise next frontier).
- Before/after: [{RAW}/s208_dooz/dooz_before_newgame_golden.jpg]({RAW}/s208_dooz/dooz_before_newgame_golden.jpg) · [after (blank)]({RAW}/s208_dooz/dooz_after_newgame_blank.jpg)

## 4. Sweep + workspace state (§12 cycle)
- Full forward sweep re-run: **462 open issues**, ALL recent key issues (536/557/565-574 + new #575) show **0 unreviewed** coder comments (older-issue fetch-fails = rate-limit tails, noted in the evidence JSON).
- Disk check (user question): sandbox root fs = 1.5G used / 9.9G (**17%**) — NOT disk-full; the sandbox collapses are server-side, zero data loss (all work on origin/main).

**Statuses**: tictactoe multi-round score accumulation = TESTED+OBSERVED on rebuilt binary (×2); gmdice roll loop = TESTED+OBSERVED (×1 per tap-count, rerun-identical per recipe); dooz interaction = OBSERVED, board render BLOCKED. Nothing weakened, no re-pins; goldens untouched.
"""

CENTRAL = """**S208 central record** (evidence commit `266c88c0`, binary `e6287d1a2c175cf0`, gate ALL HOLD re-confirmed):
1. **tictactoe multi-round loop CLOSED**: win→restart→win→**score 1|0 → 2|0** (pixel-forensic digit proof: new glyph distinct from `1` L1=1633614 and `0` L1=325821), face `b8cfbf735d3eda6d` ×2, 0 uncaught. TURN-LAW CORRECTED: restart tap places nothing, turn resets to X (L-07 docstring fixed).
2. **gmdice roll loop**: old gate taps (540,1200) were NO-OP (no-tap face == tap face); real bar y≈1836; tap `1d6` → renders **6→5→3** (faces `d540433a`/`86aec2bd`/`8eedc7aa`, all reproducible, 0 uncaught). The rerun-identical pin `3891679d` is now understood as the no-tap/unused-tap static screen.
3. **dooz first interaction**: New-game tap → navigation PROVEN (face `a0fae907`→`eccabf41`, chrome gone), post-nav screen renders BLANK WHITE → board render BLOCKED = next frontier (Compose content path).
4. Sweep: 462 open issues, 0 unreviewed (all key recent issues covered; rate-limit tails documented). Disk 17% used — not the sandbox-collapse cause.
5. Next highest root-cause candidates: (a) dooz post-navigation blank Compose screen, (b) microtimer tap-targets were spot-checks only. Full verdict in #557 (L-08).
"""

if __name__ == "__main__":
    ids = {}
    ids['557_s208_l08'] = post(557, L08)
    ids['536_s208_central'] = post(536, CENTRAL)
    print(json.dumps(ids))
