#!/usr/bin/env python3
"""cont48_registry.py — CONT-48 registry updates (canonical, no duplicate IDs).

CONT-48 = the Dooz white-screen closure wave, executed on the CONT-47 binary
lineage (local == origin == b0b903be; work binary c0f31ade222bdf9a = CONT-47
post-fix 387390a00f2de498 + two env-gated draw-caller diagnostics + F-NEW-315).

  F-NEW-314: the F084 "stall" judgment (CONT-42 standing question: budget vs
             real defect) — MEASURED, not a stall: dooz v23 at 15 s = white
             anchor 31ddd4d5b8e6d18e (4.7M instrs), 60 s = SAME white face,
             120 s = 36.2M instrs, boot composition COMPLETES, real Scaffold
             layout renders (screenshot 6841d52a20e6597e x3 deterministic,
             11.3% non-background). Every F084 row in every run is the
             wall-clock budget tail ("Wall-clock budget reached"), no
             [HALT-LOOP], no [R361-DEEP-REFUSE] at ANY budget — the S51-era
             face is superseded. CLASSIFIED: engine-budget class, not a
             correctness defect; throughput engineering is the follow-up.
  F-NEW-315: res/font ("Fonts in XML", AOSP API 26+) file-backed app fonts
             were never registered — FIX-4 scanned only assets/; Dooz v23
             ships res/UJ.ttf (aapt2-renamed res/font entry) and reported
             FONT_SOURCE font_files=0. FIX: the same extension-only law now
             scans res/ too. Dooz positive: font_files=1 registered=1; the
             negative space is provably unchanged (every other corpus member
             still font_files=0, 33/33 gate MATCH).
  F-NEW-316: Compose ImageVector icon paths render EMPTY — 1721/1721 PATH
             ops in the 120 s op trace have zero contours; the compose
             buildPath site (Lbo;::T, the PathNode->android.graphics.Path
             builder, static callers Led0;::a pc=253 / Lh41;::a pc=8) never
             executes (Led0; has zero runtime mentions, no CLASS_INIT row);
             runtime drawPath caller = Ly3;.g pc=12 (the compose
             AndroidCanvas forwarding arm). CLASSIFIED — needs a deeper
             caller-forensics law (ctx.caller is one frame deep) before any
             dispatch change.
  F-NEW-317: one solid-black 24dp-icon-bounding RECT per icon slot (4 total:
             two top-bar, one bottom-left circle, one bottom-right pill) —
             drawRect(0,0,24,24) under the icon's own translate(849,53)+
             scale(2.625) canvas, color ff000000, recorded BEFORE the two
             empty PATH ops of the same icon; runtime caller = Ly3;.p pc=6.
             CLASSIFIED — same wave discipline as F-NEW-316 (decode first).

RESULT (binary c0f31ade222bdf9a): Dooz v23 is PAST ITS WHITE SCREEN for the
launch page at a 120 s budget — REAL_LAYOUT_CONTENT face 6841d52a20e6597e x3
byte-identical (top app bar + bottom action bar with real Material geometry,
11.3% non-background pixels; face-level defects F-NEW-316/317 recorded).
15 s canonical anchor 31ddd4d5b8e6d18e UNCHANGED x3. Corpus-wide ZERO DRIFT:
33/33 gate MATCH (all anchors x3 byte-identical + csw + simplecalc), BMI
b52252c2de19b03a (REAL_APP_CONTENT held), sol ba50a4d2 x3, notes eb5ebd55 x3,
alex c8d69f81 x3, probe battery == records exactly (fcol 140/0, f259 49/0,
f259g 84/7, f266 42/0, fnew302 48/24, fnew298 19/0 KEEP=5, fnew260 13/0,
fnew262 19/0), skill self-test 13/13.
"""
import json

REG = 'root_registry.json'
d = json.load(open(REG))
roots = d['roots']
by_id = {r['id']: r for r in roots}

for nid in ('F-NEW-314', 'F-NEW-315', 'F-NEW-316', 'F-NEW-317'):
    assert nid not in by_id, f'{nid} must be free'
assert 'F-NEW-313' in by_id and len(roots) == 624, 'expected 624 roots at start'

roots.append({
    'id': 'F-NEW-314',
    'status': 'CLASSIFIED',
    'title': 'Dooz v23 F084 "stall" judged — NOT a stall: boot composition is '
             'budget-bound, not defect-bound. Measured A/B on the same binary: '
             '15 s = 4.7M instrs, white anchor 31ddd4d5b8e6d18e; 60 s = 31ddd4d5 '
             '(same face, more budget consumed); 120 s = 36.2M instrs, composition '
             'COMPLETES and the real Scaffold renders (6841d52a20e6597e x3 '
             'deterministic, 11.3% non-background). Every F084 row at every budget '
             'is the wall-clock tail ("Wall-clock budget reached ... F084-HALT-RETURN '
             '(deferred)"), 0 [HALT-LOOP], 0 [R361-DEEP-REFUSE] — the S51-era face '
             'is superseded by later engine fixes. Follow-up: throughput '
             'engineering (interpreter speed), NOT a dispatch/lifecycle change.',
    'evidence': 'run/cont48/baseline/r1..r3 (15s), run/cont48/budget_t60, '
                'run/cont48/budget_t120 + dooz120_r1..r3 (x3 deterministic), '
                'run/cont48/optrace (CANVAS_OP_TRACE), '
                'run/cont48/budget_t120/screenshot.png (real layout face)',
    'priority': 'P1',
    'layer': 'engine-budget',
})
roots.append({
    'id': 'F-NEW-315',
    'status': 'ROOT-CAUSED-FIXED',
    'title': 'AOSP "Fonts in XML" (API 26+) app fonts under res/font/ were never '
             'registered: the FIX-4 app-font law scanned ONLY assets/, but aapt2 '
             'ships font resources as file-backed res/*.ttf|otf entries (R8 renames '
             'them arbitrarily — dooz v23: res/UJ.ttf) and ResourcesCompat.getFont '
             'surfaces them through the same Typeface family model. Dooz reported '
             'FONT_SOURCE font_files=0 registered=0 despite shipping a font. FIX: '
             'the same extension-only scan (no package/name special-casing, bold '
             'detection unchanged) now covers res/ as well — the negative space '
             '(apps with no .ttf/.otf entries anywhere) is provably unchanged. '
             'POST: dooz font_files=1 registered=1 (positive); all other corpus '
             'members font_files=0 (negative), 33/33 gate MATCH. Honest bound: the '
             'dooz RENDERED face is unchanged (6841d52a x3) — its compose text '
             'chain stops before drawText (no TEXT ops), which is F-NEW-316/317 '
             'adjacent decode, NOT the registration law.',
    'evidence': 'src/runtime/execution_engine.cpp FIX-4 block (assets+res scan); '
                'run/cont48/f315_dooz (FONT_SOURCE font_files=1 registered=1 '
                'first=res/UJ.ttf); run/cont48/reg_* negative rows (font_files=0 '
                'unchanged); binary c0f31ade222bdf9a',
    'priority': 'P2',
    'layer': 'resources',
})
roots.append({
    'id': 'F-NEW-316',
    'title': 'Compose ImageVector icon paths render EMPTY on the 120s dooz face: '
             '1721/1721 PATH ops have zero contours (op trace), so no vector icon '
             'pixel ever lands. Static decode: the compose buildPath site (Lbo;::T, '
             'the PathNode list -> android.graphics.Path builder: rewind/'
             'setFillType/moveTo/lineTo/close chain) has exactly two static '
             'callers (Led0;::a pc=253, Lh41;::a pc=8) and ZERO runtime presence '
             '(no Lbo; mention, no Led0;/Lh41; CLASS_INIT row in the whole 120s '
             'log); runtime drawPath calls all arrive through Ly3;.g pc=12 (the '
             'compose AndroidCanvas forwarding arm) with already-empty paths. '
             'CLASSIFIED: ctx.caller is one frame deep — before any dispatch '
             'change, a deeper caller-forensics diagnostic (stack-PC style, the '
             'THROWABLE-STACK-PC precedent) must pin which compose node drives '
             'the empty-path drawPath, and why the VectorPainter machine '
             '(Led0;) never runs.',
    'evidence': 'run/cont48/optrace/optrace.tsv (1721 empty PATH, colors '
                '4d000000/ff000000 at icon origins, scale 2.625); '
                'scripts/cont48_dooz_draw_scan.py (DEX-wide draw/path caller '
                'census: 13 callers); /tmp/led0_disasm.txt (Led0 = '
                'VectorPainter-shaped, super Lb22;); run/cont48/callertrace2 '
                '(DRAW-CALLER drawPath caller=Ly3;.g pc=12 x1747)',
    'priority': 'P1',
    'layer': 'compose-gfx',
})
roots.append({
    'id': 'F-NEW-317',
    'title': 'One solid-black 24dp-icon-bounding RECT per icon slot on the dooz '
             '120s face (4 slots: two top-bar actions, bottom-left circle button, '
             'bottom-right pill button — the only black pixels in the screenshot): '
             'drawRect(0,0,24,24) recorded under the icon canvas '
             'translate(849,53)+scale(2.625) => device RECT (849,53,912,116), '
             'color ff000000, stroke 0, recorded BEFORE the same icon two empty '
             'PATH ops (F-NEW-316); bottom slots repeat at (43,1790)/(869,1784). '
             'The 63x63 device size = 24dp x 2.625 density (Material icon '
             'viewport). Runtime caller = Ly3;.p pc=6 (the compose AndroidCanvas '
             'drawRect forwarding arm; MINIANDROID_DRAW_CALLER_TRACE diagnostic, '
             'env-gated, screenshot SHA unchanged 6841d52a with it on). '
             'CLASSIFIED with F-NEW-316 — same decode-first discipline.',
    'evidence': 'run/cont48/optrace/optrace.tsv (RECT rows seq 3/60/67 + repeats '
                'at icon origins, in front of the paired PATH rows); '
                'run/cont48/callertrace (DRAW-CALLER drawRect caller=Ly3;.p pc=6 '
                'x1098); run/cont48/budget_t120/screenshot.png (4 black squares '
                'at the same slots); MINIANDROID_DRAW_CALLER_TRACE diagnostic '
                'added to canvas_shadow.cpp drawRect/drawPath handlers',
    'priority': 'P1',
    'layer': 'compose-gfx',
})

d['total'] = len(roots)
json.dump(d, open(REG, 'w'), indent=1, ensure_ascii=False)
print(f'registry {624} -> {len(roots)}')
for r in roots[-4:]:
    print(r['id'], r.get('status', '-'), '-', r['title'][:100])
