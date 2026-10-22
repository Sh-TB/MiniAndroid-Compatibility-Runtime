#!/usr/bin/env python3
"""cont158_games.py — CONT-158 game_registry.json updates for the three
F-NEW-497 crossings + honest re-bases. Idempotent: evidence refs carry the
CONT-158 tag; statuses only move forward."""
import json

P = 'canonical/game_registry.json'
g = json.load(open(P))
by = {x['id']: x for x in g['games']}

# GAME-016 TriPeaks: PARTIAL → OBSERVED (lobby now renders real content)
r = by['GAME-016']
r['status'] = 'OBSERVED'
r['checkpoints']['L5'] = True
r['note'] = ('CONT-158: F-NEW-497 drain-to-deadline crossed the 5s splash Timer — '
             'LobbyActivity renders (face e2a290ab, 130 colors; texts: "Welcome to the '
             'Tri Peaks Solitaire for Android!" + New Game/About Us/Help/Exit). '
             'Pre-fix face b5a7a35d uniform grey-48. Game table still behind taps (S121 HUD ledger remains the play evidence).')
r['evidence_refs'].append('CONT-158 battery (binary b7b193b5+): run/c158/battery/tripeaks — [F497-DRAIN] 1 launch, virtual 5000ms; frame_497_drain texts real lobby UI')

# GAME-015 Fish Rings: VERIFIED stays; the blank-splash era closed
r = by['GAME-015']
r['note'] = ('S121 state change 1860 px/tap, 2x IDENTICAL. CONT-158: F-NEW-497 crossed the '
             '5s splash Timer → GameActivity renders the real Rings board (face a341e3ad, '
             '3310 distinct colors, 100% non-white) — the b5a7a35d uniform-splash face era closed; '
             'assets/banner.html absence confirmed artifact-faithful (APK has no assets/ dir).')
r['evidence_refs'].append('CONT-158 battery: run/c158/battery/fishrings — [F497-DRAIN] 1 launch; game board 3310 colors')

# GAME-014 FreeKlondike (veldsoft_3 artifact): menu now renders
r = by['GAME-014']
r['note'] = (r.get('note', '') + ' CONT-158: F-NEW-497 crossed the 5s splash Timer → '
             'MenuActivity renders (face re-based 31ddd4d5→a77038da, 136 colors; New Game/'
             'View Help/About Game/Check for Updates/Exit). Wall: 8 MATCH + this JUSTIFIED '
             'RE-BASE (REAL_APP_CONTENT advance category).')
r['evidence_refs'].append('CONT-158 anchors: run/c158/anchors/klondike — [F497-DRAIN] 1 launch, virtual 5000ms')

# GAME-088 secuso memory: relaunch note (theme delta, content preserved)
r = by['GAME-088']
r['note'] = (r.get('note', '') + ' CONT-158: F-NEW-497 drain fired the app restart flow '
             '(relaunch MainActivity, root 512); same menu texts; face 807a0cca→6da289aa '
             '(relaunch theme rebind gap = F-NEW-499 CLASSIFIED).')
r['evidence_refs'].append('CONT-158 battery: run/c158/battery/memory')

# GAME-011 tictactoe: honest boundary decode row
r = by['GAME-011']
r['note'] = (r.get('note', '') + ' CONT-158: killer chain classified = F-NEW-498 '
             '(libgdx.so dlopen SIGSEGV inside loader + null Gdx.app NPE at '
             'AndroidLauncher.onCreate; face b5a7a35d uniform grey-48, RelativeLayout children=0).')
r['evidence_refs'].append('CONT-158 battery: run/c158/battery/tictactoe.log')

# GAME-091 dooz v23: frontier unchanged this round, battery evidence refreshed
r = by['GAME-091']
r['note'] = (r.get('note', '') + ' CONT-158: face stable at 31ddd4d5 draw-op boundary '
             '(1947 recorded ops since F-NEW-495; presentation still behind the F084 '
             'throughput wall = F-NEW-481 cohort frontier).')

json.dump(g, open(P, 'w'), ensure_ascii=False, indent=1)
print('game_registry.json updated:', len(g['games']), 'games')
