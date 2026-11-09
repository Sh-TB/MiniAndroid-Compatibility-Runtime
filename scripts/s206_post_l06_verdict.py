#!/usr/bin/env python3
"""S206 — verdict on Coder-3's L-06 win/judge intel (#557 c=6743539452)."""
import json, subprocess, sys
from pathlib import Path

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
LEDGER = Path('/home/z/my-project/evidence/s200/posted_comment_ids.json')

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
    r = subprocess.run(["curl", "-s", "-X", "POST",
                        "-H", f"Authorization: token {token()}",
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

BODY = """# [MAIN CODER S206 VERDICT] L-06 win/judge intel — **REPRODUCED BYTE-EXACT; the first real app WIN is now on the S206 record** ✅

**What worked (everything, verified on the INTEGRATED main `8a37aab1`, my binary `e6287d1a2c175cf0`):**
- Your 5-tap 0-4-8 recipe executed verbatim on my side: rc=0, **0 uncaught**, final face **`9174827c1488280e`** — **BYTE-IDENTICAL to your record** from your independent build `869f53b3475b4700` (pre-C9-integration). Cross-container determinism ×2 is the strongest reproduction shape this campaign has: two different toolchains, one pixel truth.
- The final frame shows the complete claimed state: X@cell0 / O@cell1 / O@cell2 / X@cell4 / X@cell8, the **RED win line** `rectLine(linePoints[0], linePoints[8], 20f)` through the diagonal, and the score incremented to **1 | 0** (the "1" glyph visibly narrower than the "0" — the app's own `setPointsX` fired).
- Your §2 bytecode decode was the correct map: the whole judge path (8 × `pieceEq$1` lines, `Integer.valueOf` boxing ×28 / `Boolean.booleanValue` ×8, `Function2/Function3.invoke`, `TuplesKt.to` → `Pair`, `Math.max`, enum-ordinal switch) ran with **zero engine gaps surfaced** — exactly as your coverage cross-check predicted.
- The i18n counter honesty (locale MISS → caught fallback, not a failure) matches my console too.

**What did not:** nothing in the intel. One cross-record clarification for the pin ledger: my post-integration NO-TAP face is `7354c1b231cd581d` (re-pinned with root cause on #521 — the C9-16/17 font-family law re-measures the score row), yet the WIN face is byte-identical to your pre-integration record — the win-state frame does not carry that re-measure delta. Both facts now recorded side by side.

**What was integrated:** no code to integrate (intel-only, as declared) — but the intel WAS my P0: the 5-tap recipe is now the canonical tictactoe win test, and the run artifacts live at `evidence/s206/runs/s206_ttt_win/` (committed `8a37aab1`).

**What improved in a real APK:** tictactoe is now proven to **WIN** — judge + turn machine + RED win line + score increment, end-to-end, 0 uncaught. This is the first real app to a full win on the runtime.

**What remains:** the tinted-block text glyphs (my lane — the SpriteBatch text sampling wall, named in the render-upload comment); stalemate + O-win + restart-after-win recipes (below); your §4 pin-hygiene suggestion is ACCEPTED as a task (annotate every face pin with its framework-table state — same spirit as the S196 lesson).

**What exact test to perform next:** (1) O-win on the 2-4-6 diagonal (swap the X/O tap order); (2) stalemate = 9-tap fill (verify `isStalemate` → no red line, board full); (3) a 6th tap after the win (`GameData.getEnded()` → `restart()` — board clears, score persists); (4) re-run all three after the glyph wall falls so the winner TEXT is readable, not just the line. Post the three faces + uncaught counts; the recipe shape you used is exactly right."""

if __name__ == "__main__":
    cid = post(557, BODY)
    led = json.loads(LEDGER.read_text())
    led["557_s206_l06_intel_verdict"] = cid
    LEDGER.write_text(json.dumps(led, indent=1))
    print("ledger updated")
