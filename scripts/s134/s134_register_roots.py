#!/usr/bin/env python3
"""S134 root registration + registry updates (idempotent, evidence-linked).
Registers F-NEW-160 (DEX field identity law, ROOT-CAUSED-FIXED) and the
honestly-open downstream roots F-NEW-161/162/163 discovered by the FAST path.
"""
import json, hashlib
from pathlib import Path

BASE = Path('/home/z/my-project')
RR = BASE / 'canonical/root_cause_registry.json'

def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16] if Path(p).exists() else 'none'

rr = json.loads(RR.read_text())
roots = rr['roots']
ids = {r.get('id') for r in roots}

def root(rid, title, status, priority, layer=None, extra=None):
    if rid in ids:
        for r in roots:
            if r.get('id') == rid:
                r['title'] = title
                r['status'] = status
                r['priority'] = priority
                if layer: r['layer'] = layer
                if extra: r.update(extra)
        return
    rec = {'id': rid, 'title': title, 'status': status, 'priority': priority}
    if layer: rec['layer'] = layer
    if extra: rec.update(extra)
    roots.append(rec)
    ids.add(rid)

# ── F-NEW-160: DEX instance-field identity law (ROOT-CAUSED-FIXED) ──────
root('F-NEW-160',
     'DEX INSTANCE FIELD IDENTITY LAW: heap instance fields were keyed by '
     'BARE NAME only — two same-named fields of two different classes aliased '
     'ONE storage slot. Faces: (1) solitaire_71 e.m (AppCompat delegate field, '
     'support/v7/app/e) collided with classes.c.m (app Handler field, b/b#30) '
     '→ the Handler answered as the delegate → g.a(Activity,f) invoked on a '
     'Handler → Window null → support/v7/app/h.<init> pc=11 "Window.getCallback '
     'on null receiver" NPE → APP-BOUNDARY unwind → blank two-color screen; '
     '(2) R-NEW-414 initializer scan matched by NAME across the superclass '
     'chain and materialized an unrelated class\'s `new T` initializer '
     '(classes.c m=new b.b()) for the undeclared e.m; (3) simplestopwatch_26 '
     'StopWatch.options (read ref class) vs ShowTime.options (write ref class) '
     '— ONE logical field, two ref classes — split by the naive qualified key '
     'and regressed to null prefs until the ART declarer-resolution walk was '
     'added. FIX (S134): qualified key "Lcls;->name" for DEX-defined declaring '
     'classes (framework-owned classes keep bare keys for C++ shadow interop); '
     'ART law resolved_field_declarer() walks the superclass chain to the '
     'actual declarer; field reads of never-written fields answer the declared '
     'DEFAULT (zero/null) — never another class\'s slot; DEX writes dual-write '
     '(qualified primary + bare legacy mirror).',
     'ROOT-CAUSED-FIXED', 'P0', 'dex/vm',
     extra={
         'evidence': 'run/s134/fast/ (FAST A/B before/after), '
                     'run/s134/sol_v12.log ([S134-QGET] qualified-key probes), '
                     'run/s134/sol_v13.log ([S134-GCB] getCallback answered, '
                     'delegate constructed, AppCompat theme machinery ran), '
                     '3-run solitaire 6588621c4a0c4182 x3 (new frontier state), '
                     'simplestopwatch e00fe7e082c385f8 x3 with isolated '
                     '--data-root (regression caught by FAST suite and fixed '
                     'in-wave by the declarer law)',
         'regression': 'laws130 51/51 PASS; dooz ba8a95eb2278594f + ballbreak '
                       '8a951f5f975c4742 BYTE-IDENTICAL to HEAD A/B '
                       '(git worktree fbc0291 rebuild); webfix T02 golden '
                       'c95affdefb734ffd x3; T01-T14 suite all render; '
                       'S114 HTML5 fixture APKs missing from reset workspace '
                       '(environment gap, honest BLOCKED re-run pending)',
         'fix': 'miniandroid/src/dex/dalvik_engine.cpp s134_dex_field_key + '
                'DalvikExecutionEngine::resolved_field_declarer + qualified '
                'reads in execute_iget/execute_iget_object + dual writes in '
                'execute_iput/execute_iput_object + declaring-class-restricted '
                'R-NEW-414 initializer scan',
         'first_divergence': 'iget-object e.m answered classes.c.m Handler '
                             '(name-aliased slot) instead of the honest null',
         'upstream': 'ART/ART field resolution (ResolveField with hierarchy '
                     'walk); JLS field shadowing across superclass hierarchy',
     })

# ── F-NEW-161: chessclock Uri.toString null (OBSERVED, next wave) ────────
root('F-NEW-161',
     'chessclock_29: NPE "Uri.toString on null receiver" at ChessClock.setUpGame '
     'pc=321 → APP-BOUNDARY unwind. getIntPref chain works (prefs shadow OK); '
     'the null Uri producer (RingtoneManager.getDefaultUri family or '
     'Uri.parse(pref)) is not yet attributed — disassembler tooling cannot '
     'disassemble the 300+ instruction method (dex_method_dump.py buffer '
     'mismatch). STATUS: OBSERVED-FAIL, first-divergence producer pending '
     'per-instruction proof.',
     'OBSERVED-FAIL', 'P1', 'dex/api',
     extra={'evidence': 'run/s134/fast/chessclock_29/ (FAST fingerprint: '
                        'STATE_NONBLANK 3 colors, rc=1), /tmp/s134_cc.log '
                        '(verbose trace to getIntPref boundary)'})

# ── F-NEW-162: C013 inline placeholder contamination + false SUCCESS ─────
root('F-NEW-162',
     'C013-CUSTOMVIEW inline placeholder contaminates visible frames and can '
     'stand in for unimplemented renderer families: (a) headingcalc_1 — '
     'pink "custom view (not rendered)" boxes overpaint REAL heading text '
     '(Heading custom views extend a text base and must route to the base '
     'draw semantics per S134 §16, not a placeholder); (b) simplestopwatch_26 '
     '— BigTextView placeholder label in the live frame; (c) boxcars_libgdx '
     '(EbitenSurfaceView, GL/SurfaceView family) — the FULL-SCREEN frame IS '
     'the inline placeholder while the run reports Status: SUCCESS Errors: 0 '
     '(§30 gate violation: placeholder + nonblank framebuffer classified as '
     'success instead of the honest NATIVE/JS-ENGINE-DEPENDENCY failure). '
     'LAW NEEDED: unknown custom views extending known bases route to base '
     'semantics with live state; SurfaceView/GLSurfaceView subclasses route '
     'to the surface pipeline; placeholders never overwrite real pixels and '
     'never produce SUCCESS.',
     'OBSERVED-FAIL', 'P1', 'renderer/framework',
     extra={'evidence': 'run/s134/fast/headingcalc_1/screenshot.png (visible '
                        'overpaint), run/s134/fast/boxcars_libgdx/run.log '
                        '(C013 placeholder + SUCCESS + EXP092-COPY nonwhite '
                        'claims), run/s134/fast/simplestopwatch_26',
            'writer_classification': 'C013 inline placeholder = DIAGNOSTIC '
                                     'writer currently reaching AUTHORITATIVE '
                                     'frames (§19 violation)'})

# ── F-NEW-156/157 status updates ─────────────────────────────────────────
for r in roots:
    if r.get('id') == 'F-NEW-156':
        r['status'] = 'PARTIAL'
        r['title'] = (r['title'] + ' | S134 UPDATE: solitaire_71 face '
                      'ROOT-CAUSED-FIXED via F-NEW-160 (field identity law) — '
                      'delegate constructs, AppCompat theme machinery runs, app '
                      'reaches onStart (3-run 6588621c4a0c4182); NEXT faces: '
                      'support-v7 i.<init> Window-callback wrapper IAE family, '
                      'SharedPreferences.getBoolean null at c/m.aR, '
                      'FragmentManager "No activity" at v4/b/r.a from m.onStart '
                      '(downstream of the F-NEW-160 frontier). chessclock face '
                      '→ F-NEW-161; simplestopwatch+headingcalc faces render '
                      '(residual C013 contamination → F-NEW-162).')
    if r.get('id') == 'F-NEW-157':
        r['title'] = (r['title'] + ' | S134 UPDATE: boxcars (libGDX-class '
                      'Ebiten engine via gomobile) measured — run completes '
                      'rc=0 Errors=0 but the frame is the C013 placeholder '
                      '(TRUE_EMPTY 3 colors 99.81%): the honest classification '
                      'is native/Go-engine dependency missing; root continues '
                      'via F-NEW-162 (placeholder/false-SUCCESS law) and the '
                      'GL/EGL chain (F-144).')

rr['generated'] = 'S134'
rr['total'] = len(roots)
from collections import Counter
rr['status_counts'] = dict(Counter(r.get('status') for r in roots))
RR.write_text(json.dumps(rr, indent=1, ensure_ascii=False))
print('registry updated: total roots =', len(roots))
print('F-NEW-160..162 registered; F-NEW-156 -> PARTIAL; F-NEW-157 annotated')
