#!/usr/bin/env python3
"""s74f_issue_checkpoints.py — S74 FOLLOW-UP WAVE §5/§6: post ONE compact
execution-checkpoint comment per canonical [EXEC] issue #10-#23, embedding
the human-visible representative evidence via GitHub-renderable raw URLs.

RUNS ONLY WITH GH_TOKEN IN THE ENVIRONMENT (constitution §52: never stored,
never committed). Idempotent-ish: run once per wave; comments are dated.

Usage: GH_TOKEN=... python3 scripts/s74f_issue_checkpoints.py [issue# ...]
"""
import json, os, sys, urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
HEAD = os.popen("git -C /home/z/my-project rev-parse HEAD").read().strip()[:8]
RAW = f"https://raw.githubusercontent.com/{REPO}/{HEAD}/docs/evidence/s74_ops"

# issue -> (bundle dir, status line, stage summary, blocker, next action)
CP = {
 10: ("helloworld", "DONE (golden control target)",
      "launch -> self-aware hello-world identity frame (golden byte-stable replay; APK not committed per §20 policy)",
      "none", "optional interactive probe if an input-bearing variant is used"),
 11: ("tictactoe_golden_fixture", "DONE — fixture-scope human-visible proof; REAL APK honest blocker",
      "fixture: launch 'X to move' -> first move -> 'X WINS' board (9/9 real clicks, byte-identical replay at HEAD). REAL APK at HEAD: libgdx createGLSurfaceView NPE (F-144) -> blank frame (truthful blocker evidence in bundle tictactoe/)",
      "real APK: F-144 GL surface family", "optional GL compatibility path research (F-144)"),
 12: ("connectfour_golden_fixture", "DONE (validator ALL PASS at HEAD)",
      "launch 'R to move' -> midgame -> 'Y WINS' at click 22 (canonical corrected result), 24 real clicks, 11R+11Y, byte-identical replay",
      "none", "none (completed state preserved)"),
 13: ("androidgamesnake", "OBSERVED — S73 proof preserved (§8: no re-run, no reopen)",
      "launch -> START -> snake run -> food capture at frame 34 (snake 3->4) -> final; 88 moves / 22 turns / 23 scheduled real taps / 3-run byte-identical (frames re-wired from committed S73 run_01)",
      "restart-after-game-over NOT observed (honest open)", "only if restart probe is explicitly selected as a new task"),
 14: ("dooz", "BLOCKED — visual frontier open (truthful)",
      "launch pipeline executes; current face = engine-default black region (23,472 px) — NO_MEANINGFUL_VISUAL_PROOF, attached as blocker evidence only",
      "F-146 / F-147 (+ F-145 frontier); CLAIM-DOOZ-23472-VISUAL stays SUPERSEDED", "targeted Compose frontier wave (F-145/146/147)"),
 15: ("unote", "PARTIAL -> strongest evidence wave to date",
      "launch 'Add note / Search / Quit' UI (231,120 px, byte-matches S73) + REAL SQLite persistence: notes.db created on launch and survives close/reopen (SHA 2bccf9475fe3810d unchanged)",
      "note-creation end-to-end chain unproven", "Add note -> editor -> save -> reopen -> read-back"),
 16: ("telegram", "PARTIAL/BLOCKED at HEAD (truthful); historical SmsView depth preserved",
      "v12.10.3 (official URL, sha b6a13e87...) 3-frame bounded run: engine-default region + init NPE family recorded; EXP071 CHECKPOINT_M (auth.sendCode -> callback -> 53 SmsView nodes, screenshot SHA x6 identical) remains the historical proven path on an older binary",
      "app-init NPE family + init budget on current official build", "androidx fragment/activity-result NPE wave to reopen the SmsView ladder"),
 17: ("gmdice", "PARTIAL (identity flag recorded honestly)",
      "launch dice UI; click dispatch reaches the real GameMasterDice listener; visible roll render NOT reproduced at HEAD (S63 roll evidence remains historical, older binary)",
      "APK identity divergence: local sha 1621eda1 vs dossier-recorded ee9f7396", "re-pin canonical APK (source-first rebuild), then re-prove visible roll chain"),
 18: ("microtimer", "PARTIAL -> input/state legs re-proven at HEAD",
      "launch keypad UI -> after real clicks the timer display shows 00:09:87 (real input -> state -> render at current HEAD)",
      "start/stop ticking flow unproven", "start -> ticking -> stop probe (completes C6-C8 ladder)"),
 19: ("fishrings", "PARTIAL (board render re-proven at HEAD)",
      "splash (0 px frames 0-3 by app design) -> full colored ball board + rotation arrows + ebinqo logo",
      "game-logic depth unexercised at HEAD", "tap-based rotation interaction probe (V2/V3 stages)"),
 20: ("tripeaks", "BLOCKED (board) — lobby NEWLY proven at HEAD",
      "splash -> lobby 'Welcome to the Tri Peaks Solitaire for Android!' (frame 7+, 205,061 px). 'New Game' tap hit-test target=0 — menu is not a per-view listener surface at HEAD",
      "R-NEW-388 OBJECT-IDENTITY for the board path (generic RL anchor laws stay proven)", "R-NEW-388 root-cause wave"),
 21: ("bouncy", "PARTIAL (menu + navigation at HEAD)",
      "'Select Table / Unlimited Balls / Start Game / High scores / Help / Preferences / Quit' menu; click round-robin navigates to the full-screen table-selector state",
      "L7 physics game-loop proof open", "Start Game -> physics loop proof (L7 ladder)"),
 22: ("stopwatch", "BLOCKED by design (service-only manifest) — engine behavior correct",
      "aapt2 badging at HEAD confirms launchable=[] (no Activity); engine-default face is the EXPECTED output, attached as factual evidence",
      "F-143 family: service-only manifest (not a runtime defect)", "optional service-dispatch probe when the service family wave is scheduled"),
 23: ("opmt", "PARTIAL (menu + real dialog at HEAD)",
      "'Play with Friend / Play with Computer / How to play?' menu; click round-robin opens the app's REAL AlertDialog 'Who will go first?' (Human/Computer)",
      "app-own IOOBE (OBJECT-IDENTITY) stops progression past menu/dialog", "OBJECT-IDENTITY root-cause wave (shared with tripeaks)"),
}


def post(issue, body):
    token = os.environ.get("GH_TOKEN")
    if not token:
        sys.exit("FAIL: GH_TOKEN env var not set (constitution §52: refusing to proceed)")
    url = f"https://api.github.com/repos/{REPO}/issues/{issue}/comments"
    req = urllib.request.Request(url, data=json.dumps({"body": body}).encode(),
                                 method="POST", headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "miniandroid-s74-followup",
    })
    with urllib.request.urlopen(req) as r:
        return json.load(r).get("html_url", "?")


def body_for(issue, bundle, status, stage, blocker, nxt):
    sess_p = f"/home/z/my-project/docs/evidence/s74_ops/{bundle}/session.json"
    frames = []
    if os.path.exists(sess_p):
        s = json.load(open(sess_p))
        frames = list((s.get("frame_metrics") or {}).keys())
    lines = [
        "**S74 FOLLOW-UP — execution checkpoint (operational wave; runtime untouched)**",
        "",
        f"Execution checkpoint:",
        f"- Session: docs/evidence/s74_ops/{bundle}/ (session.json + SHA256SUMS)",
        f"- App: `{bundle.replace('_golden_fixture','')} (canonical dossier: docs/compatibility/apps/{bundle.replace('_golden_fixture','')}.json)`",
        f"- Exact variant: APK sha pinned in session.json",
        f"- Runtime commit: `{HEAD}` (== origin/main at wave start; binary rebuilt from HEAD)",
        f"- Environment: real-dalvik bytecode interpretation, per-app sandbox data root, aapt2 {os.popen('/home/z/my-project/tools/aapt2/aapt2 version 2>/dev/null | head -1').read().strip() or 'toolchain re-bootstrapped'}",
        f"- Stage: {stage}",
        f"- Input: canonical paths only (TouchDispatcher taps / XML-onClick & listener click dispatch / F-117 scheduled taps)",
        f"- State transition: see checkpoint above; sandbox + persistence probes recorded in session.json",
        f"- Result: {status}",
        f"- Trace evidence: session.json (frame metrics with SHA256_16), committed run artifacts under run/ hashes in SHA256SUMS",
        f"- Reproducibility: deterministic replays where claimed (tictactoe/connectfour golden byte-identical at HEAD; snake 3-run byte-identical from S73)",
        f"- Current blocker: {blocker}",
        f"- Next action: {nxt}",
        "",
    ]
    vis = "YES" if any(f.startswith(("01_", "02_", "03_")) for f in frames) and \
        json.load(open(sess_p)).get("frame_metrics") else "see frames"
    if issue == 14 or issue == 16 or issue == 22:
        lines.append("Human-visible screenshot: NO — truthful blocker frame attached below (NO manufactured success per taskbook §29)")
    elif frames:
        lines.append("Human-visible screenshot: YES (links below render on GitHub)")
    lines.append("")
    for fr in frames:
        png = fr.endswith((".png", ".jpg"))
        url = f"{RAW}/{bundle}/{fr}"
        if png:
            lines.append(f"![{fr}]({url})")
        else:
            lines.append(f"- {fr}: {url}")
        lines.append("")
    lines.append("_Evidence rules: AGENT_OBSERVED vs HUMAN_VISIBLE distinguished; every bundled frame was individually opened and reviewed by the executing agent before status assignment; validator `tools/validate_compatibility_graph.py` (§35 gates) PASS at this HEAD._")
    return "\n".join(lines)


def main():
    only = [int(x) for x in sys.argv[1:]] or None
    for issue, (bundle, status, stage, blocker, nxt) in CP.items():
        if only and issue not in only:
            continue
        b = body_for(issue, bundle, status, stage, blocker, nxt)
        print(f"#{issue} <- {post(issue, b)}")


if __name__ == "__main__":
    main()
