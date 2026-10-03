#!/usr/bin/env python3
"""DIFFERENTIAL-366 — fetch white-app candidate APKs from the S115 population.

Selection law (issue #366 §2): white candidates come from the S115 NEAR_BLANK
population (evidence/audit_s107/reopened.json), spanning DIFFERENT root
families so the differential has discriminating power. Corrupt-fetch tickets
(#87 #107 #120 #185 #206), PARTIAL-only tickets (#191 #216 #219 #212) are NOT
eligible.

Fetch: F-Droid suggested version via api/v1, else latest.
Output: tmp/diff366_apks/<pkg>_<code>.apk + manifest json.
"""
import json, os, sys, time, urllib.request
from pathlib import Path

BASE = Path('/home/z/my-project')
APKDIR = BASE / 'tmp/diff366_apks'
APKDIR.mkdir(parents=True, exist_ok=True)
FETCH_CAP = 120

# candidate pool: ticket -> package (spanning S115 families 1/2/3/4/5/6/7)
CANDIDATES = [
    (202, 'org.fossify.clock',            'F1-empty-viewtree'),
    (122, 'com.sidhant.triplematch',      'F1-empty-viewtree'),
    (148, 'com.forrestguice.suntimeswidget', 'F1-empty-viewtree'),
    (64,  'com.galaxyrio.sudokusolver',   'F2-empty-viewtree-rc1'),
    (88,  'com.fairytrick.fairymahjong',  'F2-empty-viewtree-rc1'),
    (109, 'com.game.asteroids_revenge',   'F3-libgdx-jni'),
    (75,  'com.yepgoryo.EggReturnsHome',  'F3-libgdx-jni'),
    (86,  'com.sidhant.blockblast',       'F4-lifecycleregistry'),
    (96,  'fr.arnaudguyon.spacevertex',   'F5-fragmentmanager'),
    (67,  'com.sanskritbasics.memory',    'F6-multidex'),
    (218, 'com.fpf.smartscan',            'F7-viewtree-owner'),
    (222, 'com.google.android.stardroid', 'F-other'),
]

UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) MiniAndroid-Research'}

def http_get(url, dest, cap=FETCH_CAP):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=cap) as r, open(dest, 'wb') as f:
            while True:
                chunk = r.read(1 << 16)
                if not chunk:
                    break
                f.write(chunk)
        return True
    except Exception as e:
        if dest.exists():
            dest.unlink()
        print(f'    ERR {url}: {e}')
        return False

def fdroid_code(pkg):
    try:
        req = urllib.request.Request(
            f'https://f-droid.org/api/v1/packages/{pkg}', headers=UA)
        with urllib.request.urlopen(req, timeout=45) as r:
            meta = json.load(r)
        return meta.get('suggestedVersionCode'), meta.get('suggestedVersionName')
    except Exception as e:
        print(f'    meta ERR {pkg}: {e}')
        return None, None

def main():
    manifest = {}
    mpath = APKDIR / 'manifest.json'
    if mpath.exists():
        manifest = json.load(open(mpath))
    for ticket, pkg, family in CANDIDATES:
        key = f't{ticket}_{pkg}'
        if key in manifest and (APKDIR / manifest[key]['file']).exists():
            print(f'[skip] {key}')
            continue
        print(f'[fetch] t{ticket} {pkg} ({family})')
        code, vname = fdroid_code(pkg)
        fetched = None
        for c in ([code] if code else []) :
            dest = APKDIR / f'{pkg}_{c}.apk'
            if dest.exists() and dest.stat().st_size > 10000:
                fetched = dest
                break
            print(f'    try {pkg}_{c}.apk ...')
            if http_get(f'https://f-droid.org/repo/{pkg}_{c}.apk', dest):
                fetched = dest
                break
        if fetched is None:
            # last resort: F-Droid archive pool
            if code and http_get(f'https://f-droid.org/archive/{pkg}_{code}.apk',
                                 APKDIR / f'{pkg}_{code}.apk'):
                fetched = APKDIR / f'{pkg}_{code}.apk'
        if fetched:
            manifest[key] = {
                'ticket': ticket, 'package': pkg, 'family': family,
                'file': fetched.name, 'bytes': fetched.stat().st_size,
                'version_code': code, 'version_name': vname,
            }
            print(f'    OK {fetched.name} ({fetched.stat().st_size} bytes)')
        else:
            manifest[key] = {'ticket': ticket, 'package': pkg,
                             'family': family, 'file': None, 'error': 'FETCH_FAIL'}
            print(f'    FETCH FAIL {pkg}')
        mpath.write_text(json.dumps(manifest, indent=1))
    ok = sum(1 for v in manifest.values() if v.get('file'))
    print(f'\nfetched {ok}/{len(CANDIDATES)}')

if __name__ == '__main__':
    main()
