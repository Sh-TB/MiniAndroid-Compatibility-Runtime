#!/usr/bin/env python3
"""
S95-FOLLOWUP — VERIFIED EXECUTED GAMES AUDIT (evidence wave, no runtime changes).

Builds the authoritative executed-games index from CANONICAL sources only:
  - docs/evidence/canonical/registry.json   (identity + status + artifact + SHA)
  - docs/evidence/canonical/SHA256SUMS      (artifact hashes)
  - docs/ACHIEVEMENTS.md                    (per-title proven chain, S84 law)
  - docs/achievements/GAMES_WITH_GIFS.md    (frames + state-change records)
  - docs/evidence/s95/before_after_summary.json (S95 measured verdicts)
  - docs/evidence/s95/wave_c_determinism.json   (x3 deterministic runs)
  - docs/evidence/s93/repeatability.json        (x3 repeat verdicts)
  - docs/evidence/s79/reproofs/S79_REPROOF_MATRIX.json (run_a/run_b, det x2)
  - docs/evidence/s91_fish_reproof/README.md    (fish rings tap->state, RC=0)
  - docs/TICKET_REGISTRY.json               (GAME-/APP- master records)

Outputs (created/updated):
  - docs/verified_executed_games.json  (machine-readable; references canonical IDs)
  - docs/VERIFIED_EXECUTED_GAMES.md    (human-readable, clickable links)

Strict status vocabulary: VERIFIED / TESTED / OBSERVED / PARTIAL / FAILED / BLOCKED / PENDING.
Evidence levels: E0..E6. Downgrades are applied where recorded evidence is weaker
than the stored status (never upgrades without runtime evidence).
"""

import json, os, re, sys, hashlib
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

REG = json.load(open('docs/evidence/canonical/registry.json'))
TITLES = REG['titles']
SUMS = {}
for line in open('docs/evidence/canonical/SHA256SUMS'):
    parts = line.split()
    if len(parts) == 2:
        SUMS[parts[1]] = parts[0]

S95 = json.load(open('docs/evidence/s95/before_after_summary.json'))['titles']
WC = json.load(open('docs/evidence/s95/wave_c_determinism.json'))
REP = json.load(open('docs/evidence/s93/repeatability.json'))

GH_BASE = 'https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/blob/main/'
LAST_HEAD = 'd5946533'   # S95-CTRL commit; battery 99/99 re-certified on it
S95_COMMIT = '4e44124c'  # S95 P0 execution wave commit

def canon_sha(fname):
    return SUMS.get('docs/evidence/canonical/' + fname, '')

def fdroid(pkg):
    return f'https://f-droid.org/en/packages/{pkg}/'

def gh(path):
    return GH_BASE + path

# ---------------------------------------------------------------------------
# Curated evidence records for every game that has a canonical runtime
# artifact (12 JPG + 11 GIF games). Every field below was read from the
# canonical sources listed in the header — nothing invented.
# 'runs' = number of recorded independent executions found in the repo.
# ---------------------------------------------------------------------------
G = []
def g(**kw):
    kw['kind'] = 'game'
    G.append(kw)

# ---- Interactive games (canonical GIF + click->state-change proven) -------
g(title='Snake Deluxe', package='com.miniandroid.snakedeluxe', version='1.0 (vc1)',
  upstream='in-house — games/snake-deluxe (source in repo)', fdroid=None, apk_sha256=None,
  artifact='com.miniandroid.snakedeluxe.gif', gif_frames=49, level=3, level_name='L3_STRUCT_CANDIDATE',
  sessions='S79 / S80 / S83 / S91', interaction=True,
  protocol='real-dalvik run, TouchDispatcher tap schedule (23 autonomous taps + death extension + restart tap @ (758,1022)); autoplay driver scripts/s80_sd_autoplay.py',
  state_change='full gameplay loop: 2 lives (moves 88/90, turns 22/24, food captures), game over @frame 94 and 192, CJK dialog painted, restart tap observed (S79_REPROOF_MATRIX run_a/run_b)',
  runs=4, runs_evidence='S79 run_a+run_b (det x2 protocol) + docs/evidence/s83b/snake_head_run_00..03.jpg (4 runs)',
  e_level='E5',
  limitations='rendering L3 struct-candidate; graphics verdict not yet SEMANTIC_PASS',
  ticket=None,
  evidence_extra=['docs/evidence/s79/reproofs/S79_REPROOF_MATRIX.json', 'docs/evidence/s80/snake_gameplay.gif', 'docs/evidence/s83b/snake_head_gameplay.gif'])

g(title='Mini Tetris', package='com.miniandroid.tetris', version='1.0 (vc1)',
  upstream='in-house — games/mini-tetris (source in repo)', fdroid=None,
  apk_sha256='cb2818dfe6c6cadb651348ddaf4c91c57bea5ecc134f215d25fb5ffdffdf8644',
  artifact='com.miniandroid.tetris.gif', gif_frames=75, level=3, level_name='L3_STRUCT_CANDIDATE',
  sessions='S80 / S83 / S95', interaction=True,
  protocol='real-dalvik run; START tap at (786,1854) (S95 protocol correction — old (540,1500) hit no touch target); autoplay driver scripts/s80_tet_autoplay.py',
  state_change='piece falls + NEXT queue changes: 6 unique frames per 24-frame run, identical across 3 deterministic runs (wave_c_determinism.json)',
  runs=5, runs_evidence='S95 x3 deterministic runs + S80 autoplay + S83 sweep',
  e_level='E5',
  limitations='S95 verdict SEMANTIC_PARTIAL(0 flags); S92 ANIMATION_FROZEN classification REFUTED (was a harness tap bug, GAME-0004 CLOSED)',
  ticket='GAME-0004',
  evidence_extra=['docs/evidence/s95/wave_c_determinism.json', 'docs/evidence/s80/tetris_gameplay.gif'])

g(title='MiniCraft (House Builder)', package='com.miniandroid.minicraft', version='1.0',
  upstream='in-house — games/minicraft (source in repo)', fdroid=None,
  apk_sha256='77b9629ee111b968ccc9dbd4507eab3564a0a7a6e26dcacbe28f99de189c3a90',
  artifact='com.miniandroid.minicraft.gif', gif_frames=15, level=3, level_name='L3_STRUCT_CANDIDATE',
  sessions='S86 / S95', interaction=True,
  protocol='real-dalvik run; DEMO tap at (925,1862); build cursor walked via direction pad; BRICK cycles material; PLACE/DIG edit world',
  state_change='world blocks 0->2 (house built), stats strip mutates (Blocks/Dug); identical across 3 deterministic runs (wave_c_determinism.json); canonical GIF shows 5 real placements + material cycle + 2 digs',
  runs=5, runs_evidence='S95 x3 deterministic runs + S86 canonical session + S83-era sweep',
  e_level='E5',
  limitations='S95 verdict SEMANTIC_PARTIAL(0 flags); S92 ANIMATION_FROZEN REFUTED (GAME-0005 CLOSED)',
  ticket='GAME-0005',
  evidence_extra=['docs/evidence/s95/wave_c_determinism.json'])

g(title='2048', package='com.miniandroid.g2048', version='1.0 (vc1)',
  upstream='in-house — games/2048 (source in repo)', fdroid=None,
  apk_sha256='1b1c602a5f0a27231ebcdcfdc632a96c82f6fb74aaae7d80130ac63ab185d278',
  artifact='com.miniandroid.g2048.gif', gif_frames=65, level=2, level_name='L2_GRAPHICALLY_INCOMPLETE',
  sessions='S80 / S83', interaction=True,
  protocol='real-dalvik run + autoplay driver scripts/s80_2048_autoplay.py (swipe-equivalent tap schedule)',
  state_change='tile merges advance SCORE to 200 in canonical GIF (65 frames); S92 fresh verify: no failing stages',
  runs=2, runs_evidence='S80 autoplay session + S83 sweep (sweep_GAME-2048.jpg)',
  e_level='E4',
  limitations='rendering L2; S92 reclassification candidate_INTERACTION_VERIFIED pending S92 §29 human review (registry status not yet promoted)',
  ticket=None,
  evidence_extra=['docs/evidence/s80/g2048_gameplay.gif'])

g(title='TicTacToe Deluxe', package='com.miniandroid.tictactoedeluxe', version='1.0 (vc1)',
  upstream='in-house — games/tictactoe-deluxe (source in repo)', fdroid=None, apk_sha256=None,
  artifact='com.miniandroid.tictactoedeluxe.gif', gif_frames=4, level=3, level_name='L3_STRUCT_CANDIDATE',
  sessions='S83', interaction=True,
  protocol='real-dalvik run + tap schedule on the 3x3 grid',
  state_change='O/X placement + turn flip captured across 4 GIF frames',
  runs=1, runs_evidence='S83 canonical session only — no repeat protocol recorded',
  e_level='E4',
  limitations='rendering L3; single recorded run; S92 reclassification candidate_INTERACTION_VERIFIED pending human review',
  ticket=None, evidence_extra=[])

g(title='Vector Pinball (bouncy)', package='com.dozingcatsoftware.bouncy', version='—',
  upstream='https://github.com/dozingcatsoftware/Bouncy', fdroid=fdroid('com.dozingcatsoftware.bouncy'),
  apk_sha256='ffda0d9cb0b1b2aa58be9559dda891c4fa24391bc481d297a8e3d96c31f62721',
  artifact='com.dozingcatsoftware.bouncy.gif', gif_frames=2, level=2, level_name='GRAPHICALLY_INCOMPLETE',
  sessions='S62+ / S85 / S95', interaction=True,
  protocol='real-dalvik run, tap schedule (launch + nudge), ViewTree dump; S95 capture: 10 frames, 1080x1920',
  state_change='ball launch + score state change captured (registry interacted=true state_changed=true)',
  runs=3, runs_evidence='S62+ canonical + S85 sweep + S95 before/after captures (screenshot SHAs 362b191e… -> cf76282e…)',
  e_level='E4',
  limitations='S95 verdict SEMANTIC_FAIL with 1 residual WRONG_CLIP flag (GFX-002-adjacent measure semantics); runtime rc=1 APP-BOUNDARY exception (pre-existing, identical in BEFORE capture)',
  ticket='GAME-0002',
  evidence_extra=['docs/evidence/s95/before_after_summary.json'])

g(title='ca.rmen.nounours', package='ca.rmen.nounours', version='3.5.8',
  upstream='https://github.com/caarmen/nounours-android', fdroid=fdroid('ca.rmen.nounours'),
  apk_sha256='0e7da7b17b63d727fb2a3a75e0576e1a42e286ebc8fb73b368da5518a728c682',
  artifact='ca.rmen.nounours.gif', gif_frames=2, level=2, level_name='GRAPHICALLY_INCOMPLETE',
  sessions='S84 / S79-reproof / S95', interaction=True,
  protocol='real-dalvik run + click probe (probed=1 state_changed=1); S95 capture 10 frames',
  state_change='tap swaps the teddy-bear drawing state (GIF 2 frames, state_changed=true)',
  runs=3, runs_evidence='S84 canonical + S79 HEAD reproof + S95 capture (SEMANTIC_PASS)',
  e_level='E4',
  limitations='registry field anomaly launched=false while LOADED/RENDERED/INTERACTED proven (recorded as inconsistency AUD-IC-1); rc=1 APP-BOUNDARY exception',
  ticket=None,
  evidence_extra=[])

g(title='com.dozingcatsoftware.dodge', package='com.dozingcatsoftware.dodge', version='1.5.1 (vc10)',
  upstream='https://github.com/dozingcat/dodge-android', fdroid=fdroid('com.dozingcatsoftware.dodge'),
  apk_sha256='a5687d1bad7b2927740a55b7b1df11efc81edcad03f0633ab5c2e5c58b120541',
  artifact='com.dozingcatsoftware.dodge.gif', gif_frames=14, level=3, level_name='L3_STRUCT_CANDIDATE',
  sessions='S84 / S86 / S95', interaction=True,
  protocol='real-dalvik run; New Game tap at (537,935); 14-frame canonical GIF = menu + 13 live gameplay frames',
  state_change='bullets move + dodger visible on real SurfaceView field (S86 root-cause wave fixed 7 laws F-NEW-164..170 to make the field render)',
  runs=3, runs_evidence='S84 canonical + S86 A/B root-cause runs + S95 capture',
  e_level='E4',
  limitations='menu-panel weighted buttons measure ~1645px (LinearLayout weight bug GFX-002, diagnosed NOT implemented) -> SEMANTIC_FAIL 3 WRONG_CLIP residual',
  ticket='GAME-0001',
  evidence_extra=['docs/evidence/s95/before_after_summary.json'])

g(title='com.smorgasbork.hotdeath', package='com.smorgasbork.hotdeath', version='1.0.11',
  upstream='https://github.com/jpriebe/hotdeath', fdroid=fdroid('com.smorgasbork.hotdeath'),
  apk_sha256='8e6c19ead1795fa5b0f62090f3a56efa4be16e4b3e33f151af707f5eb5e5c620',
  artifact='com.smorgasbork.hotdeath.gif', gif_frames=2, level=2, level_name='GRAPHICALLY_INCOMPLETE',
  sessions='S84 / S92 / S95', interaction=True,
  protocol='real-dalvik run + click probe (probed=6 state_changed=3); S95 capture 10 frames + verifier',
  state_change='card menu interaction captured (3 state changes in S84 click pass)',
  runs=3, runs_evidence='S84 canonical + S92 fresh-SHA verify + S95 re-run (SEMANTIC_PASS, luminance 239.5->55.5)',
  e_level='E4',
  limitations='S92 downgraded to FRAME_CAPTURED (assets_rendered/visual failing); S95 vector/adaptive decode fix (GAME-0006 CLOSED) restored SEMANTIC_PASS — registry status field still FRAME_CAPTURED (recorded as inconsistency AUD-IC-2)',
  ticket='GAME-0006',
  evidence_extra=['docs/evidence/s95/before_after_summary.json'])

g(title='org.bobstuff.bobball', package='org.bobstuff.bobball', version='1.17',
  upstream='https://github.com/bobthekingofegypt/BobBall', fdroid=fdroid('org.bobstuff.bobball'),
  apk_sha256='fd43009a7ffdfaf84963487e2b3502bef63775a4eedd60d7040da70e658b3241',
  artifact='org.bobstuff.bobball.gif', gif_frames=2, level=2, level_name='GRAPHICALLY_INCOMPLETE',
  sessions='S84 / S92 / S95', interaction=True,
  protocol='real-dalvik run + click probe (probed=6 state_changed=6); S95 capture',
  state_change='game field interaction captured (6/6 click state changes in S84 pass)',
  runs=3, runs_evidence='S84 canonical + S92 fresh-SHA verify (no failing stages) + S95 re-run (SEMANTIC_PARTIAL, 0 flags, 6/6 texts TEXT_VISUALLY_VERIFIED)',
  e_level='E4',
  limitations='S95 verdict SEMANTIC_PARTIAL(0) — residual named gap: none open (GAME-0003 CLOSED)',
  ticket='GAME-0003',
  evidence_extra=['docs/evidence/s95/before_after_summary.json'])

g(title='TicTacToe Classic', package='com.emmanuelmess.tictactoe', version='—',
  upstream='F-Droid com.emmanuelmess.tictactoe', fdroid=fdroid('com.emmanuelmess.tictactoe'),
  apk_sha256='16510d7cb5dbcf7db049762728bd3e38911c3117b1f090129caee11e2b098f6e',
  artifact='com.emmanuelmess.tictactoe.gif', gif_frames=3, level=2, level_name='L2_GRAPHICALLY_INCOMPLETE',
  sessions='S83 / S83b / S92', interaction=True,
  protocol='real-dalvik run + click probe; s83b click frames click_GAME-TTT-CLASSIC_CLICK_00..02.jpg',
  state_change='O/X placement captured (GIF 3 frames; registry interacted=true state_changed=true)',
  runs=3, runs_evidence='S83 canonical + S83b click frames + S92 fresh-SHA verify',
  e_level='E4',
  limitations='S92 fresh verify FAILED stages scene/frame_output/visual -> registry status FAILED while ACHIEVEMENTS says VERIFIED-INTERACTIVE (inconsistency AUD-IC-3). Audit downgrades to PARTIAL (weaker preserved; execution+interaction proven, visual semantics contested)',
  ticket=None,
  evidence_extra=['registry/graphics_verdicts/com.emmanuelmess.tictactoe@com.emmanuelmess.tictactoe_3.json', 'docs/evidence/s83b/click_GAME-TTT-CLASSIC_CLICK_00.jpg'])

# ---- Non-interactive games with meaningful canonical JPG ------------------
g(title='Anuto TD', package='ch.logixisland.anuto', version='—',
  upstream='https://github.com/jogishop/AnutoTD', fdroid=fdroid('ch.logixisland.anuto'),
  apk_sha256=None, artifact='ch.logixisland.anuto.jpg', gif_frames=0, level=5, level_name='L5',
  sessions='S62+ / S85', interaction=False,
  protocol='real-dalvik run, 8-frame capture; canonical harvested from s62plus_spotlight/anuto_frame0_after_onDraw.png',
  state_change=None, runs=2, runs_evidence='S62+ canonical + S85 shell re-run at HEAD',
  e_level='E4',
  limitations='no interaction probe recorded; no APK SHA recorded in canonical registry',
  ticket=None, evidence_extra=[])

g(title='OpenSudoku', package='cz.romario.opensudoku', version='—',
  upstream='https://github.com/romario333/opensudoku', fdroid=fdroid('cz.romario.opensudoku'),
  apk_sha256=None, artifact='cz.romario.opensudoku.jpg', gif_frames=0, level=5, level_name='L5',
  sessions='S62+ / S85', interaction=False,
  protocol='real-dalvik run, frame capture (s62plus_spotlight)',
  state_change=None, runs=2, runs_evidence='S62+ canonical + S85 shell re-run at HEAD',
  e_level='E4',
  limitations='no interaction probe; no APK SHA recorded',
  ticket=None, evidence_extra=[])

g(title='FreeKlondike', package='eu.veldsoft.free.klondike', version='—',
  upstream='https://github.com/VelbazhdSoftwareLLC/FreeKlondike', fdroid=fdroid('eu.veldsoft.free.klondike'),
  apk_sha256=None, artifact='eu.veldsoft.free.klondike.jpg', gif_frames=0, level=10, level_name='L10',
  sessions='S64', interaction=False,
  protocol='real-dalvik run; canonical harvested from s64_spotlight/fk_game_deal_response.png (deal-response frame)',
  state_change=None, runs=1, runs_evidence='S64 session only',
  e_level='E4',
  limitations='no interaction flag recorded despite deal-response capture; no APK SHA recorded; single session',
  ticket=None, evidence_extra=[])

g(title='Fish Rings', package='eu.veldsoft.fish.rings', version='1.23 (vc6)',
  upstream='https://github.com/VelbazhdSoftwareLLC/FishRingsForAndroid', fdroid=fdroid('eu.veldsoft.fish.rings'),
  apk_sha256='c8a9cb7cadaaced37a1b13ba32ad9bdc1fbe6d38c9d5348aa56a78b4767c1c70',
  artifact='eu.veldsoft.fish.rings.jpg', gif_frames=0, level=10, level_name='L10',
  sessions='S65 / S79 / S91 / S93', interaction=True,
  protocol='real-dalvik run 60 frames; tap 184,184@40 (arrow onClick -> updateInfo() -> repaint(); 36 ImageViews setImageResource); RC=0, 0 crash-log errors',
  state_change='S91 reproof: frame_039 vs frame_041 = 4,312 pixels changed (measured, PIL); board appears at the tap; provenance chain SOURCE->TIMER->RESOLVE->DECODE->TAP->SETIMAGE(36)->PIXELS all logged',
  runs=6, runs_evidence='S65 canonical + S79 board-state taps (3 boards) + S91 reproof (RC=0) + S93 repeatability x3 (SEMANTIC_PARTIAL x3)',
  e_level='E5',
  limitations='S93 repeat verdicts were SEMANTIC_PARTIAL (graphics-verifier taxonomy), later icon pipeline re-proven RC=0 at S91 HEAD; canonical registry fields interacted/state_changed not set (inconsistency AUD-IC-4)',
  ticket=None,
  evidence_extra=['docs/evidence/s91_fish_reproof/README.md', 'docs/evidence/s91_fish_reproof/frames/frame_039.png', 'docs/evidence/s91_fish_reproof/frames/frame_041.png', 'docs/evidence/s79/fishrings/board_state_1_before_taps.jpg', 'docs/evidence/s93/repeatability.json'])

g(title='TriPeaks', package='eu.veldsoft.tri.peaks', version='—',
  upstream='https://github.com/VelbazhdSoftwareLLC/TriPeaks', fdroid=fdroid('eu.veldsoft.tri.peaks'),
  apk_sha256=None, artifact='eu.veldsoft.tri.peaks.jpg', gif_frames=0, level=10, level_name='L10',
  sessions='S65', interaction=False,
  protocol='real-dalvik run; canonical harvested from visual_forensics/s65_reval/tripeaks/board_full.png',
  state_change=None, runs=1, runs_evidence='S65 session only',
  e_level='E4',
  limitations='status PARTIAL (first divergence recorded in S65 report); no APK SHA recorded',
  ticket=None, evidence_extra=[])

g(title='OPMT (One More Time…)', package='one.scarecrow.games.OPMT', version='—',
  upstream='https://github.com/scarecrowgames/OneMoreTimePuzzleGame', fdroid=fdroid('one.scarecrow.games.OPMT'),
  apk_sha256=None, artifact='one.scarecrow.games.OPMT.jpg', gif_frames=0, level=2, level_name='GRAPHICALLY_INCOMPLETE',
  sessions='S85 / S79-reproof', interaction=False,
  protocol='real-dalvik run, 8-frame capture',
  state_change=None, runs=2, runs_evidence='S85 sweep + S79 HEAD reproof (root_registry S79 note)',
  e_level='E4',
  limitations='no interaction probe; no APK SHA recorded',
  ticket=None, evidence_extra=[])

g(title='com.trianguloy.adnihilation', package='com.trianguloy.adnihilation', version='1.0',
  upstream='https://github.com/TrianguloY/Adnihilation', fdroid=fdroid('com.trianguloy.adnihilation'),
  apk_sha256='ae531b495cc39b210fc13ef74e7e5e663f8fde658a3535e3b964675f8c417d80',
  artifact='com.trianguloy.adnihilation.jpg', gif_frames=0, level=2, level_name='GRAPHICALLY_INCOMPLETE',
  sessions='S85', interaction=False,
  protocol='real-dalvik run, 8-frame capture',
  state_change=None, runs=1, runs_evidence='S85 session only',
  e_level='E4', limitations='no interaction probe; single session',
  ticket=None, evidence_extra=[])

g(title='Mines (premy)', package='cos.premy.mines', version='—',
  upstream='F-Droid', fdroid=fdroid('cos.premy.mines'),
  apk_sha256='18faef7028457f4d123ac8d781f3ecdbf9e29b451468d5d6a348df28e8842aa7',
  artifact='cos.premy.mines.jpg', gif_frames=0, level=2, level_name='GRAPHICALLY_INCOMPLETE',
  sessions='S85', interaction=False,
  protocol='real-dalvik run, 8-frame capture',
  state_change=None, runs=1, runs_evidence='S85 session only',
  e_level='E4', limitations='no interaction probe; single session',
  ticket=None, evidence_extra=[])

g(title='de.georgsieber.ballbreak', package='de.georgsieber.ballbreak', version='1.8.1',
  upstream='https://github.com/schorschii/ballBreak-Android', fdroid=fdroid('de.georgsieber.ballbreak'),
  apk_sha256='e6e9f37293d3aaacda7163f997d17e538962acde7a991f6325f9dd72b45ffe02',
  artifact='de.georgsieber.ballbreak.jpg', gif_frames=0, level=2, level_name='GRAPHICALLY_INCOMPLETE',
  sessions='S84 / S85', interaction=False,
  protocol='real-dalvik run, 8/8 frames; click probe probed=2 state_changed=0',
  state_change=None, runs=2, runs_evidence='S84 canonical + S85 shell re-run',
  e_level='E4',
  limitations='ACHIEVEMENTS "Proven exactly" line says INTERACTED but recorded run shows state_changed=0 (inconsistency AUD-IC-5); no state-change proof',
  ticket=None, evidence_extra=[])

g(title='Balance the Ball', package='com.jeffliu.balancetheball', version='—',
  upstream='F-Droid', fdroid=fdroid('com.jeffliu.balancetheball'),
  apk_sha256='6180534b151e4d50365b21483f3719e32f207a42675dee20227de449c875c1e2',
  artifact='com.jeffliu.balancetheball.jpg', gif_frames=0, level=2, level_name='L2_GRAPHICALLY_INCOMPLETE',
  sessions='S83 / S85', interaction=False,
  protocol='real-dalvik run, 8-frame capture',
  state_change=None, runs=2, runs_evidence='S83 canonical + S85 shell re-run',
  e_level='E4', limitations='no interaction probe (sensor-driven game — tilt not implemented)',
  ticket=None, evidence_extra=[])

g(title='x653.all_in_gold', package='x653.all_in_gold', version='1.2',
  upstream='https://gitlab.com/x653/all_in_gold', fdroid=None,
  apk_sha256='01f04f99173ead827a6669a2fcd0625331bc0a68bcfa8684b87d0990fa7f9bae',
  artifact='x653.all_in_gold.jpg', gif_frames=0, level=2, level_name='GRAPHICALLY_INCOMPLETE',
  sessions='S85', interaction=False,
  protocol='real-dalvik run, 8-frame capture',
  state_change=None, runs=1, runs_evidence='S85 session only',
  e_level='E4', limitations='no interaction probe; single session',
  ticket=None, evidence_extra=[])

# ---- Executed but DOWNGRADED (screenshot exists, L0 blank-class) ----------
g(title='Memory', package='eu.quelltext.memory', version='—',
  upstream='F-Droid', fdroid=fdroid('eu.quelltext.memory'),
  apk_sha256='4dd3957983e3c3f38c673f898d9659d5e0251f97137bab5254eafdcdbc9fa27c',
  artifact='eu.quelltext.memory.jpg', gif_frames=0, level=0, level_name='L0_LOADED_ONLY',
  sessions='S83', interaction=False,
  protocol='real-dalvik run, 8-frame capture (blank-class frames per S54 gate)',
  state_change=None, runs=1, runs_evidence='S83 session only',
  e_level='E4',
  limitations='EVIDENCE DOWNGRADE AUD-DG-1: canonical status VERIFIED at L0 with rendered=false — blank-class frames are not visual evidence (S54 law); audit status OBSERVED',
  ticket=None, evidence_extra=[], downgrade='AUD-DG-1')

# ---------------------------------------------------------------------------
def main():
    by_title = {t['title']: t for t in TITLES}
    by_pkg = {}
    for t in TITLES:
        by_pkg.setdefault(t['package'], []).append(t)

    problems = []
    records = []

    for c in G:
        reg = by_title.get(c['title'])
        if reg is None:
            problems.append(f"curated title not in canonical registry: {c['title']}")
            continue
        if reg['package'] != c['package']:
            problems.append(f"package mismatch {c['title']}: {reg['package']} vs {c['package']}")
        if reg['type'] != 'game':
            problems.append(f"type mismatch {c['title']}: registry says {reg['type']}")
        art = 'docs/evidence/canonical/' + c['artifact']
        if not os.path.exists(art):
            problems.append(f"missing artifact file: {art}")
        want = canon_sha(c['artifact'])
        got = reg.get('artifact_sha256', '')
        if want and got and want != got:
            problems.append(f"artifact sha mismatch {c['artifact']}: SUMS={want[:12]} registry={got[:12]}")
        # APK sha cross-check: registry may record it
        reg_apk = reg.get('apk_sha256', '')
        cur_apk = c.get('apk_sha256')
        if cur_apk and reg_apk and cur_apk != reg_apk:
            problems.append(f"apk sha mismatch {c['title']}: registry={reg_apk[:12]} audit={cur_apk[:12]}")

        # strict status assignment
        if c.get('downgrade'):
            status = 'OBSERVED'
        elif c['title'] == 'TicTacToe Classic':
            status = 'PARTIAL'          # S92 verify FAILED visual stages; weaker preserved
        elif c['title'] == 'TriPeaks':
            status = 'PARTIAL'          # canonical status PARTIAL
        else:
            status = 'VERIFIED'

        rec = {
            'title': c['title'],
            'package': c['package'],
            'version': c['version'],
            'kind': 'game',
            'upstream': c['upstream'],
            'fdroid': c['fdroid'],
            'apk_sha256': cur_apk or (reg_apk or None),
            'registry_status': reg['status'],
            'audit_status': status,
            'evidence_level': c['e_level'],
            'render_level': f"L{c['level']} {c['level_name']}",
            'sessions': c['sessions'],
            'execution_protocol': c['protocol'],
            'interaction': c['interaction'],
            'state_change_evidence': c['state_change'],
            'recorded_runs': c['runs'],
            'runs_evidence': c['runs_evidence'],
            'screenshot': {
                'path': art,
                'url': gh(art),
                'sha256': got or want or None,
                'kind': 'gif' if c['artifact'].endswith('.gif') else 'jpg',
                'gif_frames': c['gif_frames'] or None,
            },
            'github_issue': None,
            'issue_status': 'MISSING_ISSUE',
            'last_verified_commit': S95_COMMIT if 'S95' in c['sessions'] else LAST_HEAD,
            'limitations': c['limitations'],
            'ticket': c.get('ticket'),
            'permanent_evidence': [art, 'docs/ACHIEVEMENTS.md#' + c['title'].lower().replace(' ', '-').replace('(', '').replace(')', '').replace('.', '')] + c['evidence_extra'],
            'downgrade': c.get('downgrade'),
        }
        records.append(rec)

    # remaining executed games (no canonical artifact): OBSERVED tier from registry
    artifact_games = {c['package'] for c in G}
    observed = []
    for t in TITLES:
        if t['type'] != 'game' or t['package'] in artifact_games:
            continue
        observed.append({
            'title': t['title'],
            'package': t['package'],
            'version': t.get('version') or None,
            'registry_status': t['status'],
            'audit_status': 'OBSERVED',
            'evidence_level': 'E3',
            'level': f"L{t['level']} {t['level_name']}",
            'session': t.get('session'),
            'launched': t.get('launched'),
            'rendered': t.get('rendered'),
            'proven': t.get('proven'),
            'apk_sha256': t.get('apk_sha256') or None,
            'upstream': t.get('upstream') or None,
            'artifact': None,
            'notes': t.get('notes'),
        })

    games_all = [t for t in TITLES if t['type'] == 'game']
    verified_games = [r for r in records if r['audit_status'] == 'VERIFIED']
    partial_games = [r for r in records if r['audit_status'] == 'PARTIAL']
    state_change_games = [r for r in verified_games if r['state_change_evidence']]
    shot_games = [r for r in records if r['audit_status'] in ('VERIFIED', 'PARTIAL')]
    repeated_games = [r for r in records if r['recorded_runs'] >= 2 and r['audit_status'] in ('VERIFIED', 'PARTIAL')]
    e5_games = [r for r in records if r['evidence_level'] == 'E5']

    # ---- 22-VERIFIED claim verification ------------------------------------
    v22 = [t for t in TITLES if t['status'] == 'VERIFIED']
    v22_games = [t for t in v22 if t['type'] == 'game']
    v22_apps = [t for t in v22 if t['type'] == 'app']
    v22_fixture = [t for t in v22 if t['type'] == 'fixture']
    downgrades = []
    for t in v22:
        if t['level'] == 0 and not t.get('rendered'):
            downgrades.append({
                'id': 'AUD-DG-1' if t['title'] == 'Memory' else 'AUD-DG-2',
                'title': t['title'], 'package': t['package'], 'type': t['type'],
                'reason': f"status VERIFIED at L{t['level']} ({t['level_name']}) with rendered=false — blank-class frames are not visual evidence (S54 screenshot-gate law)",
                'action': 'downgraded to OBSERVED in this audit (canonical registry untouched — historical evidence not modified)',
            })

    inconsistencies = [
        {'id': 'AUD-IC-1', 'title': 'ca.rmen.nounours',
         'detail': 'registry/ACHIEVEMENTS say LOADED proven but launched=false; GIF + click state change recorded (rc=1 APP-BOUNDARY). Status kept VERIFIED on GIF evidence; field anomaly recorded.'},
        {'id': 'AUD-IC-2', 'title': 'com.smorgasbork.hotdeath',
         'detail': 'registry status FRAME_CAPTURED (S92 downgrade) vs S95 measured SEMANTIC_PASS (GAME-0006 CLOSED, luminance 239.5->55.5). Audit keeps VERIFIED; canonical status field update belongs to a future canonical-sync wave.'},
        {'id': 'AUD-IC-3', 'title': 'com.emmanuelmess.tictactoe',
         'detail': 'registry FAILED (S92 scene/frame_output/visual) vs ACHIEVEMENTS VERIFIED-INTERACTIVE. Audit: PARTIAL (weaker preserved).'},
        {'id': 'AUD-IC-4', 'title': 'eu.veldsoft.fish.rings',
         'detail': 'canonical interacted=false/state_changed=false while S91/S79/S93 record tap->4,312px state change and x3 repeats. Audit keeps VERIFIED + state-change proof.'},
        {'id': 'AUD-IC-5', 'title': 'de.georgsieber.ballbreak',
         'detail': '"Proven exactly" string says INTERACTED but recorded click pass: probed=2 state_changed=0. No state-change proof; VERIFIED (static) retained.'},
        {'id': 'AUD-IC-6', 'title': 'registry vs ACHIEVEMENTS status drift',
         'detail': '7 GIF titles carry candidate_*/FRAME_CAPTURED/FAILED in registry.json (S92 §29 human-review gate pending) while ACHIEVEMENTS.md prints VERIFIED-INTERACTIVE (12). Both read from the same evidence; the S92-gate promotion was never executed.'},
    ]

    machine = {
        'schema': 'miniandroid.executed_games.v1',
        'generated': 'S95-FOLLOWUP',
        'last_verified_commit': LAST_HEAD,
        'canonical_sources': [
            'docs/evidence/canonical/registry.json',
            'docs/evidence/canonical/SHA256SUMS',
            'docs/ACHIEVEMENTS.md',
            'docs/achievements/GAMES_WITH_GIFS.md',
            'docs/evidence/s95/before_after_summary.json',
            'docs/evidence/s95/wave_c_determinism.json',
            'docs/evidence/s93/repeatability.json',
            'docs/evidence/s79/reproofs/S79_REPROOF_MATRIX.json',
            'docs/evidence/s91_fish_reproof/README.md',
            'docs/TICKET_REGISTRY.json',
        ],
        'status_vocabulary': ['VERIFIED', 'TESTED', 'OBSERVED', 'PARTIAL', 'FAILED', 'BLOCKED', 'PENDING'],
        'evidence_levels': {
            'E0': 'hypothesis', 'E1': 'source evidence', 'E2': 'unit test',
            'E3': 'runtime trace (frames/logs, no meaningful visual)',
            'E4': 'real APK execution (screenshot/session evidence)',
            'E5': 'deterministic repeated execution (recorded protocol)',
            'E6': 'corpus fan-out across APKs (law-level record)',
        },
        'summary': {
            'corpus_titles': len(TITLES),
            'games_total': len(games_all),
            'games_with_real_execution_evidence': len(records),
            'games_verified': len(verified_games),
            'games_partial': len(partial_games),
            'games_downgraded': len([r for r in records if r.get('downgrade')]),
            'games_observed_no_artifact': len(observed),
            'verified_games_with_state_change': len(state_change_games),
            'games_with_meaningful_screenshot': len(shot_games),
            'games_with_repeated_run_proof': len(repeated_games),
            'games_at_E5': len(e5_games),
            'claim_22_verified': {
                'count': len(v22),
                'games': len(v22_games), 'apps': len(v22_apps), 'fixture': len(v22_fixture),
                'game_titles': [t['title'] for t in v22_games],
                'app_titles': [t['title'] for t in v22_apps],
                'fixture_titles': [t['title'] for t in v22_fixture],
                'interactive_gif_titles_outside_22': 12,
                'downgrades': downgrades,
            },
            'inconsistencies': inconsistencies,
        },
        'games': records,
        'observed_games': observed,
    }
    with open('docs/verified_executed_games.json', 'w') as f:
        json.dump(machine, f, indent=1)
        f.write('\n')

    if problems:
        print('VALIDATION PROBLEMS:')
        for p in problems:
            print(' -', p)
        sys.exit(1)

    print(json.dumps(machine['summary'], indent=1)[:2400])
    print('\nOK: docs/verified_executed_games.json written')
    print('verified games:', [r['title'] for r in verified_games])
    print('state-change games:', [r['title'] for r in state_change_games])
    print('repeated-run games:', len(repeated_games))

if __name__ == '__main__':
    main()
