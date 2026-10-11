#!/usr/bin/env python3
"""cont46_registry.py — CONT-46 registry updates (canonical, no duplicate IDs).

1. F-NEW-262 re-classified per-manifestation on CURRENT HEAD (8f2f6aab /
   binary 56c04526 PRE, a63bf3b5 POST):
   - manifestation 1 (BMI mHandler): RE-ROOTED (the resurrected EXP-058
     checkNotNull name-gate) + F-058-R fixed at probe + real-APK level.
   - manifestation 2 (solitaire wrapper IAE): SUPERSEDED on the current
     lineage — no longer reproduces; first divergence moved to F-NEW-309.
   - manifestation 3 (notes mFragmentLifecycleRegistry): BLOCKED for
     tracing (masked by the S83 androidx bypass; experimental fall-through
     arm required).
2. F-NEW-260 / F-NEW-261 revalidation evidence appended (probe + runtime
   rows on the rebased tree).
3. F-NEW-309 appended (solitaire DrawerLayout drawer-gravity root,
   CLASSIFIED).
"""
import json, sys

REG = 'root_registry.json'
d = json.load(open(REG))
roots = d['roots']
by_id = {r['id']: r for r in roots}

assert 'F-NEW-309' not in by_id, 'F-NEW-309 must be free'
assert 'F-NEW-262' in by_id and 'F-NEW-260' in by_id and 'F-NEW-261' in by_id

# ── F-NEW-262 re-classification ──────────────────────────────────────────
r262 = by_id['F-NEW-262']
r262['status'] = 'ROOT-CAUSED-FIXED (manifestation 1) / SUPERSEDED (2) / BLOCKED (3)'
r262['cont46_reclassification'] = {
    'head': '8f2f6aab4f0f54e77f6081de03e483b89b198ccd',
    'binary_pre': '56c045260767ac667f65553275768fbef9296f01d5aa877c868545fbd3abfa95',
    'binary_post': 'a63bf3b53ac3c082 (16-prefix)',
    'evidence': 'evidence/cont46/CONT46_RESULT.md',
    'm1_bmi': {
        'verdict': 'RE-ROOTED + FIXED (F-058-R)',
        'first_divergence': (
            'NOT an abstract register/identity loss: the EXP-058-era '
            'stub-only gate (dalvik_engine.cpp ~8797, resurrected by the '
            'cross-campaign recovery import d7427016 after R-NEW-365/S47 '
            'F-058 had removed it) refused DEX dispatch for EVERY '
            '"*Preconditions*" checkNotNull — a name-based, blanket '
            'refusal. The value-returning identity helper answered via '
            'bridge_to_api → ActivityShadow 4-level hierarchy walk '
            '(not_handled → no result-slot write) → the 4-arg '
            'FragmentHostCallback ctor\'s move-result-object read <unset> '
            '→ iput stored <unset> into its final mHandler field '
            '(FIELD-TRACE put-obj row on binary 56c04526) → '
            'mHost.getHandler() null → scheduleCommit posted on a null '
            'receiver → transaction never executed.'),
        'fix': 'F-058-R: the stub removed (restoring the proven S47 '
               'state); F-056 descriptor-aware cycle keys + M3-19 '
               'active-cycle law + MAX_RECURSION_DEPTH remain the '
               'generic protections.',
        'probe': 'fixtures/fnew262_probe CK-1..CK-3: 3/3 FAIL on '
                 '56c04526 → 3/3 PASS on a63bf3b5 (19/19 total).',
        'runtime_effect': 'FIELD-TRACE put-obj FragmentHostCallback.'
                          'mHandler value=<unset> → value=obj#29 '
                          '(the real Handler identity); '
                          'enqueueAction → Handler.post Runnable id=38 '
                          'enqueued+dequeued+invoked → '
                          'ensureExecReady→generateOps→executeOps→'
                          'moveToState all execute (BMI, a63bf3b5).',
        'remaining_frontier': 'BMI content attach: the app layout root 78 '
                              'never attached under the delegate\'s '
                              'id-swapped ContentFrameLayout 163 '
                              '([P0-1-ORDER] first-traversal attach wave '
                              'root=78 attached=0) — the AOSP '
                              'inflate(resId, contentParent) leg of the '
                              'v7 delegate setContentView path; next '
                              'bounded decode.',
    },
    'm2_solitaire': {
        'verdict': 'SUPERSEDED on the current lineage',
        'evidence': 'solitaire on 56c04526: rc=1, 0 uncaught; the '
                    'WindowCallbackWrapper IAE no longer reproduces — '
                    'the S134-GCB getCallback bridge answers non-null '
                    '(act=21 row) and the wrapper wraps successfully. '
                    'The recorded 28-uncaught IAE face predates the '
                    'CONT-42..44 framework laws.',
        'new_first_divergence': 'F-NEW-309 (DrawerLayout.j '
                                '"is not a drawer").',
    },
    'm3_notes': {
        'verdict': 'BLOCKED for tracing (masked)',
        'reason': 'the androidx family stays on the S83 bypass (F-NEW-261 '
                  'measured scope law) — mFragmentLifecycleRegistry init '
                  'chain never executes on current HEAD; classification '
                  'requires the experimental androidx fall-through arm '
                  '(a separate bounded A/B, NOT a ship change). Static '
                  'decode: androidx FragmentActivity.<init> builds '
                  'mFragments via FragmentController.createController '
                  '(shadow-bridge + move-result-object shape) and '
                  'mFragmentLifecycleRegistry via pure-DEX '
                  'new LifecycleRegistry(this) — either shape could '
                  'carry the loss; runtime evidence pending the arm.',
    },
}

# ── F-NEW-260 / F-NEW-261 revalidation evidence ─────────────────────────
r260 = by_id['F-NEW-260']
r260['cont46_revalidation'] = {
    'head': '8f2f6aab (rebased tree)',
    'verdict': 'LIVE INCREMENT — revalidated by probe + runtime',
    'probe': 'fixtures/fnew260_probe: 13/13 PASS on 56c04526 '
             '(public/protected/package/private × static/non-static '
             'members, nested interface, anonymous, top-level, '
             'isMemberClass predicates, framework-token negatives). '
             'Anonymous-class law verified against the OpenJDK 21 host '
             'JVM oracle: getModifiers() answers the InnerClasses '
             'access_flags VERBATIM (0x0 for anonymous) — the engine '
             'matches the law.',
    'runtime': 'BMI BackStackRecord.doAddOp getModifiers gauntlet '
               'executes with the law (Class.getModifiers/isMemberClass/'
               'Modifier.isPublic/isStatic rows on binary a63bf3b5).',
    'implementation': 'dex_parser.cpp:540-600 (InnerClass SYSTEM '
                      'annotation capture) + dalvik_engine.cpp:28351+ '
                      '(getModifiers preference).',
}
r261 = by_id['F-NEW-261']
r261['cont46_revalidation'] = {
    'head': '8f2f6aab (rebased tree)',
    'verdict': 'LIVE INCREMENT — revalidated at runtime',
    'evidence': 'the support-family fall-through is live: BMI '
                'FragmentActivity.onCreate executes REAL DEX on '
                '56c04526/a63bf3b5 (attachHost → '
                'attachController → enqueueAction rows; '
                'FragmentManagerImpl machine executes end-to-end after '
                'F-058-R). androidx family stays bypassed — notes '
                'untested on the fall-through arm this wave (masked).',
}

# ── F-NEW-309 new root ───────────────────────────────────────────────────
roots.append({
    'id': 'F-NEW-309',
    'status': 'CLASSIFIED',
    'title': 'Solitaire (de.tobiasbielefeld.solitaire) v7 delegate content '
             'machine reaches DrawerLayout and dies on the drawer-gravity '
             'check: DrawerLayout.j(View) ("isDrawerView") answered FALSE '
             'for the design AppBarLayout child and threw IAE "View '
             'AppBarLayout@209 is not a drawer" (DrawerLayout.j pc=34, '
             'uncaught, frame = single-color 0x5d80f0 theme background, '
             'ba50a4d28ea62fe7 on 56c04526).',
    'priority': 'P1',
    'layer': 'framework/layout-inflater/layoutparams-gravity',
    'root_cause': (
        'Static decode (solitaire base.apk fdfaf7cad18e4416): '
        'g(View) = checkDrawerViewOrFail reads '
        '(DrawerLayout$g) child.getLayoutParams() then iget g.a:I '
        '(the LayoutParams gravity) and computes '
        'GravityCompat.getAbsoluteGravity(g.a, viewLayoutDirection); '
        'j() throws IAE when no LEFT/RIGHT bit survives. The '
        'engine-materialized DrawerLayout.LayoutParams carries gravity=0 '
        '— the layout_gravity attr of the XML drawer children never '
        'resolved into the LayoutParams during inflation. First '
        'divergence row: [S134-GCB] answered, wrapper wrapped, '
        'DrawerLayout.onMeasure/child-check hit gravity=0.'),
    'classification_note': (
        'This is the CURRENT first divergence of solitaire on the true '
        'lineage — it SUPERSEDES the F-NEW-262 manifestation-2 face '
        '(the wrapper IAE no longer reproduces on the rebased engine). '
        'Generic law family: LayoutParams subclass construction with '
        'custom attrs during XML inflation (layout_gravity / '
        'DrawerLayout_LayoutParams rules).'),
    'next_wave': (
        'Decode the inflater\'s generateLayoutParams/attr resolution for '
        'LayoutParams subclasses (R8-renamed DrawerLayout$g.a field); '
        'A/B with a drawer-layout probe (positive: drawer child passes '
        'g(); negative: non-drawer child still throws); then re-run '
        'solitaire x3.'),
    'evidence': 'evidence/cont46/CONT46_RESULT.md',
})
d['count'] = d.get('count', len(roots)) if isinstance(d.get('count'), int) else len(roots)
d['total_roots'] = len(roots)
if 'total' in d: d['total'] = len(roots)
json.dump(d, open(REG, 'w'), indent=1, ensure_ascii=False)
print('registry updated:', len(roots), 'roots; F-NEW-309 appended; 262/261/260 reclassified')
