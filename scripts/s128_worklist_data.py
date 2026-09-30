#!/usr/bin/env python3
"""S128 MASTER WORKLIST data assembly.
Builds the canonical item list from: root_registry.json (421 roots), capability_registry,
app_registry, game_registry, mandated campaign items. Deduplicates and classifies every
item into the 127-category taxonomy (s128_master_categories). Computes fan-out, pipeline
node, affected caps/APKs. Emits `worklist` dict consumed by the renderer."""
import json, re, os, sys, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s128_master_categories import CATEGORIES, NODE_CATS, classify

ROOT = '/home/z/my-project'

STATUS_MAP = {
    'ROOT-CAUSED-CLOSED': 'VERIFIED_3RUN',
    'VERIFIED-FIXED': 'VERIFIED', 'ROOT-CAUSED-FIXED': 'VERIFIED', 'ROOT_CAUSED-FIXED': 'VERIFIED',
    'VERIFIED-CORRECT': 'VERIFIED', 'PROVEN-FIXED': 'VERIFIED', 'FIXED-VERIFIED': 'VERIFIED',
    'FIXED-S75': 'VERIFIED', 'ROOT-CAUSED-SEMANTIC': 'VERIFIED',
    'ROOT-CAUSED-REMEASURED-GENERIC-OK': 'VERIFIED',
    'NOT-APPLICABLE': 'SUPERSEDED', 'SUPERSEDED-BY-EVIDENCE': 'SUPERSEDED',
    'IMPLEMENTED+TESTED': 'TESTED', 'USED_BY_EXECUTION': 'TESTED',
    'IMPLEMENTED': 'IMPLEMENTED', 'OBSERVED-FAIL': 'OBSERVED',
    'PARTIAL': 'PARTIAL', 'PARTIAL-FIX': 'PARTIAL',
    'UNPROVEN': 'PENDING', 'RESEARCHED-NOT-IMPLEMENTED': 'PENDING',
    'OPEN': 'PENDING', 'REGISTERED': 'PENDING',
}
PRIO_FANOUT = {'P0': 'P0-ARCHITECTURAL', 'P1': 'P1-MAJOR', 'P2': 'P2-MEDIUM', 'P3': 'P3-LOCAL'}
VISUAL_NODES = {'THEME','RESOURCES','VIEWTREE','LAYOUT','TEXT','IMAGES','DRAWABLE','CANVAS',
                'SURFACE','FRAMEBUFFER','SCREENSHOT','INPUT','STATE','REDRAW'}
CAT_DEFAULT_APKS = {
    119: 'Telegram 12.10.1 (APP-012); Forkgram (#355)', 120: 'WhatsApp 2.26.38.74 (APP-013)',
    99: 'dooz v23 (GAME-091); compose corpus', 98: 'WebView/HTML5 targets (#353 Breakout)',
    113: 'FlappyCow (GAME-024); Telegram; WhatsApp', 118: 'Surge (GAME-047); TheXTech (GAME-048)',
    114: 'libGDX titles (F-144 family)', 121: '200-title corpus + 114-stage battery',
    122: 'Telegram (grey); WhatsApp (b/w); Flashlight; dooz v23 (blank)',
    104: 'uNote (APP-002); notes apps', 29: 'Simple Stopwatch (APP-004)',
    116: 'autoplay-driven games', 115: 'SurfaceView games',
}
TEST_PLAN_STD = ('reproducer run + fan-out wave (2 unrelated APK + 2 unrelated games) + battery gate + '
                 'golden ladder G0-G11 + 3-run byte-identical SHA when visual')

def build():
    caps_reg = json.load(open(f'{ROOT}/canonical/capability_registry.json'))
    caps = caps_reg['capabilities']
    roots = json.load(open(f'{ROOT}/root_registry.json'))['roots']
    apps = json.load(open(f'{ROOT}/canonical/app_registry.json'))['apps']
    games = json.load(open(f'{ROOT}/canonical/game_registry.json'))['games']

    # ---- classify capabilities into categories ----
    cap_cat = {}
    for c in caps:
        n = classify(f"{c.get('name','')} {c.get('id','')} {c.get('layer','')}")
        cap_cat[c['id']] = n
    cat_caps = {}
    for cid, n in cap_cat.items():
        cat_caps.setdefault(n, []).append(cid)

    # ---- items from roots ----
    items = []
    unclassified = []

    # pass 1: classify every root
    raw = []
    for r in roots:
        title = r.get('title') or (r.get('evidence') or '')[:130] or (r.get('missing') or '')[:130] or '(untitled registry entry)'
        blob = f"{title} {r.get('evidence','')} {r.get('missing','')} {r.get('next','')}"
        raw.append((r, str(title).strip(), classify(blob)))

    # pass 2: terse 'same as NNN' / 'see NNN' / bare 'same' entries inherit the referenced root's category
    ref_re = re.compile(r'(?:same as|see|with|via|partial via)\s*(?:R-NEW-)?0*(\d{1,3})\b', re.I)
    def find_cat(idx):
        r, title, cat = raw[idx]
        if cat is not None: return cat
        m = ref_re.search(f"{r.get('evidence','')} {r.get('next','')}")
        if m:
            ref_id = f"R-NEW-{int(m.group(1)):03d}"
            for j, (r2, t2, c2) in enumerate(raw):
                if r2['id'] == ref_id:
                    c = find_cat(j)
                    if c is not None: return c
                    break
        for j in range(idx - 1, -1, -1):          # nearest-lower inheritance fallback
            if raw[j][2] is not None: return raw[j][2]
        return None

    for idx, (r, title, cat0) in enumerate(raw):
        st = STATUS_MAP.get(r.get('status', '?'), 'PENDING')
        cat = find_cat(idx)
        if cat is None:
            unclassified.append(r['id'])
            cat_name, sub, layer, aosp, impl = 'UNCLASSIFIED (reconcile queue)', 'INFRA', 'APK', '-', '-'
            catn = None
        else:
            c = next(x for x in CATEGORIES if x[0] == cat)
            catn, cat_name, sub, layer = c[0], c[1], c[2], c[3]
            aosp, impl = c[5], c[6]
        node = layer
        deps = sorted(set(re.findall(r'R-NEW-\d+', f"{r.get('missing','')} {r.get('next','')}")))
        prio = r.get('priority', 'P3') if r.get('priority', 'P3') in PRIO_FANOUT else 'P3'
        fanout = PRIO_FANOUT[prio]
        ncaps = len(cat_caps.get(catn, [])) if catn else 0
        fanout += f' ({len(cat_caps.get(catn, []))} caps in category)' if catn and ncaps else ''
        visual = 'YES' if (r.get('fg') or node in VISUAL_NODES) else 'INDIRECT'
        items.append({
            'id': r['id'], 'title': title.strip(), 'category': f'MC-{catn:03d} {cat_name}' if catn else 'MC-000 UNCLASSIFIED',
            'category_num': catn, 'subsystem': sub, 'layer': node,
            'current_status': r.get('status', '?'), 'root_cause': str(r.get('evidence') or '-')[:400],
            'exists': (f"law/fix committed {r.get('commit','-')}" if st in ('VERIFIED','VERIFIED_3RUN','TESTED','IMPLEMENTED') else str(r.get('evidence') or '-')[:200]),
            'missing': r.get('missing') or '-', 'dependencies': ', '.join(deps) if deps else '-',
            'fanout': fanout, 'visual_impact': visual,
            'affected_apks': r.get('app') or CAT_DEFAULT_APKS.get(catn, 'corpus class'),
            'affected_caps': ', '.join(cat_caps.get(catn, [])[:8]) or '-',
            'source_law': str(r.get('evidence') or '-')[:200],
            'aosp_ref': aosp, 'mature_impl': impl,
            'reuse': f'HIGH - reuse {impl}' if impl and impl != '-' else 'project law (no external impl needed)',
            'plan': r.get('next') or 'on demand', 'test_plan': TEST_PLAN_STD,
            'regressions': 'battery 114-stage gate + golden ladder G0-G11 + affected titles',
            'evidence': r.get('commit') or '-', 'blocker': '-',
            'next': r.get('next') or 'on demand', 'status': st,
        })

    # ---- items from ALL capabilities (nothing may disappear from the list;
    # status upgrades change the record, they never remove it) ----
    for c in caps:
        cst = c.get('status')
        if cst == 'PENDING':
            root_cause = 'capability never implemented (source-grep only seed)'
            missing = c.get('name', '?') + ' implementation + runtime evidence'
            exists = f"tracked in capability registry since S125 ({c.get('evidence','-')})"
        else:
            root_cause = f'capability at {cst} level (evidence-gated, SS2 ceiling law)'
            missing = {'TESTED': 'real-APK fan-out + 3-run reproducibility for VERIFIED',
                       'IMPLEMENTED': 'runtime evidence (TESTED tier requires real-APK proof)',
                       'VERIFIED': 'regression watch only',
                       'TESTED_X': ''}.get(cst, 'next evidence tier')
            exists = f"evidence: {'; '.join(c.get('evidence', [])) if isinstance(c.get('evidence'), list) else c.get('evidence','-')}"[:280]
        cat = cap_cat.get(c['id'])
        if cat:
            cc = next(x for x in CATEGORIES if x[0] == cat)
            cat_name, sub, layer, aosp, impl = cc[1], cc[2], cc[3], cc[5], cc[6]
            catn = cat
        else:
            catn, cat_name, sub, layer, aosp, impl = None, 'UNCLASSIFIED (reconcile queue)', 'INFRA', 'APK', '-', '-'
        node = c.get('layer', layer)
        items.append({
            'id': c['id'], 'title': f"Capability [{cst}]: {c.get('name','?')}",
            'category': f'MC-{catn:03d} {cat_name}' if catn else 'MC-000 UNCLASSIFIED',
            'category_num': catn, 'subsystem': sub, 'layer': layer,
            'current_status': cst, 'root_cause': root_cause,
            'exists': exists,
            'missing': missing,
            'dependencies': '-', 'fanout': 'P1-MAJOR (layer gap)' if cst == 'PENDING' else 'tier upgrade path',
            'visual_impact': 'YES' if layer in VISUAL_NODES else 'INDIRECT',
            'affected_apks': CAT_DEFAULT_APKS.get(catn, 'layer-wide corpus'),
            'affected_caps': c['id'], 'source_law': 'capability seed law (grep hits max out at IMPLEMENTED)',
            'aosp_ref': aosp, 'mature_impl': impl,
            'reuse': f'HIGH - reuse {impl}' if impl and impl != '-' else 'project law',
            'plan': (f"TOOL-FIRST: reuse {impl or 'AOSP'}; implement missing piece; add unit+control+real-APK evidence"
                     if cst == 'PENDING' else 'advance evidence tier per SS2 law; regression watch'),
            'test_plan': TEST_PLAN_STD, 'regressions': 'battery gate + golden ladder',
            'evidence': '-', 'blocker': '-', 'next': 'implement via TOOL-FIRST reuse path' if cst == 'PENDING' else 'evidence-tier upgrade / regression watch',
            'status': cst,
        })

    return items, caps, apps, games, cap_cat, cat_caps, unclassified

# ---- mandated campaign items (user directives + honest frontiers) ----
MANDATED = [
 dict(id='M-01', title='INPUT layer completion: touch dispatch + gestures + focus + scrolling',
      cat='MC-053 touch dispatch', layer='INPUT', status='PARTIAL', fanout='P0-ARCHITECTURAL (highest computed fan-out) — TouchTarget + intercept DONE S128 (R-NEW-424), residuals below',
      root_cause='highest-fan-out PENDING layers computed from capability registry: INPUT 4 pending caps (onInterceptTouchEvent CAP-INPUT-100, TouchTarget CAP-INPUT-102, VelocityTracker CAP-INPUT-108, TouchDelegate CAP-INPUT-110) + SCROLLING 3 (computeScroll 126, EdgeEffect 127, nested 128)',
      missing='AOSP TouchTarget law, intercept pass, velocity tracking, edge effects',
      apks='every interactive app/game (L5 band of the whole corpus)', caps='CAP-INPUT-100/102/108/110, CAP-SCROLLING-126/127/128',
      aosp='AOSP ViewGroup.dispatchTouchEvent + TouchTarget; View.computeScroll; EdgeEffect',
      impl='AOSP View/ViewGroup source (direct law port)', plan='port TouchTarget + intercept law, then VelocityTracker/EdgeEffect; unit + control APK + real APK fan-out',
      next='CAP-INPUT-102 TouchTarget law first (blocks click routing correctness)'),
 dict(id='M-02', title='VIDEO layer: MediaCodec/MediaExtractor/video decode/Surface output',
      cat='MC-091 video', layer='SURFACE', status='PENDING', fanout='P0-ARCHITECTURAL',
      root_cause='VIDEO layer 4 pending caps; zero runtime evidence at layer level',
      missing='video decode pipeline end-to-end', apks='video-playing corpus titles',
      caps='CAP-VIDEO-170/171/172/174', aosp='AOSP MediaCodec stagefright; NDK MediaCodec',
      impl='FFmpeg (LGPL/GPL) — TOOL-FIRST law; no from-scratch codec', plan='decide FFmpeg integration (license record), wire MediaExtractor->decode->Surface output law',
      next='G-decision: FFmpeg candidate + license (report G)'),
 dict(id='M-03', title='GAME layer: lockCanvas loop + game loops + timestep + sprites',
      cat='MC-115 game loop', layer='STATE', status='PENDING', fanout='P0-ARCHITECTURAL',
      root_cause='GAME layer 4 pending caps; SurfaceView/lockCanvas loop never proven end-to-end',
      missing='CAP-GAME-177 lockCanvas loop, 178 game loops, 179 fixed/variable timestep, 180 sprites',
      apks='all SurfaceView games (65 OBSERVED corpus)', caps='CAP-GAME-177..180',
      aosp='AOSP SurfaceView + SurfaceHolder.lockCanvas; Game SDK loop patterns',
      impl='AOSP SurfaceView law (direct port)', plan='implement lockCanvas software surface loop + fixed timestep law; prove on 1 real SurfaceView game then fan out',
      next='CAP-GAME-177 lockCanvas loop'),
 dict(id='M-04', title='S68 default-theme law: manifest-theme-less APKs get platform default',
      cat='MC-011 Theme', layer='THEME', status='PENDING', fanout='P1-MAJOR',
      root_cause='uNote-class APKs without android:theme must resolve the platform default theme chain',
      missing='default theme selection + framework bag application when manifest has no theme',
      apks='uNote (APP-002) and all theme-less APKs', caps='CAP-RESOURCES theme family',
      aosp='AOSP Themes.java device-default + PhoneWindow constructor default',
      impl='AOSP PhoneWindow/Themes', plan='implement default-theme law; A/B uNote before/after; battery gate',
      next='implement + uNote visual A/B'),
 dict(id='M-05', title='Per-activity themes (SplashTheme vs AppTheme)',
      cat='MC-011 Theme', layer='THEME', status='PENDING', fanout='P1-MAJOR',
      root_cause='activity-level android:theme overrides application theme; currently partial',
      missing='per-activity theme overlay switching at activity bind', apks='OpenSudoku (APP-011) SplashTheme; corpus-wide',
      caps='CAP-RESOURCES-0xx theme override family', aosp='AOSP ActivityThread performLaunchActivity theme attach + AttachInfo',
      impl='AOSP ActivityThread', plan='resolve activity theme at launch; splash->main switch visual test on sudoku',
      next='sudoku splash A/B'),
 dict(id='M-06', title='Compose render cluster: MonotonicFrameClock + composition render + ComposeView 0->N',
      cat='MC-099 Compose', layer='REDRAW', status='PENDING', fanout='P0-ARCHITECTURAL',
      root_cause='dooz v23 blank first frame; cluster R-NEW-246/256/259/279/285 (+242/261) all hang on R-NEW-294 (MonotonicFrameClock fold) then R-NEW-295 (composition render)',
      missing='frame clock -> recomposition -> pixel path', apks='dooz v23 (GAME-091); compose corpus family',
      caps='CAP-UI compose family', aosp='androidx.compose.runtime Recomposer + MonotonicFrameClock (upstream source)',
      impl='androidx compose runtime (upstream)', plan='close R-NEW-294 then R-NEW-295; unblock 246/279/285/256/259 chain; dooz visual proof',
      next='R-NEW-294 (MonotonicFrameClock) — the single highest-dependency node'),
 dict(id='M-07', title='Telegram 12.10.1 frontier: themed-icon SVG (SvgHelper) + gms Api builder nulls',
      cat='MC-119 Telegram frontier', layer='VIEWTREE', status='BLOCKED', fanout='P0-ARCHITECTURAL',
      root_cause='grey 3-color frame = NOT A RENDER; SvgHelper SVG rasterization + gms Api builder null returns',
      missing='SVG engine (TOOL-FIRST: rlottie/androidsvg candidate) + gms boundary stubs',
      apks='Telegram (APP-012); Forkgram (#355)', caps='MC-073 SVG; MC-113 GMS boundary',
      aosp='Telegram upstream source (github.com/DrKLO/Telegram) SvgHelper',
      impl='rlottie (tools/rlottie present) or androidsvg for SVG; microG as gms boundary reference',
      plan='TOOL-FIRST decision G: SVG engine; then gms Api builder honest stubs; keep generic laws only',
      next='SVG engine decision -> SvgHelper chain probe'),
 dict(id='M-08', title='WhatsApp 2.26.38.74 frontier: AppContext.set injection + INVOKE_RETURN null',
      cat='MC-120 WhatsApp frontier', layer='VIEWTREE', status='BLOCKED', fanout='P0-ARCHITECTURAL',
      root_cause='black/white frame = NOT A RENDER; AppContext.set static injection path + INVOKE_RETURN null propagation',
      missing='Context injection law (generic), null INVOKE_RETURN handling (generic)',
      apks='WhatsApp (APP-013)', caps='MC-028 Context',
      aosp='AOSP ContextImpl/ContextWrapper law (generic only; app is closed-source)',
      impl='AOSP ContextImpl', plan='fix the GENERIC Context-static-injection law + INVOKE_RETURN null law; WhatsApp only a witness, never a target of app-specific checks',
      next='generic Context.setApp static law + null propagation audit'),
 dict(id='M-09', title='FlappyCow gameplay past GMS frontier (bird through pipes)',
      cat='MC-113 GMS boundary', layer='STATE', status='BLOCKED', fanout='P1-MAJOR',
      root_cause='start screen VERIFIED_3RUN (13cf4746 x3, S124/S127); gameplay chain blocked by gms Api builder nulls',
      missing='gms boundary stub set + game-loop drive of Game activity', apks='FlappyCow (GAME-024)',
      caps='MC-113; MC-115 game loop', aosp='N/A (GMS is closed); microG boundary reference',
      impl='microG-pattern honest stubs', plan='after M-07 gms stub law: drive Game activity, verify bird/pipe physics via pixel state changes',
      next='gms stub set -> Game loop drive'),
 dict(id='M-10', title='Chess wave 2: jwtc.android.chess full interaction',
      cat='MC-118 complex games', layer='STATE', status='PENDING', fanout='P1-MAJOR',
      root_cause='chess (GAME-044) OBSERVED trace-only; user directive: chess + next game wave',
      missing='L4 visual + L5 input + L6 move state change', apks='jwtc chess (GAME-044)',
      caps='MC-053; MC-115', aosp='N/A app; AOSP input+view laws', impl='AOSP laws',
      plan='full-load -> board render -> legal-move drive -> HUD anchored evidence 3-run', next='board render probe'),
 dict(id='M-11', title='Calculator-class completion: OpenCalculator SlidingUpPanelLayout gravity idiom',
      cat='MC-100 AndroidX', layer='VIEWTREE', status='PARTIAL', fanout='P2-MEDIUM',
      root_cause='OpenCalculator (APP-010) PARTIAL: near-blank from SlidingUpPanelLayout gravity idiom (pre-existing, A/B proven)',
      missing='sliding-panel layout law', apks='OpenCalculator (APP-010)', caps='CAP-UI view family',
      aosp='androidx slidingpanelayout (upstream)', impl='androidx slidingpanelayout',
      plan='port gravity idiom handling; near-blank A/B re-run', next='slidingpanelayout law port'),
 dict(id='M-12', title='Corpus failure clustering: 65 OBSERVED games -> L4+ progression',
      cat='MC-121 200-title corpus', layer='SCREENSHOT', status='PENDING', fanout='P0-ARCHITECTURAL',
      root_cause='65/91 titles OBSERVED = trace-only E3, no meaningful visual proof; campaign law: corpus clustering only AFTER base integration',
      missing='per-title blank/grey/white/black clustering -> CORPUS->CLUSTER->ROOT FIX->RETEST waves',
      apks='GAME-027..090 OBSERVED family', caps='all layers', aosp='project corpus law',
      impl='project cluster tooling', plan='cluster by failure signature; each cluster -> one root fix wave; retest',
      next='cluster sweep after INPUT/GAME base (M-01/M-03) lands'),
 dict(id='M-13', title='snake_deluxe AI wall-pass driver defect (port wrap-BFS from snake_neon)',
      cat='MC-116 game input', layer='INPUT', status='PENDING', fanout='P4-APK-SPECIFIC',
      root_cause='autoplay AI passes walls; snake_neon has correct wrap-BFS port candidate',
      missing='driver fix (not a runtime law)', apks='Snake Deluxe (GAME-001)', caps='MC-116',
      aosp='N/A (project driver)', impl='in-repo snake_neon wrap-BFS',
      plan='port wrap-BFS into snake_deluxe driver; 3-run', next='port'),
 dict(id='M-14', title='tetris driver tick drift (~7 locks post-lock)',
      cat='MC-089 timing/frame scheduling', layer='STATE', status='PENDING', fanout='P4-APK-SPECIFIC',
      root_cause='driver tick drifts after locks; fixed-timestep needed', missing='driver fixed timestep',
      apks='Mini Tetris (GAME-002)', caps='MC-089/MC-115', aosp='AOSP Choreographer clock law (analogy)',
      impl='project driver', plan='fixed-timestep driver; 3-run', next='driver patch'),
 dict(id='M-15', title='2048 estimate-vs-HUD delta (HUD = sole authority)',
      cat='MC-116 game input', layer='INPUT', status='PENDING', fanout='P4-APK-SPECIFIC',
      root_cause='driver score estimate diverges from HUD; law: HUD is the only authority',
      missing='HUD-read anchoring in driver', apks='2048 (GAME-004)', caps='MC-116',
      aosp='N/A (project driver)', impl='project driver', plan='HUD OCR-anchor read; 3-run', next='driver patch'),
 dict(id='M-16', title='WebView/HTML5 engine TOOL-FIRST decision (G-report entry)',
      cat='MC-098 browser/HTML5 engine integration', layer='RUNTIME', status='PENDING', fanout='P0-ARCHITECTURAL',
      root_cause='campaign forbids writing a browser; #353 proved quickjs JS execution + real game loop; full HTML/CSS needs an upstream engine decision',
      missing='recorded decision: candidates Chromium/WebKit/Gecko/Servo/WPE vs quickjs+custom-shim scope',
      apks='WebView/HTML5 targets (#353 Breakout; mykanji; weather forecast)', caps='CAP-WEBVIEW-159 + family',
      aosp='AOSP WebView (Chromium-based) is the reference behavior',
      impl='upstream engines (integration only)', plan='write decision record G: candidates, licenses, integration cost; choose incremental path',
      next='decision record + mykanji/weather probe'),
 dict(id='M-17', title='Golden ladder G0-G11 as permanent regression suite',
      cat='MC-124 golden ladder', layer='SCREENSHOT', status='IN_PROGRESS', fanout='P0-ARCHITECTURAL',
      root_cause='campaign requires G0 Text/Button/Image/XML Drawable/Framework Drawable/Theme/ViewGroup/Canvas/SurfaceView/WebView/Complex app/Complex game ladder, forever-green on every framework change',
      missing='codified ladder runner (currently implicit battery + ad-hoc goldens)',
      apks='ladder set: calc/uNote/FlappyCow/dooz/telegram/whatsapp/battery', caps='all',
      aosp='project law', impl='existing battery + wave scripts',
      plan='codify G0-G11 runner script mapping each rung to APK+probe+assert', next='script scripts/s128_ladder.sh'),
 dict(id='M-18', title='Framework DRAWABLE files law (windowBackground selector) — S127 CLOSED state',
      cat='MC-008 Drawable resources', layer='DRAWABLE', status='VERIFIED_3RUN', fanout='CLOSED',
      root_cause='R-NEW-423 ROOT-CAUSED-CLOSED S127: compact-entry law + one derived-field law + package-routed color deref + 1120 framework res files committed',
      missing='nothing (closed with battery gate zero-FAIL)', apks='battery helloworld/EXT-01/EXT-02/M3-F012; uNote; notes',
      caps='CAP-RESOURCES drawable family', aosp='AOSP ResTable_entry::Compact (ResourceTypes.h main)',
      impl='AOSP androidfw (law port complete)', plan='n/a — regression watch',
      next='none; regression watch'),
 dict(id='M-19', title='L7 multi-feature/realistic sweep (all titles L7=False)',
      cat='MC-123 regression infrastructure', layer='SCREENSHOT', status='PENDING', fanout='P1-MAJOR',
      root_cause='every registry title has L7=False; no title carries a multi-feature realistic session proof',
      missing='per-title multi-feature session scripts + evidence', apks='all 15 apps + 91 games',
      caps='all', aosp='project checkpoint law', impl='project drivers',
      plan='roll L7 sessions into new-title waves (TriPeaks already L7=True)', next='piggyback on M-12 waves'),
 dict(id='M-20', title='Historical user batch: chess+next game, +1 game, calculator app, other app, flappy pipe game',
      cat='MC-121 200-title corpus', layer='APK', status='PENDING', fanout='P1-MAJOR',
      root_cause='standing user directives from earlier sessions (never dropped)',
      missing='per-item waves; flappy gameplay blocked by GMS (see M-09)',
      apks='chess jwtc, new titles, calculator-class, note-class, flappy', caps='all',
      aosp='N/A', impl='N/A', plan='execute as waves after M-01/M-03 unblock interaction band', next='wave scheduling'),
 dict(id='M-21', title='Flashlight SurfaceView-family blank frame',
      cat='MC-082 SurfaceView', layer='SURFACE', status='PENDING', fanout='P2-MEDIUM',
      root_cause='side observation: SurfaceView family blank (ROADMAP frontier)',
      missing='SurfaceView lockCanvas path (shared with M-03)', apks='Flashlight; SurfaceView corpus',
      caps='CAP-GAME-177', aosp='AOSP SurfaceView', impl='AOSP law',
      plan='fold into M-03 lockCanvas loop work', next='shared with M-03'),
 dict(id='M-22', title='Register unregistered validation targets in canonical registries',
      cat='MC-126 documentation/registry consistency', layer='APK', status='VERIFIED_3RUN', fanout='CLOSED (this cycle)',
      root_cause='audit finding R1: FlappyCow/GameMasterDice/Snake Neon overrides never bound (titles missing from audit source)',
      missing='nothing (fixed S128: 3 rows added, canonical regenerated 91 games)',
      apks='FlappyCow GAME-024, GameMasterDice GAME-025, Snake Neon GAME-026',
      caps='N/A', aosp='N/A', impl='N/A', plan='n/a', next='registry-repair script is idempotent'),
]

def assemble():
    items, caps, apps, games, cap_cat, cat_caps, unclassified = build()
    for m in MANDATED:
        items.append(dict(
            id=m['id'], title=m['title'], category=m['cat'], category_num=None,
            subsystem='CAMPAIGN', layer=m['layer'], current_status=m['status'],
            root_cause=m['root_cause'], exists='-', missing=m['missing'],
            dependencies='-', fanout=m['fanout'], visual_impact='YES',
            affected_apks=m['apks'], affected_caps=m['caps'], source_law='user campaign directives',
            aosp_ref=m['aosp'], mature_impl=m['impl'],
            reuse=f'HIGH - reuse {m["impl"]}' if m['impl'] not in ('N/A',) else 'N/A',
            plan=m['plan'], test_plan=TEST_PLAN_STD, regressions='battery gate + golden ladder',
            evidence='-', blocker='GMS/boundary' if m['status'] == 'BLOCKED' else '-',
            next=m['next'], status=m['status'],
        ))
    return dict(items=items, caps=caps, apps=apps, games=games, cap_cat=cap_cat,
                cat_caps=cat_caps, unclassified=unclassified)

if __name__ == '__main__':
    d = assemble()
    from collections import Counter
    st = Counter(i['status'] for i in d['items'])
    print('items:', len(d['items']), dict(st))
    print('unclassified roots:', len(d['unclassified']), d['unclassified'][:20])
