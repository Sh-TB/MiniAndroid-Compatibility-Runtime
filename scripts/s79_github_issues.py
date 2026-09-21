#!/usr/bin/env python3
"""s79_github_issues.py — S79 issue sync: dated evidence comment on every open
[EXEC] issue + honest closure of #15/#17/#18 (ladders complete at HEAD).
GH_TOKEN read from /home/z/my-project/.secrets/gh_token (never echoed)."""
import json
import os
import urllib.request

TOKEN = open("/home/z/my-project/.secrets/gh_token").read().strip()
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
HEAD = "S79 wave (final binary: R-NEW-399 + R-NEW-400; main pre-push)"
API = f"https://api.github.com/repos/{REPO}"


def api(path, method="GET", body=None):
    req = urllib.request.Request(
        f"{API}{path}", method=method,
        data=json.dumps(body).encode() if body else None,
        headers={"Authorization": f"Bearer {TOKEN}",
                 "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode() or "{}")


COMMENTS = {
 14: ("**S79 EXECUTION CHECKPOINT — current-HEAD re-proof (runtime advanced beneath this issue)\n\n"
      "- Real run x2 at the S79 binary: visual face unchanged — 23,472 px engine-default "
      "(honest NOT_HUMAN_VISIBLE, byte-matches the S73/S78 record).\n"
      "- The F-152/F-154 fixes (S78) remain in place beneath the visual frontier "
      "(unsafeNPE 0, setIterNPE 0; f152 regression 6/6).\n"
      "- Still OPEN, honestly: the Job ISE chain (`Loj0;.T pc=49` — \"Job ... is already "
      "complete or completing\", observed x2 this wave, untraced) + F-147 null-producer "
      "trace + F-145 visual surface. These are the next depth links; nothing faked.\n"
      "- Session: run/s79_reproofs/dooz_run{1,2}; report: docs/foundation/s79/S79_REPORT.md"),
 15: ("**S79 — LADDER ITEM CLOSED: input → state change visible in screenshot (proven at HEAD)**\n\n"
      "- Real click-test run x2 at the S79 binary (unote vc30): tap on **Add note** → the "
      "app's REAL editor screen opens — Title field, \"Note ✍︎\" field, **Save / Return** "
      "buttons; measured diff vs pre-click frame = 13,032 sampled px (≈208K full-res), "
      "frame SHAs 2928a026c4 → dda89e95bf.\n"
      "- Persistence is real: [SQLITE-SHADOW] notes.db opened via SQLiteOpenHelper chain "
      "(getWritableDatabase dispatched through the superclass law C013-HIER), onCreate "
      "execSQL + rawQuery ran.\n"
      "- Evidence stills: docs/evidence/s79/reproofs/unote_{main_menu,after_add_note_tap}.jpg\n"
      "- Ladder: every item now checked at HEAD → **closing as completed**."),
 16: ("**S79 EXECUTION CHECKPOINT — honest status unchanged (deliberate)**\n\n"
      "- The checkpoint-M chain (EXP-064..071) remains a HISTORICAL claim; the "
      "current-HEAD re-execution was NOT run this wave (v12.10.1 real init ≈540s + "
      "multi-DEX interpretation is a dedicated wave by its own cost law).\n"
      "- Marker HISTORICAL-CLAIM-UNVERIFIED-AT-CURRENT-HEAD stays. No evidence, no claim."),
 17: ("**S79 — LADDER CLOSED: roll transition re-proven at current HEAD; multi-roll now PROVEN**\n\n"
      "- Roll results RENDERED (real GameMasterDice.roll → setText on view_37): "
      "'2 · 4 · 4', '6', '5', '3' — 5/5 click-test dispatches; each click frame differs "
      "from pre-click (distinct SHAs).\n"
      "- **S78 decor-offset hypothesis REFUTED (honest)**: the recorded multi-roll blocker "
      "(\"tap hit-test target=0\") was STALE COORDINATES — S78 tapped (540,1714); the real "
      "button row is y=1776..1920 (view_tree.json). With the real button center (580,1848): "
      "`[F117-TAP] frame 6 DOWN (580,1848) target=41` → '6'; `frame 14 → target=41` → '5' — "
      "two rolls across frames, state change visible each time (det x2).\n"
      "- Random.nextInt REC-MISS (F-114 family) remains the honesty frontier for "
      "distribution claims — recorded, not hidden.\n"
      "- Evidence: run/s79_reproofs/gmdice_multiroll{,2}; "
      "docs/evidence/s79/reproofs/gmdice_roll_result_rendered.jpg\n"
      "- Ladder complete at HEAD → **closing as completed**."),
 18: ("**S79 — LADDER ITEM CLOSED: state change re-proven at current HEAD**\n\n"
      "- Real click-test run x2 at the S79 binary: clicks → timer display running — "
      "00:00:00 → 00:00:09 → 00:00:98 (setText on view_112); 12 views probed / 11 changed.\n"
      "- Evidence still: docs/evidence/s79/reproofs/microtimer_timer_running.jpg\n"
      "- Ladder complete at HEAD → **closing as completed**."),
 19: ("**S79 — S10 INTERACTION CHAIN CLOSED AT HEAD (new runtime law)**\n\n"
      "- New failure found + closed (F-155 → R-NEW-400): every ring onClick died in "
      "GameActivity.sound() on a NULL MediaPlayer (create was an unbridged REC-MISS stub "
      "returning null — same §12 silent-propagation family as F-152). Implemented the "
      "AOSP MediaPlayer object law: create → non-null PREPARED player; start/pause/stop/"
      "release per the state table.\n"
      "- POST-FIX: 3 board taps (real ring geometry from [HITPROBE]) → CLICK dispatched "
      "to GameActivity$1/$2/$4 → 3 rotations → **3 distinct board states** "
      "(cb9ef295be → fd3319ff72 → 0c74b09a8b), deterministic x2.\n"
      "- Evidence: docs/evidence/s79/fishrings/board_state_{1,2,3}*.jpg; "
      "run/s79_reproofs/fishrings_r400{,_run2}\n"
      "- Ladder item 'tap-based rotation interaction at HEAD' = DONE. The remaining open "
      "item (catch-the-fish loop to game end / win condition) stays honestly OPEN."),
 20: ("**S79 EXECUTION CHECKPOINT — honest status unchanged**\n\n"
      "- Lobby renders (splash → lobby 205,638 px family) at HEAD; click-test finds 0 "
      "clickable views in the lobby tree (cards bind listeners at runtime deeper in).\n"
      "- R-NEW-388 (31 card ImageViews at (0,0) — RelativeLayout anchor geometry law) + "
      "the OBJECT-IDENTITY family remain the pinned blockers. Deep runtime work, not "
      "re-faked. OPEN."),
 21: ("**S79 EXECUTION CHECKPOINT — current-HEAD re-proof**\n\n"
      "- Real click-test run x2 at the S79 binary: 12 views probed / 10 changed; menu "
      "renders ('Vector Pinball 1.16.0'); distinct UI states with distinct frame SHAs "
      "(L6 family intact).\n"
      "- Honest: still NOT L7 — the multi-round game-loop proof remains OPEN. No claim inflation."),
 22: ("**S79 EXECUTION CHECKPOINT — honest status unchanged (by-design)**\n\n"
      "- aapt2 badging at HEAD still shows launchable=[] — the app IS a Tile/service app; "
      "no Activity for the execution ladder to climb. The engine is correct; the gap is "
      "the F-143 service-launch family (startService/TileService lifecycle), which stays "
      "OPEN as a runtime capability, not an app failure."),
 23: ("**S79 EXECUTION CHECKPOINT — current-HEAD re-proof**\n\n"
      "- Real click-test run x2 at the S79 binary: 6/6 probed views changed state; the "
      "app's REAL AlertDialog opens; game text renders (\"It is currently black's turn.\").\n"
      "- In-game interaction loop remains blocked by the app-own IOOBE stopper "
      "(ArrayIndexOutOfBounds inside the app's own game logic) — honestly OPEN; not "
      "engine-shaped, not faked."),
}

for n, body in COMMENTS.items():
    api(f"/issues/{n}/comments", "POST", {"body": body})
    print(f"commented #{n}")
    if n in (15, 17, 18):
        api(f"/issues/{n}", "PATCH", {"state": "closed",
                                      "state_reason": "completed"})
        print(f"closed   #{n}")
print("issue sync complete")
