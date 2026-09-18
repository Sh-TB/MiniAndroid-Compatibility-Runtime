#!/usr/bin/env python3
"""S60 registry update: R-NEW-380 closure (F-106 reflection-surface law
family + unmodifiable views + Long.toString radix), R-NEW-381 successor
face registered. No new roadmap, no new branch, no new campaigns.
"""
import json

REG = '/home/z/my-project/root_registry.json'

with open(REG) as f:
    reg = json.load(f)

roots = reg['roots']


def find(rid):
    for x in roots:
        if isinstance(x, dict) and x.get('id') == rid:
            return x
    return None


def next_rnew():
    mx = 0
    for x in roots:
        if isinstance(x, dict) and str(x.get('id', '')).startswith('R-NEW'):
            try:
                mx = max(mx, int(x['id'].split('-')[-1]))
            except ValueError:
                pass
    return f"R-NEW-{mx + 1}"


# 1. R-NEW-380 -> ROOT-CAUSED-FIXED via F-106
r380 = find('R-NEW-380')
if r380:
    r380['status'] = 'ROOT-CAUSED-FIXED'
    r380['priority'] = 'P1'
    r380['fixed'] = ('S60 F-106 (a: Class.getDeclaredConstructor full upstream '
                     'contract + Constructor.getModifiers/getParameterTypes + '
                     'Modifier static bit family + Class.toString token law; '
                     'b: Collections.unmodifiableMap/Set/Collection view law; '
                     'c: Long.toString(J) / Long.toString(J, radix) law)')
    r380['evidence'] = (
        'ROOT CAUSE (DEX ground truth: scripts/s60_r380_forensic.py — Leo;.n '
        'getDeclaredConstructor→getModifiers→isPublic→throw shape; upstream '
        'source tag 1.0.23: GameViewModel is @HiltViewModel with ONE ctor '
        '<init>(SettingsRepository) and NO no-arg ctor). THREE generic gaps, '
        'all the F-086 family (missing handler → typed-zero → wrong branch): '
        '(1) legacy getDeclaredConstructor record lost the referent identity '
        '("Ljava/lang/Class;" instead of Lhb0;) and getModifiers/isPublic had '
        'NO handlers → typed-zero 0 → the NewInstanceFactory "not public" '
        'THROW branch ALWAYS taken (message rendered EMPTY — no Class.toString '
        'law). (2) Collections.unmodifiableMap missing → the Hilt '
        'ViewModelStore-key binding (Lls;.a() → unmodifiableMap({hb0,bm1}) → '
        'new Lwl0;(null)) carried a NULL backing map → Lwl0;.containsKey(hb0) '
        'FALSE (guard TRUE per INSTANCEOF-DIAG) → the provider fell to the '
        'DEFAULT factory chain instead of the app Hilt factory. (3) '
        'Long.toString(J,I) missing → the Compose rememberSaveable key '
        'Long.toString(compositeKeyHash,36) = "" → IAE "Registered key is '
        'empty or blank" (Ldf1;.a, depth 21) — the face exposed after (1)+(2). '
        'POST-FIX (run/s60_r380_post7, --max-seconds 480): ZERO exceptions '
        'before the budget stop; the create chain resolves through the app\'s '
        'OWN Hilt factory (Lk2;.b case-1 SavedStateHandle machinery; Lqs; as '
        'Lxd0; attach OK obj#5385); the GameViewModel instance constructs '
        '(Lq32;.c ViewModel closeable registration + the game-state class '
        'inits from the ctor body); the run reaches the healthy frame loop. '
        'Regressions: semantic 32/32 (six f106 records incl. the '
        'discriminating full-chain + NSM fixtures); dooz v18 healthy '
        '(run/s60_v18_reg, 0 errors, doFrame loop alive); BATTERY GATE ALL '
        'PASS 96 stages. Evidence: docs/evidence/s60_r380/.')
    r380['last_updated'] = 'S60 2026-09-18'
    print('R-NEW-380 -> ROOT-CAUSED-FIXED')

# 2. Register the successor face R-NEW-381 (honest, pinned)
r381_id = next_rnew()
assert r381_id == 'R-NEW-381', r381_id
r381 = {
    'id': 'R-NEW-381',
    'status': 'OBSERVED-FAIL',
    'priority': 'P1',
    'app': 'io.github.yamin8000.dooz_23 (dooz, PRIORITY-1)',
    'discovered': 'S60',
    'last_updated': 'S60 2026-09-18',
    'title': ("Dooz next frontier (post F-106): the composition + Hilt "
              "ViewModel creation run end-to-end with ZERO exceptions and the "
              "frame loop is alive, but the first frame is DARK — the Compose "
              "UI content does not reach pixels (post_f106_screenshot.png "
              "non-black 0.0000, same face as the S59 post2 evidence)"),
    'evidence': ('run/s60_r380_post7/ (post_f106_keylines.log; screenshot '
                 'docs/evidence/s60_r380/post_f106_screenshot.png). The window '
                 'attaches and the Choreographer frame loop runs (the S58 v18 '
                 'healthy-face pattern), MainActivity.onStart/onResume '
                 'dispatched; the gap is INSIDE the Compose draw path — the '
                 'AndroidComposeView/View draw chain does not yet paint the '
                 'Compose tree (draw ops, Canvas dispatch, or the surface '
                 'walk). This is the render-side successor of the creation '
                 'chain, not a regression of F-106.'),
    'next': ('(1) Verify the Compose View reaches the ViewShadow draw pipeline '
             '(draw/onDraw/Canvas dispatch traces for the AndroidComposeView '
             'node). (2) Trace the Compose Owner surface ( setContent → '
             'AndroidComposeView attach → draw). (3) Generic law: the Compose '
             'draw-op to software-canvas bridge. Do NOT reopen R-NEW-380.'),
}
roots.append(r381)
print('registered', r381_id, '(successor face, OBSERVED-FAIL, P1)')

# 3. Summary
reg['summary']['open_frontiers'] = ['R-NEW-381']
reg['summary']['last_updated'] = 'S60 2026-09-18'
reg['summary']['note'] = (
    'S60 ROADMAP-3-CLOSURE: R-NEW-380 ROOT-CAUSED-FIXED (F-106 a/b/c — '
    'reflection-surface law family + unmodifiable views + Long.toString radix; '
    'the dooz v23 ViewModelProvider create chain now resolves through the '
    'app\'s own Hilt factory and the GameViewModel constructs with zero '
    'exceptions). R-NEW-381 registered as the honest successor (the Compose '
    'draw path — first-frame content). No new roadmap/branch/campaign.')

with open(REG, 'w') as f:
    json.dump(reg, f, indent=1)
print('registry saved; open_frontiers =', reg['summary']['open_frontiers'])
