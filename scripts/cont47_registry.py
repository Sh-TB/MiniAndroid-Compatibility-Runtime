#!/usr/bin/env python3
"""cont47_registry.py — CONT-47 registry updates (canonical, no duplicate IDs).

The S83 else-chain leak family: the F-NEW-261 support-family fall-through
(`if (f261_dex_body && f261_support_family) {} else if (onCreate)`) only ever
governed the onCreate arm — the lifecycle-void, setContentView and findViewById
arms were INDEPENDENT ifs that fired even when the fall-through condition held.
Three downstream laws completed the BMI content chain:
  F-NEW-310: setContentView arm gated by the negated fall-through predicate —
             the real AppCompatDelegateImpl.setContentView DEX runs, the app
             layout root lands under the sub-decor's ContentFrameLayout.
  F-NEW-311: lifecycle-void arm gated the same way — the real
             FragmentActivity.onStart/onResume DEX (the fragment-state driver:
             dispatchActivityCreated/noteStateNotSaved/execPendingActions/
             dispatchStart) executes (was: instructions=0).
  F-NEW-312: EXP-045 dispatchStateChange stub scope corrected from the
             "FragmentManager" substring (over-matched the support
             FragmentManagerImpl — mCurState frozen at 0, no fragment view
             ever created) to the androidx family prefix (its actual loop
             premise: SpecialEffectsController machinery).
  F-NEW-313: LayoutInflater.cloneInContext law — the fragment host's real DEX
             onGetLayoutInflater ends in cloneInContext; with no handler the
             fragment inflater was null, onCreateView dispatched inflate on a
             NULL receiver ([ROOT-059]), the result slot never wrote (the
             F-NEW-262 <unset> signature), Fragment.mView=<unset>, and the
             container addView never ran.

RESULT (binary 387390a00f2de498): BMI (com.zola.bmi v402) reaches
REAL_APP_CONTENT for the first time — screenshot b52252c2de19b03a x3
deterministic, full fragment UI in the window tree (RelativeLayout -> 2x
EditText + 2x Spinner + Button "Calculate BMI" + result TextView, 9.9%
non-background pixels), 0 uncaught. Corpus-wide ZERO DRIFT: 33/33 gate MATCH
(8 canonical anchors + tanana + csw + simplecalc, x3 byte-identical),
sol ba50a4d2 x3 / notes eb5ebd55 x3 / alex c8d69f81 x3 (androidx S83 scope
held), probe battery == records exactly (fcol 140/0, f259 49/0, f259g 84/7,
f266 42/0, fnew302 48/24, fnew298 19/0 KEEP=5, fnew260 13/0, fnew262 19/0),
skill self-test 13/13.
"""
import json

REG = 'root_registry.json'
d = json.load(open(REG))
roots = d['roots']
by_id = {r['id']: r for r in roots}

for nid in ('F-NEW-310', 'F-NEW-311', 'F-NEW-312', 'F-NEW-313'):
    assert nid not in by_id, f'{nid} must be free'
assert 'F-NEW-309' in by_id and len(roots) == 620, 'expected 620 roots at start'

BINARY = '387390a00f2de498'

roots.append({
    'id': 'F-NEW-310',
    'status': 'ROOT-CAUSED-FIXED',
    'title': 'S83 else-chain leak (setContentView arm): the F-NEW-261 support-family '
             'fall-through only governed the onCreate arm; the setContentView arm was an '
             'INDEPENDENT if that fired even when (f261_dex_body && f261_support_family) '
             'held — AppCompatActivity.setContentView was stolen by the ActivityShadow '
             'U007 inflate path, the real AppCompatDelegateImpl.setContentView DEX '
             '(ensureSubDecor -> mSubDecor.findViewById(android.R.id.content) -> '
             'removeAllViews -> mLayoutInflater.inflate(resId, contentParent)) never ran, '
             'and the app layout root was inflated into the shadow\'s standalone tree '
             'instead of under the sub-decor\'s ContentFrameLayout (white content past '
             'the action-bar band).',
    'priority': 'P0',
    'layer': 'dex/engine/s83-dispatch-scope',
    'root_cause': 'S83 gate at try_recursive_invoke (dalvik_engine.cpp ~6817-6962): '
                  '`if (f261_dex_body && f261_support_family) { /* fall through */ } '
                  'else if (method_name == "onCreate") {...}` — the else binds ONLY to '
                  'the onCreate arm. Measured: [S83-DIAG] row (env '
                  'MINIANDROID_S83_DIAG, run/cont47/bmi_diag) shows dispatch of '
                  'Landroid/support/v7/app/AppCompatActivity;.setContentView with '
                  'f261_dex_body=1 f261_support_family=1 idx_has_class=1 AND the '
                  'immediately following [S83-APXACT] U007 shadow row — both branches '
                  'true yet the shadow fired. Static decode (cont46_disasm.py on '
                  'bmi_402): AppCompatActivity.setContentView(I) code_off=0xc3dc0 '
                  'delegates to AppCompatDelegateImpl.setContentView(I) code_off=0xc7664 '
                  'whose body is the exact AOSP chain; the runtime\'s '
                  'LayoutInflaterShadow already implements the AOSP inflate(int,'
                  'ViewGroup) law (attach into caller root, return root).',
    'classification_note': 'Fix = gate the arm\'s own condition with the negated '
                  'fall-through predicate `!(f261_dex_body && f261_support_family)` '
                  '(smallest change; no new shadow logic, no APK knowledge; androidx and '
                  'no-DEX-body dispatches keep the exact pre-fix S83 behavior). The '
                  'lifecycle-void and findViewById arms were LEFT on their independent '
                  'ifs this wave (each needs its own probe + A/B — same discipline as '
                  'the sibling EXP-058 stubs in CONT-46); the lifecycle arm moved to '
                  'F-NEW-311 the moment causal evidence landed.',
    'evidence': 'run/cont47/bmi_diag/run.log (S83-DIAG + S83-APXACT same dispatch); '
                'scripts/cont46_disasm.py bmi_402 decode; run/cont47/bmi_f310 '
                '(delegate chain live: createSubDecor + setContentView inflate rows, '
                'app layout root under ContentFrameLayout in the window tree)',
    'next_wave': 'findViewById arm A/B (deferred, no harm evidence); '
                 'solitaire F-NEW-309 drawer-gravity fix on the now-live delegate path.'
})

roots.append({
    'id': 'F-NEW-311',
    'status': 'ROOT-CAUSED-FIXED',
    'title': 'S83 else-chain leak (lifecycle-void arm, F-NEW-172): the '
             'onStart/onResume/onPause/onStop/onDestroy/onSaveInstanceState/'
             'onBackPressed void intercept fired even when the F-NEW-261 fall-through '
             'condition held — the real FragmentActivity.onStart DEX (the fragment-state '
             'driver: mCreated guard -> dispatchActivityCreated -> noteStateNotSaved -> '
             'execPendingActions -> dispatchStart) never ran; BMIMain.onStart dispatched '
             '"instructions=0" and the committed fragment stayed at CREATED.',
    'priority': 'P0',
    'layer': 'dex/engine/s83-dispatch-scope',
    'root_cause': 'Same structural leak as F-NEW-310 (independent if vs else-chain). '
                  'Measured (run/cont47/bmi_f311 + ft4/ft5 field traces): after '
                  'F-NEW-310, BMIMain.onStart ran 167 real instructions; '
                  'FragmentActivity.mCreated went 0->1 (onStart entered the dispatch '
                  'branch); FragmentController.dispatchActivityCreated read mHost '
                  '(non-null, obj#30) and mHost.mFragmentManager (obj#31, non-null) — '
                  'the chain reached FragmentManagerImpl but mCurState stayed 0: the '
                  'EXP-045 dispatchStateChange stub (F-NEW-312) voided the state driver '
                  'BEFORE the mCurState put. The arm\'s own premise ("onCreate was '
                  'intercepted so the FragmentController fields never initialized") is '
                  'void on the support family since F-NEW-261: onCreate\'s real DEX '
                  'runs and FragmentHostCallback.<init> sets mFragmentManager=obj#31 '
                  '(FIELD-TRACE row 395).',
    'classification_note': 'Fix = gate the lifecycle-void arm with the same negated '
                  'fall-through predicate. Androidx keeps the arm '
                  '(f261_support_family=false -> intercept fires exactly as before); '
                  'notes eb5ebd55 x3 byte-identical through the change (measured).',
    'evidence': 'run/cont47/bmi_f311/run.log (instructions=0 -> 167/79 A/B); '
                'run/cont47/bmi_ft3 (mCreated 0->1); run/cont47/bmi_ft4/ft5 '
                '(dispatchActivityCreated -> mHost -> mFragmentManager chain rows); '
                'run/cont47/bmi_ft6 (mCurState 0->1->2 post-F-NEW-312)',
    'next_wave': 'onPause/onStop/onDestroy real-DEX arms now execute for support apps — '
                 'watch save-state paths (onSaveInstanceState) in future waves.'
})

roots.append({
    'id': 'F-NEW-312',
    'status': 'ROOT-CAUSED-FIXED',
    'title': 'EXP-045 dispatchStateChange stub over-match: the guard matched '
             'class_descriptor.find("FragmentManager") — a substring of the LEGACY '
             'support Landroid/support/v4/app/FragmentManagerImpl; — and refused DEX '
             'dispatch for its dispatchStateChange, the mCurState driver '
             '(dispatchCreate -> dispatchStateChange(1), dispatchActivityCreated -> '
             'dispatchStateChange(2), dispatchStart -> dispatchStateChange(3)). '
             'mCurState stayed 0 forever; moveToState never created fragment views; the '
             'committed fragment stayed CREATED; the container stayed children=0.',
    'priority': 'P0',
    'layer': 'dex/engine/stub-scope',
    'root_cause': 'EXP-045 Phase 3 (Telegram-era androidx corpus): '
                  'androidx FragmentManager.dispatchStateChange loops infinitely on '
                  'getSpecialEffectsControllerFactory (SpecialEffectsController '
                  'machinery). The substring guard over-matched the support machine. '
                  'Measured: MINIANDROID_FIELD_TRACE '
                  'FragmentManagerImpl.mCurState (run/cont47/bmi_ft2) — put 0 at <init>, '
                  'reads at 0, NO put beyond 0 despite the full dispatch chain executing '
                  'with non-null mHost/mFragmentManager (ft4/ft5). Static decode: support '
                  'FragmentManagerImpl.dispatchStateChange(I) code_off=0x6ee94 is a '
                  '17-unit try-catch-guarded move+execPendingActions that terminates; '
                  'bmi_402 contains NO androidx at all (classes.dex scan: '
                  'Landroidx/fragment/app/FragmentManager; absent).',
    'classification_note': 'Fix = scope the guard to the androidx family prefix '
                  '`class_descriptor.rfind("Landroidx/fragment/app/FragmentManager", 0) '
                  '== 0` (its actual corpus). The support machine executes. The sibling '
                  'FragmentStore stub (also EXP-045) has no support-family over-match '
                  '(support-25 has no FragmentStore) and stays.',
    'evidence': 'run/cont47/bmi_ft2 (mCurState frozen at 0 pre-fix); '
                'run/cont47/bmi_ft6 (0->1->2 post-fix + PlaceholderFragment.onCreateView '
                'row landing); scripts/cont46_disasm.py FragmentManagerImpl decode; '
                'bmi_402 classes.dex androidx-absence scan',
    'next_wave': 'audit the remaining EXP-045 substring stubs for family over-match '
                 '(each needs its own probe + A/B).'
})

roots.append({
    'id': 'F-NEW-313',
    'status': 'ROOT-CAUSED-FIXED',
    'title': 'LayoutInflater.cloneInContext had no shadow handler: the fragment host\'s '
             'real DEX FragmentActivity$HostCallbacks.onGetLayoutInflater ends in '
             'cloneInContext; the invoke answered null, Fragment.mLayoutInflater went '
             'null, PlaceholderFragment.onCreateView dispatched '
             'LayoutInflater.inflate(I,ViewGroup,Z) on a NULL receiver ([ROOT-059] '
             'null-recv row), the result slot never wrote (the F-NEW-262 <unset> '
             'signature), Fragment.mView=<unset> (FIELD-TRACE put row), and the '
             'container addView never ran — the fragment view could not materialize '
             'even with the state machine live.',
    'priority': 'P0',
    'layer': 'framework/shadow-layoutinflater',
    'root_cause': 'Measured chain (run/cont47/bmi_ft7): '
                  '[REC-MISS] LayoutInflater.cloneInContext caller=HostCallbacks.'
                  'onGetLayoutInflater -> [ROOT-059] null-recv routed inflate -> '
                  '[REC-MISS] -> put Fragment.mView value=<unset>. AOSP law: '
                  'cloneInContext returns a functional inflater (PhoneLayoutInflater '
                  'returns a new instance of its own class). The runtime\'s inflater '
                  'model is the F-021 shared singleton (LayoutInflater.from() and '
                  'Activity.getLayoutInflater() answer the SAME object); the '
                  'context-clone nuance is not observable in this model, so the '
                  'AOSP-observable contract here is: cloneInContext answers a '
                  'FUNCTIONAL inflater — the shared one.',
    'classification_note': 'Fix = LayoutInflaterShadow gains a cloneInContext branch '
                  'returning the shared F-021 singleton id (3 lines; no fake objects, '
                  'no APK knowledge). setFactory2 REC-MISS rows left as-is (no measured '
                  'harm; the inflater works without the factory hook — proven by the '
                  'delegate sub-decor inflation).',
    'evidence': 'run/cont47/bmi_ft7/run.log (null-recv -> <unset> -> no addView); '
                'run/cont47/bmi_f313 (POST: node=249 RelativeLayout(6) under the '
                'container; Button "Calculate BMI" with text; screenshot '
                'b52252c2de19b03a x3)',
    'next_wave': 'none open — companion law to F-021; A/B covered by the wave battery.'
})

d['roots'] = roots
json.dump(d, open(REG, 'w'), indent=1)
print(f'registry: {620} -> {len(roots)} roots')
print('appended:', [r['id'] for r in roots[-4:]])
