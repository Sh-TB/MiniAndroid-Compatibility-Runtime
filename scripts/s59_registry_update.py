#!/usr/bin/env python3
"""S59 registry update: R-NEW-379 closure (F-105 view-tree owner +
declaration/heap reconciliation + CLASS_REF token instance-of), R-NEW-380
next pinned face. No new roadmap, no new branch, no new campaigns.
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


# 1. R-NEW-379 -> ROOT-CAUSED-FIXED via F-105
r379 = find('R-NEW-379')
if r379:
    r379['status'] = 'ROOT-CAUSED-FIXED'
    r379['priority'] = 'P1'
    r379['fixed'] = 'S59 F-105 (a: declaration/heap reconciliation; b: ComponentActivity view-tree owner contract; c: CLASS_REF token instance-of)'
    r379['evidence'] = (
        'ROOT CAUSE (DEX ground truth: scripts/s59_vtlo_forensic.py, s59_dump_vtlo.py, '
        's59_dump2.py, s59_tagsites.py, s59_setfind.py): the lifecycle 2.8 walk '
        'Lxd1;.g(View)Lvo0; loops { getTag(view, 2131230840) -> miss -> parent = '
        'Lrd1;.v(view) -> instance-of parent, Landroid/view/View; -> if false abort }. '
        '2131230840 = 0x7F080078 = R.id.view_tree_lifecycle_owner (aapt2-verified). '
        'ZERO setTag sites for that key exist in the app DEX (owner install is '
        'androidx ComponentActivity library machinery). TWO engine faces: '
        '(D1) the parent hop aborted — ViewShadow node 20 is the F-023 activity-as-'
        'view node (id == the activity heap id BY DESIGN); heap#20 is the MainActivity, '
        'so the F-103 heap-authority classified the VIEW reference as the ACTIVITY -> '
        '`parent as? View` FALSE (INSTANCEOF-DIAG: obj#20 class=Landroid/view/View; '
        'heap=Lio/github/yamin8000/dooz/ui/MainActivity; FALSE) -> walk dead-ended -> '
        'ISE "ViewTreeLifecycleOwner not found from Lho;@1074" x4 (run/s59_repro). '
        '(D2) nobody ever wrote the owner tag (F-023/F-103 surface). '
        'FIX F-105 (all generic): (a) reconcile_class_decl() shared by instance-of and '
        'check-cast — generic declaration -> heap wins (F-103 preserved); consistent '
        'pair -> the more specific wins; CONTRADICTION -> the creation-site declaration '
        'wins (re-homing onto proxies was prototyped and REJECTED: the proxy id breaks '
        'the next shadow hop — getTag/getParent key by the shadow node id). '
        '(b) ActivityShadow setContentView(View) installs the ACTIVITY object under the '
        'app OWN view_tree_lifecycle_owner id (name-resolved via arsc find_id, no '
        'hardcoded id) on the activity-as-view node BEFORE the attach wave. '
        '(c) instance-of classifies CLASS_REF values (const-class tokens, F-069/F-103) '
        'by the token heap record — runtime class IS java.lang.Class. '
        'Post-fix (run/s59_f105_post1 + post2): F105-OWNER install line; walk hits the '
        'owner at node 20 and the app dialog machinery (Le81;.<init>) propagates it '
        'onto the decor (setTag view=308 key=2131230840 obj=20); ISE count 0 (was x4); '
        'execution advanced from depth 8 to depth 81. '
        'Regression: semantic_long_cmp_conv_test f105_instanceof_classtoken_is_class + '
        'f105_instanceof_classtoken_not_referent (26/26); battery ALL PASS; corpus '
        'determinism chessclock ecc001fd8e33519a / notes cf521b168a9b4ed2 / unote '
        '7b30d52201bb22ac — all == the S57/S58 records. Docs/evidence/s59_r379/.')
    r379['last_updated'] = 'S59 2026-09-18'

# 2. Register R-NEW-380 (the next pinned face — honest observation, not forced)
r380 = find(next_rnew())
r380 = {
    'id': next_rnew(),
    'status': 'OBSERVED-FAIL',
    'priority': 'P1',
    'app': 'io.github.yamin8000.dooz_23 (dooz, PRIORITY-1)',
    'discovered': 'S59',
    'last_updated': 'S59 2026-09-18',
}
roots.append(r380)

# fill after id resolution
for x in roots:
    if isinstance(x, dict) and x.get('id') == r380['id']:
        x.update({
            'title': ('Dooz next frontier (post F-105): ViewModelProvider create chain '
                      'falls to the throwing factory fallback — RuntimeException '
                      '"Cannot create an instance of " (class-name portion EMPTY) '
                      'caller=Leo;.n pc=53 depth=81; chain Lyd0;.b -> Ltf1;.b -> '
                      'Lt32;.b -> Lt32;.d -> Leo;.n while constructing the app '
                      'GameViewModel after the Lwl0;.containsKey Class-key guard '
                      'PASSES (F-105c)'),
            'evidence': ('miniandroid/run/s59_f105_post2/stderr.log (key lines hashed '
                         'in docs/evidence/s59_r379/post2_keylines.log). The '
                         'Class.toString/arg surface for CLASS_REF values renders an '
                         'empty name in the message; the deeper gap is the create path '
                         'itself (getDeclaredConstructor -> Constructor.newInstance -> '
                         'real <init> for the app GameViewModel; the [M3-REFLECT] '
                         'surface exists but the chain does not complete for this '
                         'path). Blocks the dooz first successful ViewModel '
                         'construction; Compose attach (R-NEW-379 owner contract) is '
                         'now live and correct upstream of this face.'),
            'next': ('(1) Trace Leo;.n exact failure input — which factory step failed '
                     '(ctor discovery vs newInstance dispatch vs a stubbed dependency). '
                     '(2) Class.toString/getName for CLASS_REF args (referent name '
                     'surface). (3) Constructor.newInstance -> try_recursive_invoke on '
                     'GameViewModel.<init> — run the real ctor DEX. (4) Re-run dooz '
                     'v23: expect the GameViewModel instance live in the '
                     'ViewModelStore and Compose advancing past the create chain.'),
        })
        break

# 3. Summary — the PINNED active frontier (S57/S58 precedent: the tracked
# frontier list carries the current dooz pin; stale placeholder roots keep
# their own statuses in the body).
open_frontiers = ['R-NEW-380']
reg['summary']['open_frontiers'] = open_frontiers
reg['summary']['last_updated'] = 'S59 2026-09-18'
reg['summary']['note'] = (
    'S59 ROADMAP-3-CLOSURE: R-NEW-379 ROOT-CAUSED-FIXED (F-105 a/b/c — view-tree '
    'owner contract + declaration/heap reference reconciliation + CLASS_REF token '
    'instance-of). Dooz advanced past the ViewTreeLifecycleOwner ISE and the '
    'Class-token key guard into the ViewModelProvider create surface: R-NEW-380 '
    'is the remaining pinned frontier (P1). No new roadmap/branch/campaign; all '
    'closures reference existing items.')

with open(REG, 'w') as f:
    json.dump(reg, f, indent=1, ensure_ascii=False)

print('R-NEW-379 -> ROOT-CAUSED-FIXED')
print('registered', r380['id'], 'OBSERVED-FAIL P1')
print('open_frontiers =', open_frontiers)
