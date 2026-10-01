#!/usr/bin/env python3
"""S134 wave-3: disassemble WhatsApp LX/00i;.A0F (F-NEW-166 root).
Usage: s134_wa_disasm.py <Lclass;> <method> [dex-name-substr]
Scans ALL classes*.dex in the APK (multidex). Ground truth = androguard.
"""
import logging, sys, zipfile
logging.disable(logging.CRITICAL)
from androguard.core.dex import DEX

APK = '/tmp/my-project/apk_cache/WhatsApp_real.apk'


def main():
    cls = sys.argv[1]
    meth = sys.argv[2] if len(sys.argv) > 2 else None
    z = zipfile.ZipFile(APK)
    dexes = sorted(n for n in z.namelist()
                   if n.startswith('classes') and n.endswith('.dex'))
    for dname in dexes:
        try:
            d = DEX(z.read(dname))
        except Exception as e:
            print(f'# {dname}: parse failed {e}')
            continue
        for c in d.get_classes():
            if c.get_name() != cls:
                continue
            for m in c.get_methods():
                if meth and m.get_name() != meth:
                    continue
                print(f"=== [{dname}] {cls}.{m.get_name()} "
                      f"{m.get_descriptor()} ===")
                code = m.get_code()
                if code is None:
                    print('  (no code)')
                    continue
                bc = code.get_bc()
                idx = 0
                for ins in bc.get_instructions():
                    try:
                        out = ins.get_output()
                    except Exception as e:
                        out = f'<{e}>'
                    print(f'  {idx:04x}: {ins.get_name()} {out}')
                    idx += ins.get_length()


if __name__ == '__main__':
    main()
