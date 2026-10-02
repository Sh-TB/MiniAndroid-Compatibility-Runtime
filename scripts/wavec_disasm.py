#!/usr/bin/env python3
"""WAVE C (F-NEW-181): disassemble guava map-build chain from WhatsApp APK.
Works with androguard 3.3.5 (DalvikVMFormat API; container-reset restore).
Usage: wavec_disasm.py <Lclass;> [method] [outfile]
Ground truth = the APK's real DEX.
"""
import logging, sys, zipfile
logging.disable(logging.CRITICAL)
from androguard.core.bytecodes.dvm import DalvikVMFormat

APK = '/tmp/my-project/apk_cache/WhatsApp_real.apk'


def main():
    cls = sys.argv[1]
    meth = sys.argv[2] if len(sys.argv) > 2 else None
    out = sys.argv[3] if len(sys.argv) > 3 else None
    fh = open(out, 'w') if out else sys.stdout
    z = zipfile.ZipFile(APK)
    dexes = sorted(n for n in z.namelist()
                   if n.startswith('classes') and n.endswith('.dex'))
    for dname in dexes:
        try:
            d = DalvikVMFormat(z.read(dname))
        except Exception as e:
            print(f'# {dname}: parse failed {e}', file=fh)
            continue
        for c in d.get_classes():
            if c.get_name() != cls:
                continue
            for m in c.get_methods():
                if meth and m.get_name() != meth:
                    continue
                print(f"=== [{dname}] {cls}.{m.get_name()} "
                      f"{m.get_descriptor()} ===", file=fh)
                code = m.get_code()
                if code is None:
                    print('  (no code)', file=fh)
                    continue
                idx = 0
                for ins in code.get_bc().get_instructions():
                    try:
                        o = ins.get_output()
                    except Exception as e:
                        o = f'<{e}>'
                    print(f'  {idx:04x}: {ins.get_name()} {o}', file=fh)
                    idx += ins.get_length()
    if out:
        fh.close()


if __name__ == '__main__':
    main()
