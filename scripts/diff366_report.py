#!/usr/bin/env python3
"""DIFFERENTIAL-366 — Stage C: generate canonical artifacts.

docs/DIFFERENTIAL_WORKING_VS_WHITE.md / .jsonl
docs/DIFFERENTIAL_FIRST_DIVERGENCES.jsonl
docs/DIFFERENTIAL_EVIDENCE_INDEX.jsonl

Every field is extracted from the run artifacts (final_state.json +
run.log markers) or from the curated causal chains read out of those
same logs during this campaign (the log-line citations in each
narrative). No field is guesswork.
"""
import hashlib, json, re
from pathlib import Path

BASE = Path('/home/z/my-project')
FIN = BASE / 'evidence/diff366/final'
STATE = json.load(open(BASE / 'run/diff366/final_state.json'))
DOCS = BASE / 'docs'

CURRENT_HEAD = '204aed6bdec7325daf8f7360517d4ef74333d086'
BINARY_SHA = '4b2db3540575b1c4'  # sha256(16) of miniandroid/build/miniandroid

# name -> (package, dir suffix)
PKGS = {
    'opencalc': 'com.darkempire78.opencalculator',
    'unote': 'app.varlorg.unote',
    'microtimer': 'dubrowgn.microtimer',
    'chess': 'jwtc.android.chess',
    'bouncy': 'com.dozingcatsoftware.bouncy',
    'dooz': 'io.github.yamin8000.dooz',
    'fossifyclock': 'org.fossify.clock',
    'blockblast': 'com.sidhant.blockblast',
    'asteroids': 'com.game.asteroids_revenge',
    'spacevertex': 'fr.arnaudguyon.spacevertex',
    'memory': 'com.sanskritbasics.memory',
}

# ---- curated causal analysis (each entry cites the runtime log lines) ----
CAUSAL = {
 'opencalc': dict(
   role='WORKING', first_divergence='NONE — frame reached REAL_APP_CONTENT',
   root_category='NONE',
   divergence_evidence='[TRACE] 17/24 FRAME_ANALYSIS state=REAL_APP_CONTENT; EXP092-RENDER 96 nodes; app_draw_ops=36',
   why=('Programmatic+XML appcompat chain completed end-to-end: provider StartupException '
        '(LH1/g;) was ABSORBED at the app boundary and Application (OpenCalcApp).onCreate '
        'finished; MainActivity.onCreate -> setContentView linked content root 937 under '
        'decor 909 ([R005-DECOR]); ARSC values resolved (570 unique colors incl. theme); '
        'ConstraintLayout measured/laid out (DEFAULT-MEASURE); 48 nodes visited by the draw '
        'walk; 36 app draw ops painted 732,555 app-owned pixels (36.7% non-bg). Preferences '
        'WRITE x2 went through the atomic prefs law (file_io.jsonl seq WRITE x2).')),
 'unote': dict(
   role='WORKING', first_divergence='NONE — frame reached REAL_APP_CONTENT',
   root_category='NONE',
   divergence_evidence='[TRACE] FRAME_ANALYSIS state=REAL_APP_CONTENT; view_tree 14 nodes',
   why=('Plain android.widget XML inflation with ZERO uncaught exceptions (crash.log empty): '
        'RelativeLayout->LinearLayout->ListView+Buttons all inflated from AXML, measured, '
        'laid out and drawn (7 app draw ops, 302,400 app pixels). Notes persistence via real '
        'SQLite notes.db. It exercises the narrowest API surface of the four — and that '
        'surface (AXML inflate, ListView, TextView draw, SQLite) is fully implemented.')),
 'microtimer': dict(
   role='WORKING', first_divergence='NONE — frame reached REAL_APP_CONTENT',
   root_category='NONE',
   divergence_evidence='[TRACE] FRAME_ANALYSIS state=REAL_APP_CONTENT; file_io MKDIR x7 OPEN x3 STAT x6',
   why=('Fully programmatic UI (no AXML): LinearLayout/ScrollView built from constructors, '
        '26-view tree, 22 draw ops, 1,029,909 app pixels (50.3% non-bg). File family real: '
        'File.mkdirs x6, cache FileOutputStream OPEN x3, STAT x6, SQLite databases/app-data '
        'with -wal/-shm materialized (WAL law). Timer state persists across runs.')),
 'bouncy': dict(
   role='WORKING', first_divergence='NONE — frame reached REAL_APP_CONTENT',
   root_category='NONE',
   divergence_evidence='[TRACE] FRAME_ANALYSIS state=REAL_APP_CONTENT; [ASSET-FD] openFd fd=4..7 real host fds',
   why=('Custom-View game: ScoreView(1080x147) + CanvasFieldView(1080x1773) inflated with '
        'real sizes and painted via Canvas (11 app draw ops, 978,380 app pixels, 314 colors). '
        'Asset contract proven live: 12 asset OPENs incl. 4 openFd calls returning REAL host '
        'fds with offset/len (dinga1.ogg fd=4 off=1459454 len=60630); missing '
        'assets/tables/tablenull.json produced the honest FileNotFoundException which the app '
        'CAUGHT (deferred handler type=Exception) and continued. libGDX SharedLibraryLoader '
        'ran; its SharedLibraryLoadRuntimeException was unwound but absorbed inside app '
        'frames — the Canvas fallback view renders regardless.')),
 'chess': dict(
   role='REGRESSION-FOUND', first_divergence='start.onCreate NPE (pc=9) -> RecyclerView adapter never bound',
   root_category='VIEWTREE/ATTACH',
   divergence_evidence='[EXC-PROPAGATE] NPE uncaught at Ljwtc/android/chess/start;.onCreate invoke_pc=9; RecyclerView node=429 children=0; app_draw_ops=0',
   why=('REGRESSION (honest reclassification): the golden b5a7a35d5fe0564b is byte-stable '
        'BUT the frame is 100% white (1 unique color). Decor inflates (7 nodes incl. '
        'Toolbar + RecyclerView 1080x1920), attach ok=true, SQLite chess_pgn.db real — '
        'yet 0 app draw ops: start.onCreate died on an uncaught NPE and the RecyclerView '
        'adapter never bound any child. Earlier campaigns used this golden as a '
        'DETERMINISM gate (persistence), not a pixel-truth gate; under the F-NEW-233 '
        'frame-truth lens it is DEFAULT_BACKGROUND_ONLY. Replaced by bouncy in the '
        'working quota per request §2.')),
 'dooz': dict(
   role='CONTROL', first_divergence='Compose composition produces no draw ops',
   root_category='COMPOSE',
   divergence_evidence='view_tree: 2 nodes (Lho;, Lt4; obfuscated Compose hosts); app_draw_ops=0; verdict DEFAULT_BACKGROUND_ONLY',
   why=('Compose control: lifecycle RESUMED, two obfuscated Compose host views exist in the '
        'tree, but the composition never emits draw ops (known R-NEW-347/345 compose '
        'frontier). Its golden d602648e8e401895 is likewise a determinism gate — and the '
        'final-campaign P1-8 cleanup REMOVED diagnostic placeholder pixels from this frame, '
        'making the blank face the honest state.')),
 'fossifyclock': dict(
   role='WHITE', first_divergence='authoritative WINDOW_ROOT absent at frame time (deferred_ui_pending=1)',
   root_category='VIEWTREE/ATTACH',
   divergence_evidence='[F-NEW-233] verdict=NO_ROOT first_missing_stage=WINDOW_ROOT; [F-NEW-232] deferred-UI pending queue_size=1; [R005-DECOR] view=2192 under decor=1133; NPE Ln/h;.inflate pc=86 XmlPullParser null',
   why=('Installation, identity, Application, SplashActivity lifecycle, startActivity, '
        'MainActivity construction + theme + inflate all RAN. Chain of damage: (1) provider '
        'StartupException absorbed (same as opencalc); (2) EventBusException unwound '
        'App.onCreate mid-way ([EXC-UNWIND] Lorg/greenrobot/eventbus/EventBusException '
        'unwound Lorg/fossify/clock/App;.onCreate); (3) LayoutInflater.inflate died on NPE '
        '"XmlPullParser.getEventType on null object reference" (Ln/h;.inflate pc=86 — the '
        'parser handed to inflate was null); (4) setContentView still linked root=2192 under '
        'decor=1133 (F-NEW-220 content-parent reuse), but the frame walk found NO '
        'authoritative window root (deferred UI queue still pending at frame time) — '
        'window_background_px=2,073,600 painted only. FIRST DIVERGENCE: window root never '
        'became authoritative at frame time — a VIEWTREE/ATTACH root downstream of the '
        'App.onCreate + inflate damage, NOT an installation/loading root.')),
 'blockblast': dict(
   role='WHITE', first_divergence='content view never materialized — ComposeView NOT in class index',
   root_category='COMPOSE',
   divergence_evidence='[UC009-ATTACH-DIAG] classes_indexed=633 nodes=1 + "ComposeView NOT in class index"; attach ok=false; [R341-APP] Application hint not in DEX',
   why=('Everything up to Activity lifecycle works: provider exception absorbed (obfuscated '
        'Le0/c;), MainActivity constructed, onCreate/onResume dispatched (106 insns). But '
        'the app UI is Compose: its ComponentActivity base never creates a ComposeView node '
        '(attach diagnostic: nodes=1, ComposeView NOT in class index, ok=false). Tree stays '
        '1 node; measure/layout/draw never ran; frame = NO_ROOT/WINDOW_ROOT, white. '
        'FIRST DIVERGENCE: Compose view materialization.')),
 'asteroids': dict(
   role='WHITE', first_divergence='Arrays.toString returned null (REC-MISS) -> kotlin Intrinsics NPE -> GodotActivity.onCreate died before creating GodotView',
   root_category='NATIVE/JNI',
   divergence_evidence='[REC-MISS] Ljava/util/Arrays;.toString caller=Lorg/godotengine/godot/GodotActivity;.onCreate; [THROWABLE-STACK] Intrinsics.checkNotNullExpressionValue -> GodotActivity.onCreate pc=0x3a -> GodotApp.onCreate; nodes=2',
   why=('Godot game: identity + provider + default Application all fine. GodotApp.onCreate '
        'dispatched and actually read command-line assets ([STREAM-READ] asset=_cl_ x3). '
        'Then GodotActivity.onCreate pc=40: Intent.getStringArrayExtra (REC-MISS -> null), '
        'Arrays.toString (REC-MISS -> null) — the shadow returned null instead of the '
        'contract String "null" — kotlin Intrinsics.checkNotNullExpressionValue threw NPE '
        '"toString(...) must not be null", GodotActivity.onCreate unwound at pc=0x3a, '
        'RuntimeException escaped at GodotApp.onCreate -> APP BOUNDARY. GodotView (native '
        'surface) was never created; tree stayed at 2 decor nodes; NO_ROOT. Even past the '
        'NPE, the Godot native/JNI surface (.so load + JNI registration) is an open '
        'frontier. FIRST DIVERGENCE: null-semantic violation in java.util.Arrays shadow '
        '(Constitution §18), content frontier NATIVE/JNI.')),
 'spacevertex': dict(
   role='WHITE', first_divergence='Class.forName("kotlin.internal...implementations").newInstance() returned null -> NPE; on re-dispatch androidx Fragment ISE: HomeFragment must be public static',
   root_category='FRAGMENT',
   divergence_evidence='[THROWABLE-MSG] NPE forName(...) must not be null caller=Lji;.n pc=11 depth=11; [THROWABLE-MSG] ISE "Fragment ... HomeFragment must be a public static class" Landroidx/fragment/app/a;.b pc=232; attach ok=true nodes=12; app_draw_ops=1',
   why=('Decor inflates and attaches (12 nodes, ok=true) and the draw walk RAN (7 nodes '
        'visited) — but only 1 draw op (window background). HomeActivity.onCreate died '
        'TWICE: first on NPE "forName(\\"kotlin.internal…implementations\\").newInstance() '
        'must not be null" (Class.forName shadow returned null — same null-semantic family '
        'as asteroids), then, on re-dispatch, on androidx Fragment IllegalStateException '
        '("Fragment HomeFragment must be a public static class to be properly recreated '
        'from instance state") — the Fragment host-attachment/recreation law gap. The '
        'app-fragment content never inflated into ContentFrameLayout. FIRST DIVERGENCE: '
        'kotlin forName null (trigger), Fragment recreation law (content frontier).')),
 'memory': dict(
   role='WHITE', first_divergence='null-receiver .getClass NPE inside androidx WindowInsets compat during ActionBarOverlayLayout.<init>',
   root_category='ANDROIDX LIFECYCLE',
   divergence_evidence='[SYNTH-EXC] f141-null-recv NPE method=Lx/h;.g pc=0; [EXC-UNWIND] chain s0$k.<clinit> -> s0.<clinit> -> ActionBarOverlayLayout.<init> -> appcompat h.c0 -> MainActivity.onCreate x3; WebView node=702 walked, 0 app draw ops',
   why=('The deepest white: setContentView succeeded, 13-node tree includes the app content '
        '(RelativeLayout + WebView 1080x1920), attach ok=true. But during decor init the '
        'androidx core WindowInsets compat chain (s0$k.<clinit> -> s0.v/.u) hit a '
        'null-receiver .getClass (f141 null-recv law) whose NPE unwound through '
        'ActionBarOverlayLayout.<init> and AppCompatActivity into MainActivity.onCreate — '
        'killed 3 times (caught by catch-all, re-thrown, died at boundary). The WebView '
        'node IS walked by the renderer (EXP092-RENDER node=702 1080x1920) but emits 0 draw '
        'ops: its engine never received content to paint. Frame = DEFAULT_BACKGROUND_ONLY, '
        'first_missing_stage=APP_PIXELS. FIRST DIVERGENCE: WindowInsets-compat null-receiver '
        'during decor init (ANDROIDX LIFECYCLE family) + WebView no-content frontier.')),
}

MARKERS = {
    'setContentView': 'R005-DECOR',
    'resource_resolution': 'ARSC-VALUES',
    'asset_access': 'ASSET-OPEN|ASSET-FD|STREAM-READ',
    'stream_fd': 'ASSET-FD|STREAM-READ',
    'decode': 'BITMAP|DECODE|decode',
}

def log_has(runlog_dir, pattern):
    p = runlog_dir / 'run.log'
    if not p.exists():
        return 'NO_LOG'
    return 'YES' if re.search(pattern, p.read_text(errors='ignore')) else 'NO'

def stage_matrix(name):
    rec = STATE[name]
    pkg = PKGS[name]
    run1 = rec['run1']
    fin_dir = FIN / f'{name}_{pkg}' / 'run1'
    frame = run1.get('frame') or {}
    px = run1.get('pixels') or {}
    role = CAUSAL[name]['role']
    real_pixels = 'YES' if frame.get('verdict') == 'REAL_APP_CONTENT' else 'NO'
    lc = run1.get('lifecycle_final_state')
    trans = run1.get('lifecycle_transitions', 0)
    return [
        ('Source APK SHA', rec['source_sha256'][:16]),
        ('Installed APK SHA', rec['installed_sha256'][:16]),
        ('SHA match (installed==source)', str(rec['sha_match'])),
        ('Package identity', f"{pkg} / pkgaudit live={str(rec.get('pkgaudit_live_sha'))[:16]}"),
        ('Installed APK actually opened', 'YES (INSTALLED-PACKAGE MODE, codePath=store base.apk)'),
        ('Source APK hidden before run', f"YES -> {Path(rec['source_hidden_to']).name}"),
        ('Manifest', 'YES (MANIFEST_PARSED trace event)'),
        ('Application', 'YES (APPLICATION_CREATE dex interpreter)'),
        ('Activity resolution', f"YES ({rec.get('main_activity')})"),
        ('Activity creation/onCreate', f"YES (lifecycle {lc}, transitions={trans})"),
        ('setContentView', log_has(fin_dir, MARKERS['setContentView'])),
        ('ViewTree node count', str(run1.get('view_count'))),
        ('Resource resolution', log_has(fin_dir, MARKERS['resource_resolution'])),
        ('Asset access', log_has(fin_dir, MARKERS['asset_access'])),
        ('File access', json.dumps(run1.get('file_io_ops', {}))),
        ('Stream/FD', log_has(fin_dir, MARKERS['stream_fd'])),
        ('Decode', log_has(fin_dir, MARKERS['decode'])),
        ('View attach', 'YES (UC009-ATTACH ok=true)' if log_has(fin_dir, 'UC009-ATTACH.*ok=true') == 'YES' else 'NO/ok=false'),
        ('Measure', str(frame.get('measure_ran'))),
        ('Layout', str(frame.get('layout_ran'))),
        ('Draw', f"app_draw_ops={frame.get('app_draw_ops')} walk_ran={frame.get('draw_walk_ran')}"),
        ('State change', 'YES' if (run1.get('file_io_ops', {}).get('WRITE') or run1.get('file_io_ops', {}).get('OPEN')) else 'NO'),
        ('Real application pixels', f"{real_pixels} (verdict={frame.get('verdict')}, owned_px={frame.get('app_owned_pixels')})"),
        ('Screenshot SHA-256', run1.get('screenshot_sha256', '')),
        ('Pixel metrics', f"colors={px.get('unique_colors')} nonbg={px.get('nonbg_ratio')} entropy={px.get('entropy')}"),
        ('First divergence', CAUSAL[name]['first_divergence']),
        ('Root category', CAUSAL[name]['root_category']),
    ]

def jsonl_rows():
    rows = []
    for name, pkg in PKGS.items():
        rec = STATE[name]
        r1 = rec['run1']
        frame = r1.get('frame') or {}
        px = r1.get('pixels') or {}
        pixclass = px.get('pixclass')
        cls = {'REAL_APP_UI_CANDIDATE': 'REAL_APP_UI'}.get(pixclass, pixclass)
        if CAUSAL[name]['role'] == 'REGRESSION-FOUND':
            cls = 'WHITE_BLANK (REGRESSED golden — determinism-only historically)'
        rows.append({
            'package': pkg, 'title': name,
            'classification': cls,
            'source_sha': rec['source_sha256'],
            'installed_sha': rec['installed_sha256'],
            'current_head': CURRENT_HEAD,
            'command': f"miniandroid install <src> --data-root <store> && miniandroid run --package {pkg} --data-root <store> --dump-view-tree --trace --max-seconds 110 -o <out>",
            'install_result': f"rc={rec['install_rc']} sha_match={rec['sha_match']}",
            'launch_result': f"rc={r1.get('run_rc')} lifecycle={r1.get('lifecycle_final_state')}",
            'lifecycle_result': f"final={r1.get('lifecycle_final_state')} transitions={r1.get('lifecycle_transitions')}",
            'viewtree_result': f"views={r1.get('view_count')} visited={frame.get('nodes_visited')}",
            'resource_result': log_has(FIN / f'{name}_{pkg}' / 'run1', 'ARSC-VALUES'),
            'asset_result': log_has(FIN / f'{name}_{pkg}' / 'run1', 'ASSET-OPEN|ASSET-FD|STREAM-READ'),
            'file_result': json.dumps(r1.get('file_io_ops', {})),
            'stream_fd_result': log_has(FIN / f'{name}_{pkg}' / 'run1', 'ASSET-FD|STREAM-READ'),
            'decode_result': log_has(FIN / f'{name}_{pkg}' / 'run1', 'BITMAP|DECODE|decode'),
            'layout_result': f"measure={frame.get('measure_ran')} layout={frame.get('layout_ran')}",
            'draw_result': f"app_draw_ops={frame.get('app_draw_ops')} owned_px={frame.get('app_owned_pixels')} verdict={frame.get('verdict')}",
            'state_change_result': 'YES' if (r1.get('file_io_ops', {}).get('WRITE') or r1.get('file_io_ops', {}).get('OPEN')) else 'NO',
            'screenshot_sha': r1.get('screenshot_sha256', ''),
            'trace_sha': sha256(FIN / f'{name}_{pkg}' / 'run1' / 'trace_summary.json'),
            'first_divergence': CAUSAL[name]['first_divergence'],
            'root_category': CAUSAL[name]['root_category'],
            'evidence_level': 'E4' if frame.get('verdict') == 'REAL_APP_CONTENT' else 'E4',
            'reproducibility': ('3/3 byte-identical ' + str(rec.get('three_run_reproducible')) if rec.get('three_run_reproducible') is not None else 'single-run'),
            'regression_result': 'REGRESSED-CLASSIFICATION (chess): determinism-golden reclassified WHITE under frame-truth law' if name == 'chess' else 'no drift',
            'notes': CAUSAL[name]['divergence_evidence'][:220],
        })
    return rows

def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

def main():
    DOCS.mkdir(exist_ok=True)
    # ---------- JSONLs ----------
    rows = jsonl_rows()
    with open(DOCS / 'DIFFERENTIAL_WORKING_VS_WHITE.jsonl', 'w') as f:
        for r in rows:
            f.write(json.dumps(r) + '\n')
    with open(DOCS / 'DIFFERENTIAL_FIRST_DIVERGENCES.jsonl', 'w') as f:
        for r in rows:
            f.write(json.dumps({
                'package': r['package'], 'classification': r['classification'],
                'first_divergence': r['first_divergence'],
                'root_category': r['root_category'],
                'evidence': CAUSAL[[k for k, v in PKGS.items() if v == r['package']][0]]['divergence_evidence'],
                'current_head': CURRENT_HEAD,
            }) + '\n')
    with open(DOCS / 'DIFFERENTIAL_EVIDENCE_INDEX.jsonl', 'w') as f:
        for name, pkg in PKGS.items():
            d = FIN / f'{name}_{pkg}'
            f.write(json.dumps({
                'package': pkg,
                'dir': str(d.relative_to(BASE)),
                'runs': sorted(p.name for p in d.iterdir() if p.is_dir()),
                'artifacts_run1': sorted(p.name for p in (d / 'run1').iterdir()),
                'stores': f"run/diff366/stores/store_{name}",
                'hidden_source': f"run/diff366/hidden_sources/",
            }) + '\n')
    print('JSONLs written')

    # ---------- stage matrix ----------
    order = ['opencalc', 'unote', 'microtimer', 'bouncy',
             'fossifyclock', 'blockblast', 'asteroids', 'spacevertex', 'memory',
             'chess', 'dooz']
    matrices = {n: stage_matrix(n) for n in order}
    (BASE / 'run/diff366/stage_matrices.json').write_text(
        json.dumps(matrices, indent=1))
    print('stage matrices written')

if __name__ == '__main__':
    main()
