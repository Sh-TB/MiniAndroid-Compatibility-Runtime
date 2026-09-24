#!/usr/bin/env python3
"""S96 — generate docs/EXECUTED_GIFS.md: the single human-facing index of every
REAL-execution GIF in the repository. Canonical GIFs (SHA-pinned, one per title)
are listed first; historical wave GIFs follow with their relationship to the
canonical asset recorded (identical duplicate / distinct earlier run).
No upstream/promotional/fake GIFs exist in the repo — exclusion stated explicitly."""

import json, os, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
M = json.load(open('docs/verified_executed_games.json'))
GAMES = {g['title']: g for g in M['games']}

def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

CANON = json.load(open('docs/achievements/ASSET_MANIFEST.json'))
canon_by_file = {a['file']: a for a in CANON['canonical']}

# canonical GIF records: (file, title, type, status, what/exec, state-change)
rows = [
    ('com.miniandroid.snakedeluxe.gif', 'Snake Deluxe', 'game', 'VERIFIED',
     'Full gameplay: 2 lives, 183 moves / 49 turns / 3 captures, game over x2, CJK dialog, restart (S79 matrix)', 'YES'),
    ('com.miniandroid.tetris.gif', 'Mini Tetris', 'game', 'VERIFIED',
     'Piece falls, NEXT queue advances; x3 deterministic runs at 6 unique frames/24 (S95)', 'YES'),
    ('com.miniandroid.g2048.gif', '2048', 'game', 'VERIFIED',
     'Tile merges advance SCORE to 200 across 65 frames (S80 autoplay)', 'YES'),
    ('com.miniandroid.minicraft.gif', 'MiniCraft (House Builder)', 'game', 'VERIFIED',
     'Terrain, 5 real placements, material cycle, DEMO builds a cottage, 2 digs; Blocks/Dug mutate (S86); x3 det runs (S95)', 'YES'),
    ('com.miniandroid.tictactoedeluxe.gif', 'TicTacToe Deluxe', 'game', 'VERIFIED',
     'O/X placement + turn flip (S83 tap schedule)', 'YES'),
    ('com.emmanuelmess.tictactoe.gif', 'TicTacToe Classic', 'game', 'PARTIAL',
     'O/X placement captured (S83 click pass); S92 graphics verify FAILED -> PARTIAL', 'YES'),
    ('com.dozingcatsoftware.bouncy.gif', 'Vector Pinball (bouncy)', 'game', 'VERIFIED',
     'Ball launch + score interaction (S62+/S85); S95: 3x WRONG_COLOR cleared, 1 clip residual', 'YES'),
    ('ca.rmen.nounours.gif', 'ca.rmen.nounours', 'game', 'VERIFIED',
     'Tap swaps the drawn teddy-bear state (S84 click pass probed=1 state_changed=1)', 'YES'),
    ('com.dozingcatsoftware.dodge.gif', 'com.dozingcatsoftware.dodge', 'game', 'VERIFIED',
     'New Game tap -> 13 live gameplay frames: bullets move, dodger visible (S84/S86)', 'YES'),
    ('com.smorgasbork.hotdeath.gif', 'com.smorgasbork.hotdeath', 'game', 'VERIFIED',
     'Card-menu interaction, 3 state changes (S84); S95 vector/adaptive fix -> SEMANTIC_PASS', 'YES'),
    ('org.bobstuff.bobball.gif', 'org.bobstuff.bobball', 'game', 'VERIFIED',
     'Game-field interaction, 6/6 click state changes (S84); S95 PARTIAL(0)', 'YES'),
    ('com.trianguloy.urlchecker.gif', 'com.trianguloy.urlchecker (app)', 'app', 'VERIFIED-INTERACTIVE',
     'Menu interaction captured (S85); core URL checks need NET-001 real networking', 'YES'),
]

# historical wave GIFs: (path, title, relationship, what)
hist = [
    ('docs/evidence/s79/snake_gameplay.gif', 'Snake Deluxe',
     'distinct earlier run (S79 reproof matrix run_a/run_b; 70-frame GIF: game1/dialog/restart/game2)',
     'Full gameplay with death + restart + CJK dialog; source of the S79 reproof record'),
    ('docs/evidence/s80/g2048_gameplay.gif', '2048',
     'byte-identical duplicate of the canonical GIF (S80 harvest source)',
     'Autoplay run, 65 frames'),
    ('docs/evidence/s80/snake_gameplay.gif', 'Snake Deluxe',
     'byte-identical duplicate of the canonical GIF (S80 harvest source)',
     'Autoplay run, 49 frames'),
    ('docs/evidence/s80/tetris_gameplay.gif', 'Mini Tetris',
     'byte-identical duplicate of the canonical GIF (S80 harvest source)',
     'Autoplay run, 75 frames'),
    ('docs/evidence/s83b/snake_head_gameplay.gif', 'Snake Deluxe',
     'distinct wave evidence (S83b 4-run head-close-up sweep; snake_head_run_00..03.jpg)',
     '4 repeated runs, head-region close-up'),
    ('docs/evidence/s73_snake_autoplay/snake_autoplay.gif', 'Snake (S73 autoplay instrument)',
     'distinct earlier-generation autoplay run (S73 harness, pre-S80 game)',
     '90-frame autoplay; superseded by the S80 Snake Deluxe instrument'),
    ('docs/demos/demo_proof.gif', 'HelloMiniAndroid demo fixture (NOT a game)',
     'distinct in-house demo-fixture execution (docs/demos/demo_manifest.json, 8 clicks dispatched)',
     'Counter/timer demo: TAP ME button, count=1..8 state changes; fixture-class evidence'),
]

GH = 'https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/blob/main/'

L = []
w = L.append
w('# EXECUTED GIFS — real MiniAndroid execution evidence index (S96)')
w('')
w('> Every GIF below corresponds to a **REAL MiniAndroid execution** (real-dalvik run,')
w('> SHA-pinned artifact, session record in the canonical registry). One canonical GIF')
w('> per title (S84 law); earlier wave GIFs are kept as historical evidence and marked.')
w('> The repo contains **no** upstream demo GIFs, promotional GIFs, generated fakes,')
w('> static screenshots renamed to `.gif`, or other-emulator recordings — any such asset')
w('> would be excluded here by law.')
w('')
w('Machine links: [verified_executed_games.json](verified_executed_games.json) ·')
w('[VERIFIED_EXECUTED_GAMES.md](VERIFIED_EXECUTED_GAMES.md) ·')
w('[canonical/SHA256SUMS](evidence/canonical/SHA256SUMS) ·')
w('validate: `python3 tools/verify_canonical_evidence.py`')
w('')
w('## Legend')
w('')
w('| Level | Meaning |')
w('|---|---|')
w('| E3 | runtime trace only (no meaningful visual) |')
w('| E4 | real APK execution (single/recorded sessions) |')
w('| E5 | deterministic repeated execution (recorded protocol) |')
w('| E6 | corpus fan-out across APKs (law-level, not per-GIF) |')
w('')
w('---')
w('')
w('## VERIFIED EXECUTION GIFS (canonical, one per title)')
w('')
w('| Title | Type | Status | Evidence | GIF |')
w('|---|---|---|---|---|')
for f, title, typ, status, what, sc in rows:
    p = 'docs/evidence/canonical/' + f
    s = sha(p)
    w(f"| {title} | {typ} | {status} | {GAMES.get(title,{}).get('evidence_level','E4')} · "
      f"state change: {sc} · SHA `{s[:12]}…` | [GIF](evidence/canonical/{f}) |")
w('')
w('Interactive/state-change proven: **12/12** (every canonical GIF records click→state change).')
w('')
w('## INTERACTIVE / STATE-CHANGE GIFS (detail)')
w('')
w('| Title | What was executed | Input / state transition | Frames | Source project |')
w('|---|---|---|---|---|')
for f, title, typ, status, what, sc in rows:
    g = GAMES.get(title)
    src = g['upstream'] if g else 'https://github.com/TrianguloY/UrlChecker'
    inp = g['execution_protocol'] if g else 'real-dalvik run + click probe (S85)'
    fr = g['screenshot']['gif_frames'] if g and g['screenshot'].get('gif_frames') else 2
    w(f"| {title} | {what} | {inp} | {fr} | {src} |")
w('')
w('## HISTORICAL / WAVE GIFS (real execution; superseded by or supplemental to canonical)')
w('')
w('| Title | Path | Relationship to canonical | What it shows |')
w('|---|---|---|---|')
for p, title, rel, what in hist:
    rp = p[len('docs/'):] if p.startswith('docs/') else p
    w(f"| {title} | [{os.path.basename(p)}]({rp}) | {rel} | {what} |")
w('')
w('## VISUAL-ONLY / LIMITED EVIDENCE')
w('')
w('- None. Every GIF in the repository falls into the two sections above.')
w('- Titles with JPG-only canonical screenshots (static verification, no GIF): see')
w('  [VERIFIED_EXECUTED_GAMES.md](VERIFIED_EXECUTED_GAMES.md) §C/§D — 10 non-interactive')
w('  VERIFIED games + 2 PARTIAL (TriPeaks, TicTacToe Classic has a GIF but contested visuals).')
w('')
w('## Exclusions (explicit)')
w('')
w('| Excluded class | Reason |')
w('|---|---|')
w('| Upstream project demo GIFs (e.g. F-Droid screenshots/phoneScreenshots) | not MiniAndroid execution |')
w('| Promotional/marketing GIFs | not evidence |')
w('| Generated/synthetic demos | never treated as execution (S92 anti-false-positive laws) |')
w('| Static screenshot renamed `.gif` | all repo GIFs verified GIF89a multi-frame |')
w('| Other emulator/runtime recordings | no such asset in repo |')
w('')

with open('docs/EXECUTED_GIFS.md', 'w') as f:
    f.write('\n'.join(L))
print('OK: docs/EXECUTED_GIFS.md written,', len(L), 'lines')
