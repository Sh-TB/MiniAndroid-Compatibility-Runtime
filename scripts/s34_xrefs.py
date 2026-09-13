#!/usr/bin/env python3
"""S34: find every method that invokes methods of given target classes.
Usage: s34_xrefs.py <Lclass;> [more classes...]
Ground-truth cross-reference scan via androguard EncodedMethod iteration.
"""
import logging, sys, zipfile
logging.disable(logging.CRITICAL)
from androguard.core.dex import DEX

APK = '/tmp/my-project/apk_cache/io.github.yamin8000.dooz_18.apk'


def main():
    targets = set(a for a in sys.argv[1:] if a.startswith('L'))
    z = zipfile.ZipFile(APK)
    d = DEX(z.read('classes.dex'))
    out = []
    for c in d.get_classes():
        cn = c.get_name()
        for m in c.get_methods():
            code = m.get_code()
            if code is None:
                continue
            try:
                for ins in code.get_bc().get_instructions():
                    nm = ins.get_name()
                    if not nm.startswith('invoke'):
                        continue
                    out_s = ins.get_output()
                    for t in targets:
                        if t + '->' in out_s or (t in out_s and '->' in out_s):
                            out.append((cn, m.get_name(), m.get_descriptor()[:40], nm, out_s[:90]))
            except Exception:
                pass
    seen = set()
    for cn, mn, md, inm, out_s in out:
        key = (cn, mn, out_s)
        if key in seen:
            continue
        seen.add(key)
        print(f'{cn}.{mn} {md}\n    {inm} {out_s}')
    print(f'total unique refs: {len(seen)}')


if __name__ == '__main__':
    main()
