#!/usr/bin/env python3
"""S58 registry update: R-NEW-376 closure (F-102), R-NEW-378 cascade (F-103),
R-NEW-352 closure, F-104 law family, R-NEW-379 next frontier. No new campaigns.
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


# 1. R-NEW-376 -> ROOT-CAUSED-FIXED via F-102
r376 = find('R-NEW-376')
if r376:
    r376['status'] = 'ROOT-CAUSED-FIXED'
    r376['priority'] = 'P0'
    r376['fixed'] = 'S58 F-102'
    r376['title'] = ('Dooz ctor-climb: Compose init constructor-invocation chains '
                     'exceeding the 2048-frame budget (v18 Lj/j0; x7 + Lt0/t;/LE0/c; '
                     'x2; v23 Lgz1; x3 + Lbp1; x1) — impossible-in-valid-DEX '
                     'self-delegating face')
    r376['evidence'] = (
        'ROOT CAUSE (F-102, generic): the 3rc invoke path (invoke-*/range) dropped '
        'the call site method PROTO at the try_recursive_invoke boundary (default '
        '"") — the F-023 exact-descriptor overload law could not fire and the arity '
        'heuristic (prefer LARGEST bytecode body) re-selected the CALLING overload '
        'itself -> same-receiver self-recursion to the depth cap. DEX ground truth: '
        'scripts/s58_gz1_forensic.py (Lgz1;/Lbp1; Kotlin default-args ladders; argc '
        'identical across overloads, descriptors distinct). Post-fix: RECURSION-LIMIT '
        'count 0 on v18 AND v23 (miniandroid/run/s58_r376_post4, s58_r376_v18; v18 '
        'rc=0 310k+ instructions with the Choreographer doFrame loop alive). '
        'Regression: semantic_long_cmp_conv_test f102_range_ctor_overload_exact_dispatch '
        '(discriminating). Docs/evidence/s58_r376/.')
    r376['last_updated'] = 'S58 2026-09-18'

# 2. R-NEW-352 -> CLOSED (blocker pre-dated by R-NEW-355)
r352 = find('R-NEW-352')
if r352:
    r352['status'] = 'PROVEN-FIXED'
    r352['priority'] = 'P2'
    r352['fixed'] = 'S58 (blocker = R-NEW-355 pc-advance, fixed S44)'
    r352['evidence'] = (
        'S58 A/B re-proof at the fixed HEAD: microtimer R-NEW-350-law-ON vs law-OFF '
        'PIXEL-IDENTICAL (1,041,437 non-white both; rc=0; HALT-LOOP 0; exactly 2 '
        'forName resolutions — no retry storm; miniandroid/run/s58_r352_lawON vs '
        's58_r352_lawOFF). The S43 50k-revisit loop was the missing pc-advance '
        'contract, root-caused and fixed at S44 (R-NEW-355). The forName law is '
        'DEFAULT-ON now (MINIANDROID_R350_LAW=0 opt-out). Corpus re-verified '
        'pixel-identical to S57 records: chessclock 2,040,736 nb / notes 2,073,600 '
        'nb / unote 236,520 nb. Docs/evidence/s58_r376/.')
    r352['last_updated'] = 'S58 2026-09-18'

# 3. New entries: R-NEW-378 (cascade, fixed via F-103) and next frontier
n378 = next_rnew()  # 378
roots.append({
    'id': n378,
    'status': 'ROOT-CAUSED-FIXED',
    'priority': 'P0',
    'title': 'Dooz post-F-102 cascade: compose rememberSaveable ACCEPTABLE_CLASSES '
             'IAE "Can\'t put value with type null into saved state" (Ljb1;.f via '
             'Lje;.<init> pc=73..104) + Class-keyed map IAE "Key must be a class" '
             '(Lwl0;.containsKey instance-of) — APP BOUNDARY unwind at '
             'MainActivity.onCreate invoke_pc=317',
    'discovered': 'S58',
    'fixed': 'S58 F-103',
    'evidence': (
        'ROOT CAUSE (F-103, generic): (1) Class.isInstance/isAssignableFrom had NO '
        'handler -> STUBBED typed-zero 0 for all 29 ACCEPTABLE_CLASSES; (2) Class '
        'tokens minted from a private counter collided with real heap ids -> §19 '
        'runtime-class dispatch sent Class-token receivers to UNRELATED objects; '
        '(3) execute_instance_of trusted the register\'s cached class_desc unless '
        'EMPTY — the CollectionShadow round-trip degraded the tag to '
        '"Ljava/lang/Object;", defeating heap-authority lookup. FIX: Class '
        'type-question laws over class_to_superclass_/interfaces_ + HEAP-BACKED '
        'Class tokens (const-class allocates Ljava/lang/Class; with '
        '__referent_desc; F-069 identity preserved) + instance-of heap-authority '
        'law. Post-fix: both IAE faces = 0 (miniandroid/run/s58_r376_post3/post4). '
        'Regression: f103_class_isInstance_string_exact, '
        'f103_class_isAssignableFrom_subclass, f103_instanceof_heap_subclass. '
        'Docs/evidence/s58_r376/.'),
    'last_updated': 'S58 2026-09-18',
})

roots.append({
    'id': 'R-NEW-379',
    'status': 'OBSERVED-FAIL',
    'priority': 'P1',
    'title': 'Dooz next frontier (post F-102/F-103): compose init dies at '
             'ViewTreeLifecycleOwner — ISE "ViewTreeLifecycleOwner not found from '
             'Lho;@1074" (Log0;.c) uncaught at MainActivity.onCreate invoke_pc=317; '
             'the owner-tag walk finds no ViewTreeLifecycleOwner on the decor/compose '
             'root chain (predecessor face R-NEW-317 fixed only the ViewShadow '
             'routing; the owner SET law + walk extension remain)',
    'discovered': 'S58',
    'fixed': '',
    'evidence': (
        'miniandroid/run/s58_dooz_final/stderr.log ([THROWABLE-MSG] x4, '
        'APP BOUNDARY unwind; framebuffer 2,073,600 nb — themed window painted '
        'before death). Next ranked: (1) ViewTreeLifecycleOwner.set/get law on the '
        'ViewShadow node model (ComponentActivity.onCreate sets the owner on the '
        'decor view; get walks parents); (2) WindowRecomposer law '
        '(checkPrecondition isAttachedToWindow). Blocks the entire Compose family '
        'below the composition bootstrap.'),
    'last_updated': 'S58 2026-09-18',
})

roots.append({
    'id': 'F-102',
    'status': 'ROOT-CAUSED-FIXED',
    'priority': 'P0',
    'title': 'F-102 (S58): 3rc invoke-*/range descriptor dispatch law — pass the '
             'call site proto to try_recursive_invoke on both attempts '
             '(F-023 exact-descriptor selection); fixes the ctor-climb '
             'self-recursion (R-NEW-376)',
    'discovered': 'S58',
    'fixed': 'S58',
    'evidence': 'See R-NEW-376; fix in dalvik_engine.cpp range-invoke case '
                '(range_proto hoisted + passed); regression '
                'f102_range_ctor_overload_exact_dispatch.',
    'last_updated': 'S58 2026-09-18',
})

roots.append({
    'id': 'F-103',
    'status': 'ROOT-CAUSED-FIXED',
    'priority': 'P0',
    'title': 'F-103 (S58): java.lang.Class type-question laws (isInstance/'
             'isAssignableFrom over the real hierarchy), HEAP-BACKED Class tokens '
             '(const-class allocates a Ljava/lang/Class; object with '
             '__referent_desc; kills the token/heap id-space collision), and the '
             'instance-of runtime-type authority law (heap class wins over the '
             'register tag)',
    'discovered': 'S58',
    'fixed': 'S58',
    'evidence': 'See R-NEW-378; regressions f103_* (3 checks).',
    'last_updated': 'S58 2026-09-18',
})

roots.append({
    'id': 'F-104',
    'status': 'IMPLEMENTED',
    'priority': 'P1',
    'title': 'F-104 (S58): io/state law family — FileInputStream/FileReader sandbox '
             'ctor law + "file:" stream keys in cached_asset_bytes (4 MiB bound); '
             'Uri.fromFile/getPath/getScheme/getLastPathSegment; '
             'ContentResolver.openInputStream; AsyncTask.execute '
             '(doInBackground+onPostExecute dispatch, ancestor-walk recognized); '
             'EnumSet.of; java.util.regex Pattern.compile / Matcher.find/matches/'
             'group/appendReplacement/appendTail (std::regex); requestPermissions '
             '-> onRequestPermissionsResult callback dispatch; BufferedInputStream '
             'joins the EXP-071 wrapper-propagation chain; [EXP093-FNA] trace '
             'env-gated (F-074 hygiene)',
    'discovered': 'S58',
    'fixed': 'S58',
    'evidence': (
        'Notes v139 real read chain proven live: seeded sandbox doc -> app '
        'defaultFile/readNote/ReadTask -> openInputStream (present=1) -> readLine '
        'x10 real lines -> setText sb_value extraction (230 chars verified) -> '
        'markdownCheck appendTail (230 chars preserved). Battery 96/96 ALL PASS at '
        'this HEAD. Remaining: commonmark parse->render yields an empty body '
        '(F-085 stays open at that face). Docs/evidence/s58_r376/.'),
    'last_updated': 'S58 2026-09-18',
})

reg['summary'] = reg.get('summary', '')
with open(REG, 'w') as f:
    json.dump(reg, f, indent=1)
print('registry updated:', len(roots), 'roots')
print('R-NEW-376 -> ROOT-CAUSED-FIXED; R-NEW-352 -> PROVEN-FIXED;'
      ' added', n378, 'R-NEW-379 F-102 F-103 F-104')
