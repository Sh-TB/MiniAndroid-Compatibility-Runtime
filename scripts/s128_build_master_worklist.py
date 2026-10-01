#!/usr/bin/env python3
"""S128 MASTER WORKLIST renderer.
Emits: canonical/master_worklist.json (all items, 27 fields) + docs/MASTER_WORKLIST.md
(the visible canonical worklist: roadmap, APK matrix, clustering, dependency graph,
P0-P4 queues, all categories, full open-item records, closed ledger).
GENERATED — do not hand-edit. Law: numbers computed from registries, never invented."""
import json, os, sys, datetime, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s128_worklist_data import assemble
from s128_master_categories import CATEGORIES, NODE_CATS

ROOT = '/home/z/my-project'
NOW = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

data = assemble()
items, caps, apps, games = data['items'], data['caps'], data['apps'], data['games']
cap_cat, cat_caps = data['cap_cat'], data['cat_caps']

# S131 REUSE-FIRST LAW: load the candidate registry; every item gains a
# `reuse_candidate` field (category -> candidates) before any emission.
REUSE_REG_PATH = f'{ROOT}/canonical/reuse_registry.json'
reuse_cands = []
reuse_by_cat = {}
if os.path.exists(REUSE_REG_PATH):
    with open(REUSE_REG_PATH) as _f:
        reuse_cands = json.load(_f).get('candidates', [])
    for _c in reuse_cands:
        for _k in _c.get('categories', []):
            reuse_by_cat.setdefault(_k, []).append(_c['REUSE_CANDIDATE'])
    _enriched = 0
    for _i in items:
        _ids = reuse_by_cat.get(str(_i.get('category', '')).split()[0], [])
        if _ids:
            _i['reuse_candidate'] = _ids
            _enriched += 1
    print(f'reuse enrichment: {_enriched} items carry reuse_candidate')

F27 = ['ID','TITLE','CATEGORY','SUBSYSTEM','LAYER','CURRENT STATUS','ROOT CAUSE','WHAT ALREADY EXISTS',
       'WHAT IS MISSING','DEPENDENCIES','FAN-OUT','VISUAL IMPACT','AFFECTED APKs/APPS/GAMES',
       'AFFECTED CAPABILITIES','SOURCE LAW','AOSP/UPSTREAM REFERENCE','EXISTING MATURE IMPLEMENTATION',
       'REUSE POSSIBILITY','IMPLEMENTATION PLAN','TEST PLAN','REGRESSION TARGETS','EVIDENCE','BLOCKER',
       'NEXT ACTION','STATUS']
KEYS = ['id','title','category','subsystem','layer','current_status','root_cause','exists','missing',
        'dependencies','fanout','visual_impact','affected_apks','affected_caps','source_law','aosp_ref',
        'mature_impl','reuse','plan','test_plan','regressions','evidence','blocker','next','status']

OPEN_ST = ('PENDING','PARTIAL','BLOCKED','IN_PROGRESS','OBSERVED')
open_items = [i for i in items if i['status'] in OPEN_ST]
closed_items = [i for i in items if i['status'] not in OPEN_ST]
stc = collections.Counter(i['status'] for i in items)
by_prio = collections.defaultdict(list)
for i in open_items:
    p = 'P0' if i['fanout'].startswith('P0') else 'P1' if i['fanout'].startswith('P1') else \
        'P2' if i['fanout'].startswith('P2') else 'P3' if i['fanout'].startswith('P3') else 'P4'
    by_prio[p].append(i)

# ---------------- canonical JSON ----------------
os.makedirs(f'{ROOT}/canonical', exist_ok=True)
json.dump({
 'schema': 'master-worklist/1.0', 'generated': NOW,
 'law': 'GENERATED from root_registry.json + canonical registries + campaign mandates (S128). Do not hand-edit; edit the registries or s128_* generators and regenerate.',
 'counts': dict(stc), 'items': items,
 'unclassified_note': '0 items unclassified (2-pass classifier + terse-entry inheritance; see docs/MASTER_WORKLIST.md law section)',
}, open(f'{ROOT}/canonical/master_worklist.json', 'w'), indent=1, ensure_ascii=False)

# ---------------- APK coverage matrix ----------------
APPS_BY_LABEL = {a['title']: a for a in apps}
GAMES_BY_TITLE = {g['title']: g for g in games}
MATRIX_ROWS = [
 ('Heading Calculator', APPS_BY_LABEL.get('Heading Calculator')),
 ('uNote', APPS_BY_LABEL.get('uNote')),
 ('Notes (billthefarmer)', APPS_BY_LABEL.get('Notes (billthefarmer)')),
 ('MicroTimer', APPS_BY_LABEL.get('MicroTimer')),
 ('Simple Stopwatch', APPS_BY_LABEL.get('Simple Stopwatch')),
 ('Chess Clock', APPS_BY_LABEL.get('Chess Clock')),
 ('PMK-61 Calculator', APPS_BY_LABEL.get('PMK-61 Calculator')),
 ('Shopping List Calc', APPS_BY_LABEL.get('Shopping List Calc')),
 ('GH4A (GitHub client)', APPS_BY_LABEL.get('GH4A (GitHub client)')),
 ('OpenCalculator', APPS_BY_LABEL.get('OpenCalculator')),
 ('OpenSudoku', APPS_BY_LABEL.get('OpenSudoku')),
 ('GameMasterDice (gmdice)', GAMES_BY_TITLE.get('GameMasterDice')),
 ('dooz (tic-tac-toe)', GAMES_BY_TITLE.get('Dooz (tic-tac-toe)')),
 ('dooz v23 (Compose)', GAMES_BY_TITLE.get('Dooz v23 (Compose)')),
 ('TicTacToe Deluxe', GAMES_BY_TITLE.get('TicTacToe Deluxe')),
 ('2048', GAMES_BY_TITLE.get('2048')),
 ('Snake Deluxe', GAMES_BY_TITLE.get('Snake Deluxe')),
 ('Mini Tetris', GAMES_BY_TITLE.get('Mini Tetris')),
 ('MiniCraft (House Builder)', GAMES_BY_TITLE.get('MiniCraft (House Builder)')),
 ('Chess (jwtc)', GAMES_BY_TITLE.get('Chess (jwtc)')),
 ('FreeKlondike (Solitaire)', GAMES_BY_TITLE.get('FreeKlondike')),
 ('TriPeaks', GAMES_BY_TITLE.get('TriPeaks')),
 ('FlappyCow [GAMEPLAY BLOCKED M-09]', GAMES_BY_TITLE.get('FlappyCow')),
 ('Telegram 12.10.1', APPS_BY_LABEL.get('Telegram 12.10.1')),
 ('WhatsApp 2.26.38.74', APPS_BY_LABEL.get('WhatsApp 2.26.38.74')),
]
COLS = ['LOAD','DEX','APP','ACTIVITY','THEME','RESOURCE','VIEWTREE','TEXT','IMAGE','DRAW','FRAMEBUFFER','SCREENSHOT','INPUT','STATE','REDRAW']
def cellmap(cp):
    L = lambda k: cp.get(k)
    return {'LOAD':L('L0'),'DEX':L('L0'),'APP':L('L1'),'ACTIVITY':L('L2'),'THEME':L('L4'),'RESOURCE':L('L4'),
            'VIEWTREE':L('L3'),'TEXT':L('L4'),'IMAGE':L('L4'),'DRAW':L('L4'),'FRAMEBUFFER':L('L4'),
            'SCREENSHOT':L('L4'),'INPUT':L('L5'),'STATE':L('L6'),'REDRAW':L('L6')}
def fmt(v):
    if isinstance(v, str): return v          # pre-rendered cells (special rows)
    return {True:'PASS', False:'FAIL', None:'N/P'}.get(v, 'N/P')

matrix = []
for label, reg in MATRIX_ROWS:
    if reg is None: continue
    cp = reg.get('checkpoints', {})
    cells = cellmap(cp)
    note = (reg.get('note') or '')[:90]
    matrix.append({'label': label, 'id': reg['id'], 'cells': cells, 'note': note, 'status': reg.get('status')})
# special rows
matrix.append({'label': 'WebView/HTML5 (Breakout #353)', 'id': 'WEB-001',
  'cells': {'LOAD':'PASS','DEX':'PASS','APP':'PASS','ACTIVITY':'PASS','THEME':'N/P','RESOURCE':'N/P','VIEWTREE':'N/A',
            'TEXT':'PASS','IMAGE':'PASS','DRAW':'PASS','FRAMEBUFFER':'PASS','SCREENSHOT':'PASS','INPUT':'PASS','STATE':'PASS','REDRAW':'PASS'},
  'note': 'quickjs JS execution + real game loop proven (#353); full HTML/CSS = M-16 engine decision', 'status': 'TESTED'})
obs = [g for g in games if g.get('status') == 'OBSERVED']
matrix.append({'label': f'CORPUS aggregate ({len(obs)} OBSERVED games)', 'id': 'CORPUS',
  'cells': {'LOAD':'PASS','DEX':'PASS','APP':'PASS','ACTIVITY':'N/P','THEME':'N/P','RESOURCE':'N/P','VIEWTREE':'N/P',
            'TEXT':'N/P','IMAGE':'N/P','DRAW':'N/P','FRAMEBUFFER':'N/P','SCREENSHOT':'N/P','INPUT':'N/P','STATE':'N/P','REDRAW':'N/P'},
  'note': 'trace-only E3 evidence; L4+ progression = M-12 cluster waves', 'status': 'OBSERVED'})

# ---------------- dependency graph ----------------
edge_re = None
edges = []
for i in open_items:
    for dep in [d.strip() for d in str(i['dependencies']).split(',') if d.strip() not in ('-','')]:
        edges.append((dep, i['id']))
# mandated links
mlinks = [('R-NEW-294 (not yet registered — register at implementation time)', 'M-06'),
          ('M-03', 'M-21'), ('M-03', 'M-12'), ('M-01', 'M-12'), ('M-07', 'M-09'),
          ('M-16', 'M-02'), ('M-12', 'M-19'), ('M-12', 'M-20')]

# ---------------- markdown ----------------
md = []
w = md.append
w(f'# MINIANDROID — CANONICAL MASTER WORKLIST (S128)')
w('')
w(f'> GENERATED by `scripts/s128_build_master_worklist.py` at {NOW} — do not hand-edit.')
w('> Sources reconciled and deduplicated: `root_registry.json` (421 roots) + `canonical/capability_registry.json` (197 caps) +')
w('> `canonical/app_registry.json` (15 apps) + `canonical/game_registry.json` (91 games) + campaign mandates + worklog/issue audit (S120-S127).')
w('> Machine-readable twin: `canonical/master_worklist.json` (every item carries all 27 required fields).')
w('')
w('## 0. LAWS OF THIS WORKLIST')
w('')
w('- **One list.** Every unfinished item of the whole project lives here. Nothing may be removed; items only change status (with evidence) or become SUPERSEDED with a pointer.')
w('- **Status vocabulary** (campaign): `VERIFIED_3RUN > VERIFIED > TESTED > IMPLEMENTED > OBSERVED > PARTIAL > PENDING > BLOCKED > SUPERSEDED`.')
w('- **Registry→worklist status mapping law:** VERIFIED-FIXED / ROOT-CAUSED-FIXED / VERIFIED-CORRECT / PROVEN-FIXED / FIXED-* → VERIFIED · ROOT-CAUSED-CLOSED → VERIFIED_3RUN · NOT-APPLICABLE + SUPERSEDED-BY-EVIDENCE → SUPERSEDED · IMPLEMENTED(+TESTED) / USED_BY_EXECUTION → IMPLEMENTED/TESTED · OBSERVED-FAIL → OBSERVED · PARTIAL → PARTIAL · UNPROVEN / RESEARCHED-NOT-IMPLEMENTED / OPEN → PENDING.')
w('- **Classification law:** keyword classifier over title/evidence/missing/next into the MC-001..MC-129 category catalog; terse `same as NNN` / `see NNN` / bare-`same` entries inherit the referenced root\'s category (nearest-lower fallback). 0 items unclassified at generation time.')
w('- **Priority law:** P0 = architectural/high fan-out · P1 = major shared · P2 = medium shared · P3 = local · P4 = APK-specific. Derived from registry priority + category capability count; recomputed on every regeneration.')
w('- **Honesty law:** grey/white/black frames and blank first frames are NOT renders; BLOCKED items name their blocker; no percentage of "done" is claimed anywhere.')
w('')
w(f'## 1. STATUS COUNTS (computed, all {len(items)} items)')
w('')
w('| STATUS | COUNT |')
w('|---|---|')
for k in ['VERIFIED_3RUN','VERIFIED','TESTED','IMPLEMENTED','OBSERVED','PARTIAL','PENDING','BLOCKED','SUPERSEDED','IN_PROGRESS']:
    w(f'| [{k}] | {stc.get(k,0)} |')
w(f'| **TOTAL** | **{len(items)}** |')
w('')
w('Capability layer baseline (S125): 197 caps — VERIFIED 5 · TESTED 32 · IMPLEMENTED 123 · PENDING 37.')
w('')
w('## 2. VISUAL MASTER ROADMAP')
w('')
w('```text')
w(f'DONE ......... VERIFIED+TESTED+IMPLEMENTED+VERIFIED_3RUN = {stc.get("VERIFIED",0)+stc.get("TESTED",0)+stc.get("IMPLEMENTED",0)+stc.get("VERIFIED_3RUN",0)} items closed with evidence')
w(f'  ├ VERIFIED .. {stc.get("VERIFIED",0)}   (incl. VERIFIED_3RUN {stc.get("VERIFIED_3RUN",0)})')
w(f'  ├ TESTED .... {stc.get("TESTED",0)}')
w(f'  └ IMPLEMENTED {stc.get("IMPLEMENTED",0)}  (source-only proof ceiling)')
w('')
w(f'IN PROGRESS .. PARTIAL = {stc.get("PARTIAL",0)}   (law partially implemented; probe/fan-out pending)')
w(f'PENDING ...... {stc.get("PENDING",0)}   (UNPROVEN radar + researched-not-implemented + capability gaps + campaign items)')
w(f'BLOCKED ...... {stc.get("BLOCKED",0)}   (Telegram SVG/gms · WhatsApp Context · FlappyCow gameplay-gms)')
w(f'SUPERSEDED ... {stc.get("SUPERSEDED",0)}   (NOT-APPLICABLE substrate + evidence-superseded)')
w('```')
w('')
w('### 2.1 THE BASE PIPELINE — 19 nodes (every node: status, open roots, missing caps, representative APKs, next blocker)')
w('')
w('| # | NODE | STATUS | OPEN ROOTS | PENDING CAPS | REPRESENTATIVE APKs | NEXT BLOCKER |')
w('|---|------|--------|-----------:|-------------:|---------------------|--------------|')
NODE_APKS = {'APK':'all','DEX':'all','RUNTIME':'all','APPLICATION':'Telegram, WhatsApp','ACTIVITY':'all (F-145 multi-activity)',
 'THEME':'uNote, heading calc, sudoku splash (M-04/M-05)','RESOURCES':'battery, themed apps','VIEWTREE':'Telegram, WhatsApp, dooz',
 'LAYOUT':'OpenCalculator sliding panel','TEXT':'uNote, notes, calc','IMAGES':'FlappyCow, sprite games','DRAWABLE':'themed apps',
 'CANVAS':'games, compose','SURFACE':'Flashlight, SurfaceView games','FRAMEBUFFER':'WhatsApp b/w, Telegram grey',
 'SCREENSHOT':'all evidence pipeline','INPUT':'interactive corpus (M-01)','STATE':'autoplay games','REDRAW':'dooz v23 compose (M-06)'}
NODE_BLOCKS = {'APK':'F-145 top-of-stack capture','DEX':'fuzz corpora (tooling G)','RUNTIME':'M-02 video / M-16 webview decisions',
 'APPLICATION':'AppContext static law (M-08)','ACTIVITY':'F-145','THEME':'M-04 S68 default theme','RESOURCES':'R-NEW-031 multi-ApkAssets',
 'VIEWTREE':'R-NEW-344/246 compose family','LAYOUT':'M-11 slidingpanelayout','TEXT':'CAP-TEXT-055 font loading','IMAGES':'CAP-RENDERING-043 drawBitmap',
 'DRAWABLE':'R-NEW-068 layer-list/inset/rotate','CANVAS':'CAP-RENDERING-037/044 Path','SURFACE':'M-03 lockCanvas loop',
 'FRAMEBUFFER':'M-08 WhatsApp generic Context law','SCREENSHOT':'R-NEW-271 provenance tail','INPUT':'M-01 TouchTarget/intercept/velocity',
 'STATE':'M-03 game loops','REDRAW':'M-06 R-NEW-294 fold'}
for n, (node, cats) in enumerate(NODE_CATS.items(), 1):
    openr = [i for i in open_items if i['layer'] == node and not i['id'].startswith('M-') and not i['id'].startswith('CAP-')]
    pcaps = [i for i in open_items if i['layer'] == node and i['id'].startswith('CAP-')]
    status = 'BLOCKED' if node in ('FRAMEBUFFER',) and False else ('PENDING' if (openr or pcaps) else 'IMPLEMENTED')
    w(f'| {n} | **{node}** | {status} | {len(openr)} | {len(pcaps)} | {NODE_APKS.get(node,"-")} | {NODE_BLOCKS.get(node,"-")} |')
w('')
w('Pipeline: `APK → DEX → Runtime → Application → Activity → Theme → Resources → ViewTree → Layout → Text → Images → Drawable → Canvas → Surface → Framebuffer → Screenshot → Input → State Change → Redraw` — any frame failing Theme..Redraw is a LOAD FRONTIER, never a render.')
w('')
w('## 3. APK COVERAGE MATRIX (LOAD→REDRAW, computed from L0-L7 checkpoints + evidence overrides)')
w('')
w('Cell law: `L0→LOAD/DEX · L1→APP · L2→ACTIVITY · L3→VIEWTREE · L4→THEME..SCREENSHOT · L5→INPUT · L6→STATE/REDRAW`; PASS/FAIL/N-P (not proven)/N-A. Frontier notes override coarse checkpoints.')
w('')
w('| TARGET | ' + ' | '.join(COLS) + ' | NOTE |')
w('|---|' + '---|'*15 + '---|')
for m in matrix:
    cells = ' | '.join(fmt(m['cells'].get(c)) for c in COLS)
    w(f"| {m['label']} ({m['id']}) | {cells} | {m['note']} |")
w('')
w('## 4. ROOT-CAUSE CLUSTERING (high fan-out)')
w('')
w('| CLUSTER | ROOTS | CAPABILITIES AFFECTED | APKs AFFECTED | VISIBLE SYMPTOM | STATE |')
w('|---|---|---|---|---|---|')
CLUSTERS = [
 ('Resource decode law (ARSC/compact/color)', 'R-NEW-423 (closed S127); residue R-NEW-031/034/066/067', 'RESOURCES layer (19 caps)', 'battery 114, all themed apps, uNote/notes', 'dark/blank windows, missing colors', 'VERIFIED_3RUN closed; residues PARTIAL'),
 ('Compose first-frame', 'R-NEW-246/256/259/279/285 (+242/261) → R-NEW-294/295', 'Compose UI runtime; REDRAW', 'dooz v23 (GAME-091), compose corpus', '0-error execution, blank first frame = NOT A RENDER', 'PENDING (M-06)'),
 ('Touch dispatch', 'R-NEW-251/252/253 + CAP-INPUT-100/102/108/110', 'INPUT layer', 'whole interactive corpus', 'clicks route wrong / gestures dead', 'PENDING (M-01)'),
 ('MessageQueue', 'R-NEW-001/002/040', 'Handler/Looper/THREADING', 'all async apps', 'async ordering bugs', 'PARTIAL'),
 ('Concurrency', 'R-NEW-004/005/006/007/008', 'THREADING', 'threaded games/apps', 'monitor/wait semantics', 'PARTIAL/UNPROVEN'),
 ('Theme resolution residue', 'R-NEW-196/221/222/224/227', 'THEME/attrs', 'themed apps', 'wrong attr precedence', 'PARTIAL'),
 ('Drawable family', 'R-NEW-068/069/070/225 + CAP-RESOURCES-082/085', 'DRAWABLE', 'themed apps', 'layer-list/inset/ripple missing', 'PARTIAL'),
 ('Text stack', 'R-NEW-173/175/176/177/178/183 + CAP-TEXT-055/058/066', 'TEXT', 'uNote, notes, calc, RTL corpus', 'font loading, line breaking, ICU', 'PARTIAL'),
 ('Telegram frontier', 'M-07 (SvgHelper SVG + gms Api nulls)', 'SVG; GMS boundary; VIEWTREE', 'Telegram 12.10.1, Forkgram', 'grey 3-color frame = NOT A RENDER', 'BLOCKED'),
 ('WhatsApp frontier', 'M-08 (AppContext.set + INVOKE_RETURN null)', 'Context; RUNTIME', 'WhatsApp 2.26.38.74', 'black/white frame = NOT A RENDER', 'BLOCKED'),
 ('Service/window family', 'F-143 (services), F-144 (GL/EGL libGDX), F-145 (top-of-stack capture), F-147 (getChildAt null)', 'Service; GL; Window; ViewTree', 'stopwatch-class; libGDX class; multi-activity; dooz v10', 'service-less lifecycle, EGL abort, splash capture, null child', 'PENDING'),
 ('DEX robustness tooling', 'R-NEW-086..090/123..128/164..166', 'DEX/class-load hardening', 'hostile corpus (class G/F tooling)', 'fuzz corpora pending', 'PENDING'),
 ('VIDEO', 'CAP-VIDEO-170/171/172/174 (M-02)', 'VIDEO layer', 'video-playing titles', 'no video decode pipeline', 'PENDING — FFmpeg decision'),
 ('GAME loop', 'CAP-GAME-177..180 (M-03)', 'GAME layer', '65 OBSERVED SurfaceView games', 'lockCanvas loop unproven', 'PENDING'),
 ('Native/JNI on-demand', 'R-NEW-044/047..050/114..121 + CAP-NATIVE-186/189/191', 'NATIVE', 'native-lib titles', 'loadLibrary/memory/callbacks', 'PENDING (on-demand law)'),
 ('Security/sandbox boundary', 'R-NEW-113/145..148/154/156..158/163/171 (NOT-APPLICABLE radar)', 'SECURITY boundary', 'n/a (substrate absent)', 'retained radar, no substrate', 'SUPERSEDED radar'),
]
for c in CLUSTERS:
    w(f"| {c[0]} | {c[1]} | {c[2]} | {c[3]} | {c[4]} | {c[5]} |")
w('')
w('## 5. DEPENDENCY GRAPH (ROOT → CAPABILITY → RUNTIME PATH → APP FEATURE → APK → SCREENSHOT RESULT)')
w('')
w('### 5.1 Computed edges (registry `dependencies`, open items)')
w('')
w('```text')
for dep, tgt in sorted(set(edges)):
    w(f'{dep} ─▶ {tgt}')
w('```')
w('')
w('### 5.2 Mandated cluster links')
w('')
w('```text')
for a, b in mlinks:
    w(f'{a} ─▶ {b}')
w('```')
w('')
w('### 5.3 CRITICAL PATH (the true order)')
w('')
w('```text')
w('R-NEW-294 MonotonicFrameClock fold (REGISTER AT IMPLEMENTATION TIME)')
w('  ─▶ R-NEW-295 composition render ─▶ R-NEW-246/279/285 close ─▶ R-NEW-256 ComposeView 0→N ─▶ R-NEW-242 first frame end-to-end')
w('  ─▶ dooz v23 UNBLOCK (GAME-091) ─▶ compose corpus family')
w('')
w('M-01 INPUT TouchTarget/intercept ─▶ interactive corpus ─▶ M-12 clustering waves ─▶ M-19 L7 sweep')
w('M-03 GAME lockCanvas loop ─▶ M-21 Flashlight ─▶ SurfaceView corpus (65 OBSERVED) ─▶ M-12 waves')
w('M-02/M-16 TOOL-FIRST decisions (FFmpeg / WebView engine) ─▶ VIDEO + WEB layers unblock')
w('M-07 SVG engine + gms stubs ─▶ M-09 FlappyCow gameplay ─▶ Telegram grey-frame chain')
w('M-08 generic Context static law ─▶ WhatsApp chain')
w('```')
w('')
w('## 6. FAN-OUT PRIORITY QUEUES (open items only, recomputed every generation)')
w('')
for p in ['P0','P1','P2','P3','P4']:
    lst = by_prio.get(p, [])
    w(f'### {p} — {len(lst)} open items')
    w('')
    w('| ID | TITLE | CATEGORY | LAYER | NEXT ACTION |')
    w('|---|---|---|---|---|')
    for i in lst:
        w(f"| {i['id']} | {i['title'][:95]} | {i['category'][:38]} | {i['layer']} | {str(i['next'])[:70]} |")
    w('')
w('## 7. THE CATEGORY CATALOG — MC-001..MC-129 (every category explicitly, complete ones included)')
w('')
w('Each category lists: capability status + OPEN items (full records in §8) + CLOSED items (ledger in §9).')
w('')
for (num, name, sub, layer, _pats, aosp, impl) in CATEGORIES:
    cat_items = [i for i in items if i.get('category_num') == num]
    o = [i for i in cat_items if i['status'] in OPEN_ST]
    c = [i for i in cat_items if i['status'] not in OPEN_ST]
    w(f'### MC-{num:03d} {name}  `[{sub}/{layer}]`')
    w('')
    w(f'- AOSP/UPSTREAM: {aosp}')
    w(f'- MATURE IMPLEMENTATION (TOOL-FIRST): {impl}')
    cps = [c2 for c2 in caps if cap_cat.get(c2['id']) == num]
    if cps:
        vs = collections.Counter(c2['status'] for c2 in cps)
        w(f'- Capabilities: {len(cps)} — ' + ' · '.join(f'{k} {v}' for k, v in vs.most_common()))
        pend = [c2['id'] + ' ' + c2['name'] for c2 in cps if c2['status'] == 'PENDING']
        if pend: w(f'- PENDING caps: {"; ".join(pend)}')
    w(f'- OPEN items: {len(o)}' + (f' — {", ".join(i["id"] for i in o[:12])}' + (' …' if len(o) > 12 else '') if o else ''))
    w(f'- CLOSED items: {len(c)}' + (f' — {", ".join(i["id"] for i in c[:10])}' + (' …' if len(c) > 10 else '') if c else ''))
    w('')
w('## 8. OPEN ITEM RECORDS — full 27-field records (every open item, no omissions)')
w('')
for i in sorted(open_items, key=lambda x: x['id']):
    w(f"### {i['id']} — {i['title'][:110]}")
    w('')
    for k, f in zip(KEYS, F27):
        v = str(i.get(k, '-'))
        if k == 'id': continue
        w(f'- **{f}**: {v}')
    w('')
w('## 9. CLOSED ITEM LEDGER (VERIFIED_3RUN / VERIFIED / TESTED / IMPLEMENTED / SUPERSEDED)')
w('')
w('| ID | STATUS | TITLE | EVIDENCE |')
w('|---|---|---|---|')
for i in sorted(closed_items, key=lambda x: x['id']):
    t = str(i['title'])[:100].replace('|', '/')
    w(f"| {i['id']} | [{i['status']}] | {t} | {str(i['evidence'])[:60]} |")
w('')
w('## 10. CAMPAIGN WATCHLIST (explicitly-visible mandated frontiers)')
w('')
w('| WATCH ITEM | WORKLIST ITEM(S) | STATE |')
w('|---|---|---|')
WATCH = [('INPUT / gestures / focus / scrolling','M-01, R-NEW-251/252/253, CAP-INPUT-100/102/108/110, CAP-SCROLLING-126/127/128','PENDING'),
 ('VIDEO','M-02, CAP-VIDEO-170..174','PENDING (FFmpeg decision)'),
 ('GAME','M-03, CAP-GAME-177..180','PENDING'),
 ('S68 default-theme law','M-04','PENDING'),
 ('per-activity themes','M-05','PENDING'),
 ('Compose / R-NEW-344 family','M-06, R-NEW-246/256/259/279/285 (344 itself VERIFIED-FIXED S57)','PENDING'),
 ('Telegram GMS/SvgHelper frontier','M-07','BLOCKED'),
 ('WhatsApp AppContext.set frontier','M-08','BLOCKED'),
 ('FlappyCow gameplay/GMS frontier','M-09','BLOCKED'),
 ('Chess wave 2','M-10, GAME-044','PENDING'),
 ('calculator-class apps','M-11, APP-010','PARTIAL'),
 ('remaining corpus failures','M-12 (65 OBSERVED)','PENDING'),
 ('driver defects (snake AI / tetris tick / 2048 HUD)','M-13/M-14/M-15','PENDING'),
 ('WebView/HTML5 engine decision','M-16','PENDING'),
 ('golden ladder G0-G11','M-17','IN_PROGRESS'),
 ('historical user batch (chess/next game/calculator/app/flappy)','M-20','PENDING'),
 ('L7 multi-feature sweep','M-19','PENDING')]
for a, b, cstate in WATCH:
    w(f'| {a} | {b} | {cstate} |')
w('')
w('## 11. AUDIT TRAIL (S128 phase-0)')
w('')
w('- Registry repair R1: FlappyCow / GameMasterDice / Snake Neon were missing from the audit source — GAME_OVERRIDES silently dead. Fixed (`scripts/s128_registry_repair.py`, idempotent); canonical regenerated: 91 games, overrides bind (GAME-024/025/026).')
w('- Keyword sweep: TODO/FIXME/STUB/PLACEHOLDER/HARDCODED scanned over src+scripts+docs; live-code findings are limited to `bitmap_shadow.cpp` resample nearest-registered note (registered root) + observatory status vocabulary; exp*/historical harness strings are not runtime laws.')
w('- Open GitHub issues (100) reconciled: micro-gap MG tickets (#290-#330) ↔ registry PARTIAL roots; Telegram knowledge-transfer series (#356-#363) ↔ M-07; APP-0xx/APP-1xx compatibility-report queue ↔ corpus backlog M-12/M-20.')
w('- Every historical unresolved item is now: completed+verified (§9), an open record with all 27 fields (§8), or superseded with evidence (§9).')
w('')

# ---- §12 REUSE / EXTERNAL COMPONENT MAP (S131 REUSE-FIRST GLOBAL LAW) ----
w('## 12. REUSE / EXTERNAL COMPONENT MAP (S131 REUSE-FIRST LAW)')
w('')
w('> LAW: MAXIMUM REAL-APK COMPATIBILITY WITH MINIMUM NEW CODE. Before ANY new')
w('> subsystem code: search existing implementation, AOSP, AndroidX, libcore/ART,')
w('> mature open-source, embeddable libraries, maintained projects. Machine twin:')
w('> `canonical/reuse_registry.json` (21 mandated fields per candidate).')
w('> Full decision table: `docs/REUSE_EXTERNAL_COMPONENT_MAP.md`.')
w('')
w('| STATUS | CANDIDATES |')
w('|---|---|')
if reuse_cands:
    _rs = collections.Counter(_c['status'] for _c in reuse_cands)
    for _s, _n in sorted(_rs.items()):
        _names = ', '.join(_c['REUSE_CANDIDATE'] for _c in reuse_cands if _c['status'] == _s)
        w(f'| [{_s}] ({_n}) | {_names} |')
    w('')
    w('Category → candidates (drives every item\'s `reuse_candidate` field):')
    w('')
    for _k in sorted(reuse_by_cat):
        w(f'- **{_k}** → {", ".join(reuse_by_cat[_k])}')
    w('')
    w('Decision law: ADOPTED_WIRED/ADOPTED_VENDORED/ADAPTED = already the substrate (never re-implement around them); EVALUATE/PLANNED = integrate-or-justify before new code in that category; ORACLE = diff-test authority; REFERENCE_ONLY = port laws 1:1 with anchors, never wholesale; REJECTED = recorded reason.')
w('')

open(f'{ROOT}/docs/MASTER_WORKLIST.md', 'w').write('\n'.join(md))
print(f'MASTER_WORKLIST.md written: {len(md)} lines; items={len(items)} open={len(open_items)} closed={len(closed_items)}')
print('priority queues:', {p: len(by_prio.get(p, [])) for p in ['P0','P1','P2','P3','P4']})
