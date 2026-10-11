#!/usr/bin/env python3
# cont44_c_scan.py — CONT44-C cross-app generality audit: STATIC machinery scan.
# Corpus: upload/*.apk + upload/canonical_apks/*.apk + upload/s83_games/**/*.apk
#       + upload/s80_games/**/*.apk + tmp/cont35_apks/*.apk + tmp/com.tananaev.calculator_11.apk
# Dedupe by basename. FAST PARTIAL SCAN: per-DEX class names + superclassnames
# + string constants ONLY. NO method-body decompile.
# Output: run/cont44/machinery_matrix.tsv + machinery_matrix_raw.json
import zipfile, os, glob, json, hashlib

from loguru import logger
logger.remove()  # androguard 4.1.4 spams DEBUG per-item parse logs; silence for the batch run
from androguard.core.dex import DEX

ROOT = '/home/z/my-project'
GLOBS = [
    f'{ROOT}/upload/*.apk',
    f'{ROOT}/upload/canonical_apks/*.apk',
    f'{ROOT}/upload/s83_games/**/*.apk',
    f'{ROOT}/upload/s80_games/**/*.apk',
    f'{ROOT}/tmp/cont35_apks/*.apk',
    f'{ROOT}/tmp/com.tananaev.calculator_11.apk',
]
OUTDIR = f'{ROOT}/run/cont44'
os.makedirs(OUTDIR, exist_ok=True)

# ---- collect + dedupe by basename (first occurrence wins, deterministic order) ----
paths, seen = [], {}
for g in GLOBS:
    for p in sorted(glob.glob(g, recursive=True)):
        b = os.path.basename(p)
        if b not in seen:
            seen[b] = p
            paths.append((b, p))

MARKERS = {
    'plat_fragment':  ['Landroid/app/Fragment;', 'Landroid/app/FragmentTransaction;',
                       'Landroid/app/FragmentManager;', 'Landroid/app/ListFragment;'],
    'androidx_frag':  ['Landroidx/fragment/app/Fragment;', 'Landroidx/fragment/app/FragmentActivity;',
                       'Landroidx/fragment/app/FragmentTransaction;'],
    'pref_frag':      ['Landroid/preference/PreferenceFragment;', 'Landroid/preference/PreferenceActivity;',
                       'Landroid/preference/Preference;', 'Landroidx/preference/'],
    'appcompat':      ['Landroidx/appcompat/app/AppCompatActivity;',
                       'Landroidx/appcompat/widget/ActionBarOverlayLayout;',
                       'Landroidx/appcompat/widget/ActionBar;', 'Landroidx/appcompat/'],
    'compose':        ['Landroidx/compose/runtime/Recomposer;', 'Landroidx/compose/ui/platform/ComposeView;',
                       'Landroidx/compose/', 'Landroidx/compose/foundation/',
                       'Landroidx/compose/material/'],
    'hilt_dagger':    ['Ldagger/hilt/', 'Ldagger/internal/', 'Ldagger/',
                       'Ljavax/inject/', 'dagger.hilt.android'],
    'workmanager':    ['Landroidx/work/WorkManager;', 'Landroidx/work/', 'Landroidx/work/impl/'],
    'lifecycle':      ['Landroidx/lifecycle/LifecycleDispatcher;', 'Landroidx/lifecycle/ReportFragment;',
                       'Landroidx/lifecycle/'],
    'service':        ['Landroid/app/Service;', 'Landroid/app/IntentService;', 'Landroid/app/ForegroundService;'],
    'notification':   ['Landroid/app/Notification;', 'Landroid/app/Notification$Builder;',
                       'Landroid/app/NotificationManager;'],
    'webview':        ['Landroid/webkit/WebView;', 'Landroid/webkit/WebViewClient;'],
    'coroutines':     ['Lkotlinx/coroutines/', 'kotlinx.coroutines'],
    'recycler':       ['Landroidx/recyclerview/widget/RecyclerView;'],
    'constraint':     ['Landroidx/constraintlayout/widget/ConstraintLayout;'],
}

def is_framework_class(cn):
    return (cn.startswith('Landroid/') or cn.startswith('Landroidx/') or
            cn.startswith('Ljava/') or cn.startswith('Lkotlin') or
            cn.startswith('Lkotlinx/') or cn.startswith('Lcom/google/'))

def scan_apk(name, path):
    z = zipfile.ZipFile(path)
    dexnames = [n for n in z.namelist() if n.endswith('.dex')]
    strings_all = set()
    app_frag_sub, app_service_sub, app_view_sub, app_act_sub, app_pref_sub = set(), set(), set(), set(), set()
    nclasses = 0
    for dn in dexnames:
        d = DEX(z.read(dn))
        strings_all.update(d.get_strings())
        for c in d.get_classes():
            nclasses += 1
            cn = c.get_name() or ''
            sc = c.get_superclassname() or ''
            if not cn.startswith('L'):
                continue
            fw = is_framework_class(cn)
            if not fw:
                if 'Fragment' in sc:
                    app_frag_sub.add(f'{cn} extends {sc}')
                if sc in ('Landroid/app/Service;', 'Landroid/app/IntentService;',
                          'Landroid/app/JobService;'):
                    app_service_sub.add(f'{cn} extends {sc}')
                if sc.startswith('Landroid/view/View') or sc in (
                        'Landroid/widget/TextView;', 'Landroid/widget/ImageView;',
                        'Landroid/widget/LinearLayout;', 'Landroid/widget/FrameLayout;',
                        'Landroid/widget/RelativeLayout;', 'Landroid/view/SurfaceView;',
                        'Landroid/widget/Button;'):
                    app_view_sub.add(f'{cn} extends {sc}')
                if sc == 'Landroid/app/Activity;' or 'Activity' in sc:
                    app_act_sub.add(f'{cn} extends {sc}')
                if 'Preference' in sc:
                    app_pref_sub.add(f'{cn} extends {sc}')
        del d
    z.close()

    hits = {}
    for fam, markers in MARKERS.items():
        found = []
        for m in markers:
            if any(m in s for s in strings_all):
                found.append(m)
        hits[fam] = sorted(set(found))[:6]  # cap detail

    def has(fam):
        return bool(hits[fam]) or bool({'plat_fragment': app_frag_sub, 'service': app_service_sub,
                                        'pref_frag': app_pref_sub}.get(fam))

    frag = has('plat_fragment') or has('androidx_frag') or bool(app_frag_sub)
    pref = has('pref_frag') or bool(app_pref_sub)
    appc = bool(hits['appcompat'])
    comp = bool(hits['compose'])
    hilt = bool(hits['hilt_dagger'])
    work = bool(hits['workmanager'])
    svc  = has('service') or bool(app_service_sub)
    notif = bool(hits['notification'])
    life = bool(hits['lifecycle'])
    coro = bool(hits['coroutines'])
    webv = bool(hits['webview'])

    if comp and (app_view_sub or appc or frag):
        framework = 'hybrid'
    elif comp:
        framework = 'Compose'
    else:
        framework = 'View-world'

    row = dict(
        app=name, path=path, sha16=hashlib.sha256(open(path,'rb').read()).hexdigest()[:16],
        bytes=os.path.getsize(path), nclasses=nclasses, framework=framework,
        Fragment=frag, Preference=pref, AppCompat=appc, Compose=comp,
        Hilt=hilt, WorkManager=work, Service=svc, Notification=notif,
        Lifecycle=life, Coroutines=coro, WebView=webv,
        app_frag_subclasses=sorted(app_frag_sub)[:5],
        app_service_subclasses=sorted(app_service_sub)[:5],
        app_view_subclasses=[x.split(' extends ')[0] for x in sorted(app_view_sub)][:8],
        app_pref_subclasses=sorted(app_pref_sub)[:3],
        markers={k: v for k, v in hits.items() if v},
    )
    return row

rows = []
for name, path in paths:
    try:
        r = scan_apk(name, path)
        r['error'] = None
    except Exception as e:
        r = dict(app=name, path=path, sha16=None, bytes=os.path.getsize(path),
                 nclasses=0, framework='SCAN-ERROR', Fragment=None, Preference=None,
                 AppCompat=None, Compose=None, Hilt=None, WorkManager=None, Service=None,
                 Notification=None, Lifecycle=None, Coroutines=None, WebView=None,
                 app_frag_subclasses=[], app_service_subclasses=[], app_view_subclasses=[],
                 app_pref_subclasses=[], markers={}, error=f'{type(e).__name__}: {e}')
    rows.append(r)
    print(f"[{len(rows)}/{len(paths)}] {name}: fw={r['framework']} F={r['Fragment']} P={r['Preference']} "
          f"A={r['AppCompat']} C={r['Compose']} H={r['Hilt']} W={r['WorkManager']} "
          f"S={r['Service']} N={r['Notification']} err={r['error']}", flush=True)

with open(f'{OUTDIR}/machinery_matrix_raw.json', 'w') as f:
    json.dump(rows, f, indent=1)

# TSV
cols = ['app','framework','Fragment','Preference','AppCompat','Compose','Hilt','WorkManager',
        'Service','Notification','Lifecycle','Coroutines','WebView','nclasses','sha16','bytes']
with open(f'{OUTDIR}/machinery_matrix.tsv','w') as f:
    f.write('\t'.join(cols)+'\n')
    for r in rows:
        f.write('\t'.join(str(r[c]) for c in cols)+'\n')

print("\n=== SUMMARY ===")
from collections import Counter
print("total apps:", len(rows))
print("framework:", Counter(r['framework'] for r in rows))
for fam in ['Fragment','Preference','AppCompat','Compose','Hilt','WorkManager','Service','Notification']:
    n = sum(1 for r in rows if r[fam])
    print(f"{fam}: {n}")
print("errors:", [r['app'] for r in rows if r['error']])
