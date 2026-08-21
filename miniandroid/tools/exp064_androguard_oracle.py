#!/usr/bin/env python3
"""
EXP-064 Phase 8: Androguard resource oracle.

Loads Telegram's resources.arsc via Androguard and resolves a list of
target resource names. Saves the result to run/exp064/androguard_oracle.json
for comparison against the MiniAndroid runtime's resource resolution.

This is the INDEPENDENT ORACLE per EXP-064 Phase 8 spec. The runtime
must not silently depend on it; it is used purely for validation.
"""
import json
import os
import sys
import time
import logging

# Suppress androguard's extremely verbose loguru output
try:
    from loguru import logger
    logger.remove()
    logger.add(sys.stderr, level='WARNING')
except ImportError:
    pass


def main():
    apk_path = sys.argv[1] if len(sys.argv) > 1 else \
        '/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/download/exp038_telegram/Telegram.apk'
    out_path = sys.argv[2] if len(sys.argv) > 2 else \
        '/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/run/exp064/androguard_oracle.json'

    t0 = time.time()
    print(f"[ORACLE] Loading APK: {apk_path}")
    from androguard.core.apk import APK
    apk = APK(apk_path)
    arsc = apk.get_android_resources()
    print(f"[ORACLE] ARSC loaded in {time.time()-t0:.1f}s")

    pkgs = arsc.get_packages_names()
    print(f"[ORACLE] Packages: {pkgs}")

    # Target resources per EXP-064 spec (Phase 1)
    targets = [
        'StartMessaging',
        'PhoneNumber',
        'StartText',
        'YourCode',
        'AppName',
        # Additional resources known to be referenced by LoginActivity
        'CountryCode',
        'Continue',
        'Next',
    ]

    result = {
        'apk_path': apk_path,
        'apk_sha256': None,
        'packages': list(pkgs),
        'resolved': {},
        'elapsed_seconds': None,
    }

    import hashlib
    with open(apk_path, 'rb') as f:
        result['apk_sha256'] = hashlib.sha256(f.read()).hexdigest()

    for name in targets:
        try:
            v = arsc.get_string_resources(name)
            if isinstance(v, dict):
                # {pkg_name: {locale: value}}
                for pkg, locales in v.items():
                    for locale, val in locales.items():
                        result['resolved'].setdefault(name, []).append({
                            'package': pkg,
                            'locale': locale or 'default',
                            'value': val,
                        })
            elif v:
                result['resolved'][name] = [{'package': pkgs[0] if pkgs else '?',
                                              'locale': 'default',
                                              'value': v}]
            else:
                result['resolved'][name] = []
        except Exception as e:
            result['resolved'][name] = [{'error': str(e)}]

    # Get total resolved strings count
    try:
        rss = arsc.get_resolved_strings()
        total = 0
        for pkg, locales in rss.items():
            for locale, items in locales.items():
                total += len(items)
        result['total_resolved_strings'] = total
    except Exception as e:
        result['total_resolved_strings_error'] = str(e)

    result['elapsed_seconds'] = time.time() - t0

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    print(f"[ORACLE] Wrote {out_path}")
    print(json.dumps(result, indent=2, default=str)[:2000])


if __name__ == '__main__':
    main()
