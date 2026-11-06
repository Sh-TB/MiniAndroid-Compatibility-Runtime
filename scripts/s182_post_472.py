#!/usr/bin/env python3
"""s182_post_472.py — post the S182 census addendum (mosaic + 20-title battery
+ closed-115 audit) to the standing census board #472."""
import json
import subprocess
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"

BODY = """## S182 census addendum — all-runs mosaic + 20-title minimal battery + the closed-115 audit (user-directed)

**Mosaic (254 distinct titles, newest face per title, class-banded):**
https://raw.githubusercontent.com/Sh-TB/MiniAndroid-Compatibility-Runtime/main/evidence/s182_mosaic/S182_MOSAIC.png
(short-lived mirror: https://tmpfiles.org/w4A2JU2dIsn2/s182_mosaic.png)

### 1) Battery S182 — 10 tiny games + 10 very simple apps (all NEVER measured before; main 5d7edcdb34b1502c, fresh stores)
`evidence/s182_minimal2/S182_BATTERY.json`

| kind | REAL_APP_CONTENT | faces (px) | PARTIAL roots |
|---|---|---|---|
| games 5/10 | gmdice `3891679d` (182,535), bouncy `dd0c1425` (978,380), uturn `a53523e7` (10,782), pfdicer `31ffa499`, pfsolitaire `88dbb4a7` (58,212) | stacktower3d + emmanuelttt = **libGDX `SharedLibraryLoadRuntimeException`/GdxRuntimeException** (NEW family: native .so loading), awagam = lifecycle NPE storm (Family 2), pfludo = `OnBackPressedDispatcher` NPE, aeropayout = NPE `L1/l;.get` |
| apps 4/10 | librecontactsbackup `e97c6367` (1,214,501 px), wocheneinkauf `eee8d351`, textpad `27f44f46`, peri `8fc63a05` (325,303 px) | quicksettingssound + floatdeck = kotlin-reflect CNFE (Family 1/3), webstack = lifecycle NPE depth 60 (Family 2), notepad = `ActivityMain.loadContent` NPE, dmfstasks = `attachBaseContext` NPE, lrceditor = `SwipeRefreshLayout` NPE |

S181's family map **confirms on 20 fresh titles**; one NEW family added:
**F4 libGDX native-lib loading** (blocks the whole tiny-game class; note bouncy survives it nonfatally and still renders 978K px).

### 2) S180 reshoot (mosaic source) — all 19 standing titles re-shot BYTE-EXACT on main
dooz `a0fae907`, microtimer `bbd350b6`, g2048 `f43face0`, opencalc `63020bc7`, tetris `b818a6a7`, snake_deluxe `5235683f`, snakeneon `9c02d9d6`, ttt `db1d633d`, minicraft `e77a073f`, gmdice `3891679d`, forkgram `c2e07171`, memory `42270417`, klondike `c2cbb759`; unchanged frontiers: tb `43bfdac6` (bg-only, uncaught 3), nc `b5a7a35d` (C7-drift face stable), tusky `31ddd4d5` (NO_ROOT), solitaire `ba50a4d2`, freebloks `b5a7a35d`, tg REAL class / white frontier. Zero gate drift.

### 3) The 115 closed issues — fine audit (`evidence/s182_audit/CLOSED_AUDIT.md`)
User asked: are the 115 closures wrong? **Answer: 0 outright wrongful closures; 72 flagged.**
- **72 = MG micro-goals closed while explicitly "(PARTIAL)"** — component-level closures; by the user's FULL-load bar these are paper-done. Flagged; reopen-policy decision pending with the owner. (Their app/game parents remain open.)
- **7 = 4APP block #421–427 closed as SUPERSEDED re-files** → live canonical set **#494–505, all OPEN**: Material Files #495 ladder is live-interactive (2026-11-05 log, Insets frontiers); NewPipe #496 / Joplin #497 / Element X #498 filed, queued, 0 comments yet.
- **7 = GAMES-1..8** — re-verified byte-exact TODAY (S180 reshoot).
- **18 = early EXP/EXEC milestone proofs** — superseded; their anchors still reproduce REAL today (unote/microtimer/gmdice).
- **3 = GAME compat reports** — bouncy #121 now VALIDATED by S182 (REAL_APP_CONTENT).
- **6 = law-fix waves (S102/F-NEW)**, 1 wave-log meta, #166 pinyin closed-completed (byte-identical CJK render proof).

### 4) Tool bug fixed
F-NEW-376 staged promotion leaves `data/app/.staging` behind → `discover_pkg` could pick `.staging` as the package (hit forkgram + uturn). Dotted dirs now skipped.

**Queue:** L-F4 libGDX `.so` loading law → L1 Insets → L2 lifecycle-NPE root → L3 Compose → C7 NC window-2 bisect → C8 3-way port.
"""

d = subprocess.run(["git", "credential", "fill"],
                   input="protocol=https\nhost=github.com\n\n",
                   capture_output=True, text=True).stdout
tok = [l.split("=", 1)[1] for l in d.splitlines()
       if l.startswith("password=")][0]
req = urllib.request.Request(
    f"https://api.github.com/repos/{REPO}/issues/472/comments",
    data=json.dumps({"body": BODY}).encode(),
    headers={"Authorization": f"token {tok}",
             "Content-Type": "application/json",
             "User-Agent": "s182-post"}, method="POST")
r = json.load(urllib.request.urlopen(req))
print("posted:", r.get("html_url"), r.get("id"))
