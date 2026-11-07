#!/usr/bin/env python3
"""S188 androguard probe: DEX-level ground truth for the W2 first-divergence walls.

User directive (Persian): "ادامه بدهد و از برنامه androguard هم کمک بگیر" —
continue, and use androguard to help. This tool is the fulfillment of that
directive: androguard (static APK/DEX analysis) extracts the EXACT missing
symbols behind each FLAT wall, so the runtime implements the right thing
instead of guessing from obfuscated names.

Targets (W2 FLAT tier, first-divergence):
  com.sidhant.queens          FLUTTER  — RuntimeException from Lh0/j;.<init>
  com.simondalvai.ball2box    GODOT    — Enum reflection + libgodot_android.so
  tibarj.tranquilstopwatch    VIEW     — NPE in FragmentContainerView.<init>
  com.justdeax.composeStopwatch COMPOSE — CNFE AndroidCompositionLocals_androidKt

Probe outputs per app:
  1. cross-validation of the S188 route classifier (libs/assets/manifest)
  2. the exact bytecode of the diverging constructor (smali-ish dump)
  3. referenced classes/methods/strings around the divergence point
"""
import json
import sys
from pathlib import Path

from androguard.core.apk import APK
from androguard.core.dex import DEX

BASE = Path('/home/z/my-project')
STUCK = BASE / 'upload/stuck_apks'
OUT = BASE / 'evidence/s188_w2/androguard'
OUT.mkdir(parents=True, exist_ok=True)

TARGETS = {
    'com.sidhant.queens': STUCK / 'com.sidhant.queens.apk',
    'com.simondalvai.ball2box': STUCK / 'com.simondalvai.ball2box.apk',
    'tibarj.tranquilstopwatch': STUCK / 'tibarj.tranquilstopwatch.apk',
    'com.justdeax.composeStopwatch': STUCK / 'com.justdeax.composeStopwatch.apk',
}

ROUTE_SIGNATURES = {
    'FLUTTER': ['Lio/flutter/embedding/engine/FlutterEngine;',
                'Lio/flutter/', 'flutter'],
    'GODOT': ['libgodot_android.so', 'Lorg/godotengine/godot/Godot;'],
    'COMPOSE': ['Landroidx/compose/runtime/CompositionLocal;',
                'androidx/compose/'],
    'WEBVIEW_HTML5_PACKAGED': ['Landroid/webkit/WebView;', 'file:///android_asset/'],
    'VIEW': ['Landroid/view/View;', 'Landroid/widget/'],
    'LIBGDX': ['Lcom/badlogic/gdx/'],
}


def find_method(dex_list, class_desc, method_name=None):
    """Yield (dex, encoded_method) for class_desc[.method_name]."""
    for d in dex_list:
        for c in d.get_classes():
            if c.get_name() == class_desc:
                for m in c.get_methods():
                    if method_name is None or m.get_name() == method_name:
                        yield d, m


def bytecode_of(m):
    """Return list of 'opcode operands' strings of a method's bytecode."""
    code = m.get_code()
    if code is None:
        return []
    out = []
    for ins in code.get_bc().get_instructions():
        try:
            out.append(f'{ins.get_name()} {ins.get_output()}')
        except Exception:
            out.append(ins.get_name())
    return out


def strings_of(dex_list, needle):
    hits = []
    for d in dex_list:
        for s in d.get_strings():
            if needle in s:
                hits.append(s[:160])
    return sorted(set(hits))


def probe(pkg, apk_path):
    a = APK(str(apk_path))
    dexes = []
    for name in a.get_files():
        if name.startswith('classes') and name.endswith('.dex'):
            dexes.append(DEX(a.get_file(name)))
    print(f'[{pkg}] dex files: {len(dexes)}')

    res = {'pkg': pkg, 'apk': str(apk_path), 'dex_count': len(dexes)}

    # ── 1. classifier cross-validation: native libs, assets, manifest ──
    libs = sorted(n.split('/')[-1] for n in a.get_libraries())
    assets = sorted(n for n in a.get_files() if n.startswith('assets/'))[:40]
    res['native_libs'] = libs
    res['assets_sample'] = assets
    res['main_activity'] = a.get_main_activity()
    res['activities'] = a.get_activities()[:12]

    detected = set()
    joined_libs = ' '.join(libs)
    all_strings_probe = None
    for route, sigs in ROUTE_SIGNATURES.items():
        for sig in sigs:
            if sig.endswith('.so') and sig in joined_libs:
                detected.add(route)
            elif sig.startswith('lib') and sig in joined_libs:
                detected.add(route)
    if any(x.startswith('flutter') for x in assets):
        detected.add('FLUTTER')
    if any('godot' in x for x in assets):
        detected.add('GODOT')
    res['route_from_androguard_libs_assets'] = sorted(detected)

    # DEX class-prefix scan (cheap, one pass over class descs)
    prefixes = {}
    for d in dexes:
        for c in d.get_classes():
            n = c.get_name()
            for probe_key in ['io/flutter', 'godotengine', 'androidx/compose',
                              'badlogic/gdx', 'org/libsdl', 'webkit']:
                if probe_key in n:
                    prefixes[probe_key] = prefixes.get(probe_key, 0) + 1
    res['dex_class_prefix_hits'] = prefixes
    if prefixes.get('io/flutter', 0) > 0:
        detected.add('FLUTTER')
    if prefixes.get('godotengine', 0) > 0:
        detected.add('GODOT')
    if prefixes.get('androidx/compose', 0) > 0:
        detected.add('COMPOSE')
    res['route_from_androguard'] = sorted(detected)

    # ── 2. divergence-point bytecode ──
    div = {}
    if pkg == 'com.sidhant.queens':
        # W2 trace: RuntimeException unwound Lh0/j;.<init> ← Lg0/f;.onCreate
        for d, m in find_method(dexes, 'Lh0/j;', '<init>'):
            div['Lh0/j;.<init>'] = bytecode_of(m)[:80]
            # collect every class the ctor touches
        for d, m in find_method(dexes, 'Lg0/f;', 'onCreate'):
            div['Lg0/f;.onCreate'] = bytecode_of(m)[:80]
        div['cowset_refs'] = []
        for d in dexes:
            for s in d.get_strings():
                if 'CopyOnWrite' in s:
                    div['cowset_refs'].append(s[:120])
        div['cowset_refs'] = sorted(set(div['cowset_refs']))[:10]
        # h0/j super class + fields (what kind of object is it?)
        for d in dexes:
            for c in d.get_classes():
                if c.get_name() == 'Lh0/j;':
                    div['h0/j_super'] = c.get_superclassname()
                    div['h0/j_ifaces'] = list(c.get_interfaces())
                    div['h0/j_fields'] = [f'{f.get_name()}:{f.get_descriptor()}'
                                          for f in c.get_fields()]
    elif pkg == 'tibarj.tranquilstopwatch':
        # W2 trace: NPE in FragmentContainerView.<init> called from MainActivity
        main_cls = 'Ltibarj/tranquilstopwatch/MainActivity;'
        for d, m in find_method(dexes, main_cls, 'onCreate'):
            div['MainActivity.onCreate'] = bytecode_of(m)[:120]
        # FragmentContainerView references inside the app
        refs = set()
        for d, m in find_method(dexes, main_cls):
            for line in bytecode_of(m):
                if 'FragmentContainer' in line or 'NavigationView' in line:
                    refs.add(line)
        div['fragment_container_refs'] = sorted(refs)[:20]
    elif pkg == 'com.simondalvai.ball2box':
        # W2: java.lang.Enum.<init> reflection-safe ctor + libgodot loading
        div['enum_reflect'] = strings_of(dexes, 'java.lang.Enum')[:10]
        div['godot_strings'] = strings_of(dexes, 'godot')[:12]
        main_cls = 'org/godotengine/godot/Godot'
        for d, m in find_method(dexes, f'L{main_cls};', 'onCreate'):
            div['Godot.onCreate_head'] = bytecode_of(m)[:60]
    elif pkg == 'com.justdeax.composeStopwatch':
        # W2: CNFE AndroidCompositionLocals_androidKt
        main_cls = 'Lcom/justdeax/composeStopwatch/MainActivity;'
        if not any(True for d in dexes for c in d.get_classes()
                   if c.get_name() == main_cls):
            # find whatever MainActivity exists
            for d in dexes:
                for c in d.get_classes():
                    if c.get_name().endswith('/MainActivity;'):
                        main_cls = c.get_name()
        for d, m in find_method(dexes, main_cls, 'onCreate'):
            div[f'{main_cls}.onCreate'] = bytecode_of(m)[:80]
        div['composition_local_kt'] = strings_of(dexes,
                                                 'AndroidCompositionLocals')[:6]
        div['setcontent_refs'] = strings_of(dexes, 'setContent')[:6]

    res['divergence'] = div
    return res


def main():
    report = {}
    for pkg, path in TARGETS.items():
        if not path.exists():
            print(f'MISSING {path}')
            continue
        try:
            report[pkg] = probe(pkg, path)
        except Exception as e:
            report[pkg] = {'pkg': pkg, 'error': f'{type(e).__name__}: {e}'}
    out_json = OUT / 'PROBE_FINDINGS.json'
    out_json.write_text(json.dumps(report, indent=1, ensure_ascii=False))
    print(f'written {out_json}')
    # compact console digest
    for pkg, r in report.items():
        if 'error' in r:
            print(f'== {pkg}: ERROR {r["error"]}')
            continue
        print(f'== {pkg}')
        print(f'   androguard route : {r["route_from_androguard"]}')
        print(f'   libs/assets route: {r["route_from_androguard_libs_assets"]}')
        print(f'   dex prefixes     : {r["dex_class_prefix_hits"]}')
        print(f'   main activity    : {r["main_activity"]}')
        for k, v in r.get('divergence', {}).items():
            if isinstance(v, list) and v and isinstance(v[0], str) and len(k) > 0:
                print(f'   - {k}: {len(v)} items; head: {v[:3]}')
            else:
                print(f'   - {k}: {v}')


if __name__ == '__main__':
    main()
