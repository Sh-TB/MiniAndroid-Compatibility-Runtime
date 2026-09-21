#!/usr/bin/env python3
"""s73_github_comments.py — S73 PART A6/D: dated evidence comments on the
canonical [EXEC] issues. Every comment carries measured evidence."""
import json
import os
import sys
import time
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
API = f"https://api.github.com/repos/{REPO}"
TOKEN = os.environ.get("GH_TOKEN")


def api(method, path, body=None):
    req = urllib.request.Request(f"{API}{path}", method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    data = json.dumps(body).encode() if body is not None else None
    with urllib.request.urlopen(req, data) as r:
        return json.load(r) if r.status != 204 else {}


def comment(num, body):
    api("POST", f"/issues/{num}/comments", {"body": body})
    print(f"commented #{num}")


def main():
    S73 = "S73 UPDATE — 2026-09-21"

    # ---- #13 Snake: full evidence (keep OPEN until commit SHA known)
    comment(13, f"""{S73}

Status: OBSERVED (autonomous chain complete; closing review after docs commit)

Milestone:
AUTONOMOUS GAMEPLAY ACHIEVED via real input chain — no state injection,
no renderer bypass, no screenshot fabrication.

Controller (C1/C3 compliant):
* vision: rendered-frame pixel extraction ONLY (snake #FF4081, food
  #0000ff, 20x20 grid / 39px cells)
* actuator: 23 scheduled taps (x,y@frame) through the canonical
  TouchDispatcher DOWN/UP law pipeline (F-117 scheduled-input extension;
  all taps hit real button view ids 441-445)
* tap geometry: view_tree.json button centers (legitimate observable UI)

Results (per full run, 90 frames):
* 88 head-advance moves, 22 accepted direction turns
* 1 food capture: frame 34, snake grew 3->4 (cells px 3042->6084),
  food respawned (0,0)->(9,0) same render
* no game over during the autonomous session
* 3-run reproducibility: 3 independent full runs, per-frame PNG sha
  equality — 90/90 frames IDENTICAL x3 (determinism_proof.json)

C4 probes (real taps, app logic authoritative):
* reverse-direction guard: tap LEFT while moving RIGHT -> REJECTED
  (direction stayed R, heads (15,10)->(18,10))
* wall/wrap law: head (19,10) -> (0,10) — WRAPS, no wall death
* game over: engineered self-collision (head re-entry into occupied
  (5,10)) -> GAME-OVER OBSERVED frame 94 (panel -> game-over surface,
  1,868,783 non-white px)
* restart via START after game over: NOT OBSERVED (honest open —
  possible Dialog-based restart path, not exercised)
* deterministic timing: whole session byte-identical x3

Evidence:
* docs/evidence/s73_snake_autoplay/run_01..03/ (frames,
  gameplay_trace.json per C5 schema, SHA256SUMS)
* snake_autoplay.gif (39KB, real run_01 frames only)
* screenshot_metrics.json (B3 gate: 1080x1920; snake #ff4081 3042->6084
  px = length 2->4; food #0000ff 1521 px = 1 cell)
* determinism_proof.json + autoplay_summary.json

Regression: fixtures 25/25 rc=0 (zero f141-throws) on the current binary
(container rebuild + F-117 extension); corpus re-run completed; W4 legacy
recipe re-verified byte-identical (final frame pixel sha 1a419545419deb3a).

Remaining: canonical docs promotion (this commit), then closing review.""")

    # ---- #14 Dooz: honest reclassification + S73 re-verification
    comment(14, f"""{S73}

Status: BLOCKED (unchanged frontier) + HONEST METRIC RECLASSIFICATION

Re-verification (current binary, canonical corpus recipe):
* dooz x3 independent runs byte-identical, final frame pixel sha
  0e334abe1b10b592 — matches S72-W3/W4 stored determinism exactly.

Metric reclassification (B4 audit finding):
* The "23472 non-white px" surface is 23,472 PURE BLACK pixels forming a
  (0,0)-(489,47) rectangle at the top-left.
* S73 control experiment: Stopwatch — an app whose manifest declares NO
  launchable Activity — renders a BYTE-IDENTICAL frame (same 23,472 px,
  same sha 0e334abe1b10b592).
* Therefore the 23472-px surface is an ENGINE-DEFAULT black region, NOT
  dooz content. The S72-W3 phrasing "197 -> 23472 px real content" is
  corrected to: "197 px placeholder -> 23,472 px engine-default black
  region (shared face with activity-less apps)". dooz's own UI surface
  remains UNRENDERED.
* This does NOT change the recorded blockers: F-146 (g8.a@569 -> ur.e(J)
  null receiver) and F-147 (onCreate@228 -> ViewGroup.getChildAt on null)
  remain the exact first divergences; F-145 remains the visual frontier.
  F-141 stays CLOSED.

New sub-lead (queued, not yet root-caused):
* locate the engine painter of the shared black region (canvas-shadow
  default-paint context is a candidate; no law claimed without upstream
  evidence).

No old history rewritten — this comment is the dated correction record.""")

    # ---- per-app corpus re-run comments (B2/D)
    per_app = {
        15: ("Unote", "231,120 px themed UI, final px sha 2928a026c4a88a14 "
             "— matches the post-F-141f record exactly; rc=1 (app-own "
             "stopper, deterministic). Ladder open: input/state."),
        16: ("Telegram", "NOT re-executed at current HEAD (heavy target; "
             "historical checkpoint-M evidence stands as recorded in "
             "closed issues #1-#8). Honest: HISTORICAL-CLAIM-UNVERIFIED-"
             "AT-CURRENT-HEAD until a fresh run is driven."),
        17: ("GMDice", "182,628 px, final px sha a011e9e9eee2cb42, det x3 "
             "same-recipe; F-137-era dispatch intact on rebuilt binary."),
        18: ("MicroTimer", "1,041,437 px (50.22% of frame — matches the "
             "W1 dashboard's 50.2%), final px sha e4869001e3638d69."),
        19: ("FishRings", "splash frames 0-3 = 0 px (white); frames 4-8 "
             "= 2,073,360 px REAL BOARD — the F-142 board law reproduces "
             "EXACTLY on the rebuilt binary. Interaction re-run remains "
             "available via the S10 recipe; ladder completion open."),
        20: ("TriPeaks", "205,638 px lobby renders (matches the S7-era "
             "lobby record); board geometry blocker R-NEW-388 unchanged."),
        21: ("Bouncy", "2,073,600 px full-frame render (100% dashboard "
             "face, final px sha 108618ac7c58083b); L6 click evidence "
             "stands; L7 loop open."),
        22: ("Stopwatch", "rc=0; manifest has NO launchable Activity "
             "(by design). Rendered face = the engine-default black "
             "region (23,472 px, sha 0e334abe1b10b592 — identical to "
             "dooz's face; see #14 reclassification). F-143 service "
             "family remains the generic frontier."),
        23: ("OPMT", "213,286 px menu (real strings face), final px sha "
             "60e5611daaf01e58; rc=0 at corpus recipe; app-own IOOBE "
             "stopper on deeper play unchanged (OBJECT-IDENTITY family)."),
    }
    for num, (name, ev) in per_app.items():
        comment(num, f"""{S73}

Status: unchanged (see issue body) — current-HEAD re-execution evidence
recorded per PART B2/D.

Corpus re-run (canonical recipe: real-dalvik, 9 frames @1500ms, current
binary = container rebuild + F-117 scheduled-input extension):

Evidence: {ev}

Regression context: fixtures 25/25 rc=0 (zero f141-throws); dooz det x3
byte-identical; snake W4 recipe re-verified byte-identical
(1a419545419deb3a). Zero regressions observed on this app's face.
Full matrix: docs/evidence/S73/S73_REPORT.md (this commit).""")
        time.sleep(0.2)

    print("all comments posted")


if __name__ == "__main__":
    main()
