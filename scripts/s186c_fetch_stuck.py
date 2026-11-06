#!/usr/bin/env python3
"""S186c: re-fetch the 40 stuck-title APKs whose /tmp corpus died with the sandbox.
SQLITE_RULE Clause 4: fixed upstream URLs + script = rebuildable state.
Source: F-Droid repo API (https://f-droid.org/api/v1/packages/<pkg>) → latest
stable versioncode → https://f-droid.org/repo/<pkg>_<code>.apk.
Non-F-Droid titles are recorded honestly as UNRESOLVED (no invention).
"""
import json, subprocess, sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

BASE = Path('/home/z/my-project')
DEST = BASE / 'upload/stuck_apks'
DEST.mkdir(parents=True, exist_ok=True)
MAN = BASE / 'evidence/s186_s107/S186C_STUCK_APK_MANIFEST.json'

CENSUS = BASE / 'evidence/s186_s107/S186_INCOMPLETE_CENSUS.json'


def stuck_packages():
    d = json.load(open(CENSUS))
    rows = d['rows']
    out = []
    for r in rows:
        if r['bucket'] in ('EXECUTED_CRASHED', 'LOADED_PARTIAL', 'EXECUTED_PARTIAL'):
            pkg = (r['package'] or '').strip()
            if pkg:
                out.append((int(r['issue']), pkg))
    return sorted(out)


def fdroid_latest(pkg):
    """Return (versioncode, apk_url) or (None, reason)."""
    url = f'https://f-droid.org/api/v1/packages/{pkg}'
    r = subprocess.run(['curl', '-fsSL', '--max-time', '30', url],
                       capture_output=True, timeout=40)
    if r.returncode != 0:
        return None, f'api-failed rc={r.returncode}'
    try:
        j = json.loads(r.stdout)
    except Exception as e:
        return None, f'api-json {e}'
    pkgs = j.get('packages') or []
    code = j.get('suggestedVersionCode') or (pkgs[-1].get('versionCode') if pkgs else None)
    if not code:
        return None, 'no versioncode (not on F-Droid or archived)'
    return int(code), f'https://f-droid.org/repo/{pkg}_{int(code)}.apk'


def fetch_one(item):
    issue, pkg = item
    apk = DEST / f'{pkg}.apk'
    if apk.exists() and apk.stat().st_size > 10000:
        return dict(issue=issue, pkg=pkg, status='CACHED',
                    path=str(apk), size=apk.stat().st_size)
    code, url_or_reason = fdroid_latest(pkg)
    if code is None:
        return dict(issue=issue, pkg=pkg, status='UNRESOLVED', reason=url_or_reason)
    r = subprocess.run(['curl', '-fL', '--max-time', '300', '-o', str(apk),
                        url_or_reason], capture_output=True, timeout=320)
    if r.returncode != 0 or not apk.exists() or apk.stat().st_size < 10000:
        apk.unlink(missing_ok=True)
        return dict(issue=issue, pkg=pkg, status='DOWNLOAD_FAIL',
                    url=url_or_reason, rc=r.returncode)
    return dict(issue=issue, pkg=pkg, status='OK', versioncode=code,
                url=url_or_reason, path=str(apk), size=apk.stat().st_size)


def main():
    items = stuck_packages()
    have = json.load(open('/tmp/stuck_apks.json')) if Path('/tmp/stuck_apks.json').exists() else None
    results = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        for res in ex.map(fetch_one, items):
            print(res.get('status'), res['issue'], res['pkg'],
                  res.get('size', res.get('reason', '')), flush=True)
            results.append(res)
    ok = sum(1 for r in results if r['status'] in ('OK', 'CACHED'))
    unres = [r for r in results if r['status'] == 'UNRESOLVED']
    fail = [r for r in results if r['status'] == 'DOWNLOAD_FAIL']
    man = dict(generated='2026-11-06', law='SQLITE_RULE Clause 4 fetch-if-missing',
               total=len(results), ok=ok, unresolved=len(unres), failed=len(fail),
               results=results)
    MAN.write_text(json.dumps(man, indent=1))
    print(f'\nOK={ok} UNRESOLVED={len(unres)} FAIL={len(fail)} -> {MAN}')


if __name__ == '__main__':
    main()
