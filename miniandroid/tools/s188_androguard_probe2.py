#!/usr/bin/env python3
"""S188-W2b androguard probe: the OTHER four FLAT walls (user directive:
'ادامه سایر موارد رو هم بررسی بکن و اضافه بکن' — check the other items too
and add them).

Companion to s188_androguard_probe.py (which covered queens/ball2box/
tranquilstopwatch/composeStopwatch). This probe covers the REMAINING FLAT
tier apps on the post-wall-promotion binary:

  eu.veldsoft.no.thanks    COMPOSE — F-NEW-491 theme chain regression (B→FLAT)
  xyz.deepdaikon.quinb     FLUTTER — dlopen __strncpy_chk2 wall (fixed this
                                      wave; probe records the DEX ground truth)
  com.qwde.ccm             GODOT   — GodotApp.onCreate runs, libgodot load
                                      never reached; find the exact call chain
  org.secuso.privacyfriendlybattleship VIEW — Bitmap.createBitmap(Matrix
                                      overload) + Matrix.postRotate REC-MISS
                                      in GameResources (400+ marks)

Outputs: evidence/s188_w2/androguard/PROBE_FINDINGS_W2B.json
"""
import json
from pathlib import Path

from androguard.core.apk import APK
from androguard.core.dex import DEX

BASE = Path('/home/z/my-project')
STUCK = BASE / 'upload/stuck_apks'
OUT = BASE / 'evidence/s188_w2/androguard'
OUT.mkdir(parents=True, exist_ok=True)

TARGETS = {
    'eu.veldsoft.no.thanks': STUCK / 'eu.veldsoft.no.thanks.apk',
    'xyz.deepdaikon.quinb': STUCK / 'xyz.deepdaikon.quinb.apk',
    'com.qwde.ccm': STUCK / 'com.qwde.ccm.apk',
    'org.secuso.privacyfriendlybattleship': STUCK / 'org.secuso.privacyfriendlybattleship.apk',
}


def find_method(dex_list, class_desc, method_name=None):
    for d in dex_list:
        for c in d.get_classes():
            if c.get_name() == class_desc:
                for m in c.get_methods():
                    if method_name is None or m.get_name() == method_name:
                        yield d, m


def bytecode_of(m, limit=140):
    code = m.get_code()
    if code is None:
        return []
    out = []
    for ins in code.get_bc().get_instructions():
        try:
            out.append(f'{ins.get_name()} {ins.get_output()}')
        except Exception:
            out.append(ins.get_name())
        if len(out) >= limit:
            out.append('…(truncated)')
            break
    return out


def strings_of(dex_list, needle, limit=12):
    hits = []
    for d in dex_list:
        for s in d.get_strings():
            if needle in s:
                hits.append(s[:160])
    return sorted(set(hits))[:limit]


def bitmap_matrix_site_lines(bytecode):
    return [l for l in bytecode
            if 'createBitmap' in l or 'Matrix' in l or 'getWidth' in l
            or 'getHeight' in l or 'BitmapFactory' in l]


def probe(pkg, apk_path):
    a = APK(str(apk_path))
    dexes = [DEX(a.get_file(n)) for n in a.get_files()
             if n.startswith('classes') and n.endswith('.dex')]
    res = {'pkg': pkg, 'apk': str(apk_path), 'dex_count': len(dexes)}
    libs = sorted(n.split('/')[-1] for n in a.get_libraries())
    res['native_libs'] = libs
    res['main_activity'] = a.get_main_activity()

    div = {}

    if pkg == 'org.secuso.privacyfriendlybattleship':
        # W2b live wall: Bitmap.createBitmap(Matrix overload) + Matrix
        # REC-MISS in GameResources.<clinit>/loadShipBitmaps/rotateShipBitmaps.
        # Extract the EXACT overloads + what the results feed (fields? paint?
        # draw?) so the runtime implements the right thing.
        game_cls = None
        for d in dexes:
            for c in d.get_classes():
                if c.get_name() == 'Lorg/secuso/privacyfriendlybattleship/game/GameResources;':
                    game_cls = c
                    div['fields'] = [f'{f.get_name()}:{f.get_descriptor()}'
                                     for f in c.get_fields()][:40]
        for name in ('<clinit>', 'loadShipBitmaps', 'rotateShipBitmaps'):
            got = False
            for d, m in find_method(dexes,
                                    'Lorg/secuso/privacyfriendlybattleship/game/GameResources;',
                                    name):
                bc = bytecode_of(m, 220)
                div[f'GameResources.{name}'] = bc
                div[f'GameResources.{name}.bitmap_sites'] = \
                    bitmap_matrix_site_lines(bc)
                got = True
            if not got:
                div[f'GameResources.{name}'] = 'NOT_FOUND_IN_DEX'
        # where do the rotated bitmaps go?
        div['Bitmap_createBitmap_overloads'] = sorted(set(
            l.split('createBitmap')[-1].strip()[:80]
            for d in dexes for c in d.get_classes()
            for m in c.get_methods()
            for l in bytecode_of(m, 400)
            if 'createBitmap' in l and 'GameResources' in str(c.get_name())))[:8]
        # what else does the game ask of Matrix?
        div['matrix_methods_used'] = sorted(set(
            l.split('Matrix;->')[-1].split()[0][:40]
            for d in dexes for c in d.get_classes()
            for m in c.get_methods()
            for l in bytecode_of(m, 400)
            if 'Landroid/graphics/Matrix;->' in l))[:12]

    elif pkg == 'com.qwde.ccm':
        # W2b live wall: GodotApp.onCreate runs (DEX engine, 0 uncaught),
        # but libgodot load is NEVER reached — find the call chain from
        # GodotApp.onCreate → Godot engine init → System.loadLibrary and
        # the first divergence the runtime hits.
        div['GodotApp.onCreate'] = bytecode_of(
            next(find_method(dexes, 'Lcom/godot/game/GodotApp;', 'onCreate'))[1], 160) \
            if any(True for _ in find_method(dexes, 'Lcom/godot/game/GodotApp;', 'onCreate')) \
            else 'NOT_FOUND'
        for cls in ('Lorg/godotengine/godot/Godot;',
                    'Lorg/godotengine/godot/GodotLib;',
                    'Lorg/godotengine/godot/GodotEngine;'):
            ms = [m.get_name() for d in dexes for c in d.get_classes()
                  if c.get_name() == cls for m in c.get_methods()]
            div[f'methods_{cls}'] = sorted(set(ms))[:24]
        div['loadLibrary_sites'] = [l[:120] for d in dexes
                                    for c in d.get_classes()
                                    for m in c.get_methods()
                                    for l in bytecode_of(m, 200)
                                    if 'loadLibrary' in l][:10]
        div['godot_so_strings'] = strings_of(dexes, 'libgodot', 8)
        div['godot_lib_strings'] = [s[:120] for s in strings_of(dexes, 'godot', 16)]

    elif pkg == 'xyz.deepdaikon.quinb':
        # W2b: the __strncpy_chk2 dlopen wall (FIXED this wave). Record the
        # FlutterJNI.loadLibrary chain + MainActivity flutter setup as DEX
        # ground truth for the promotion evidence.
        for d, m in find_method(dexes, 'Lio/flutter/embedding/engine/FlutterJNI;',
                                'loadLibrary'):
            div['FlutterJNI.loadLibrary'] = bytecode_of(m, 40)
        main = a.get_main_activity() or ''
        main_desc = 'L' + main.replace('.', '/') + ';'
        for d, m in find_method(dexes, main_desc, 'onCreate'):
            div[f'MainActivity.onCreate'] = bytecode_of(m, 100)
        div['flutter_so'] = [n for n in a.get_files()
                             if 'libflutter' in n]
        div['flutter_version_strings'] = strings_of(dexes, 'flutter_engine_', 4)

    elif pkg == 'eu.veldsoft.no.thanks':
        # W2b: F-NEW-491 theme chain regression (was B_STRUCTURED on S186i,
        # FLAT after F-NEW-491). Extract the theme attribute chain the app
        # reads at startup so the A/B bisect can target it.
        main = a.get_main_activity() or ''
        main_desc = 'L' + main.replace('.', '/') + ';'
        for d, m in find_method(dexes, main_desc, 'onCreate'):
            div['MainActivity.onCreate'] = bytecode_of(m, 120)
        div['theme_strings'] = strings_of(dexes, 'Theme', 10)
        div['compose_ambients'] = strings_of(dexes, 'Ambient', 8)
        div['attrs'] = sorted(set(s[:80] for s in strings_of(dexes, 'attr', 10)))

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
            print(f'== {pkg}: OK')
        except Exception as e:
            report[pkg] = {'pkg': pkg, 'error': f'{type(e).__name__}: {e}'}
            print(f'== {pkg}: ERROR {e}')
    out_json = OUT / 'PROBE_FINDINGS_W2B.json'
    out_json.write_text(json.dumps(report, indent=1, ensure_ascii=False))
    print(f'written {out_json}')
    for pkg, r in report.items():
        if 'error' in r:
            continue
        div = r.get('divergence', {})
        print(f'-- {pkg}: div keys: {list(div.keys())[:8]}')


if __name__ == '__main__':
    main()
