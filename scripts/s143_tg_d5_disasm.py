#!/usr/bin/env python3
"""s143_tg_d5_disasm.py — S143 Telegram launch NPE root probe.

The traced run dies at Lorg/telegram/ui/LaunchActivity;.d5 (NPE unwound,
invoke_pc=0x98, escaped .onCreate at 0x3e9 -> APP-BOUNDARY, launch chain
killed at 2 frames). This tool resolves d5 across ALL dex files of the
forkgram APK and prints the ref-resolved disasm so the NPE source can be
pinned to a concrete field/invoke.

Usage: s143_tg_d5_disasm.py <apk> <class-desc> <method-name>
"""
import sys, zipfile, importlib.util

spec = importlib.util.spec_from_file_location(
    'cd', '/home/z/my-project/scripts/cont9_dexdump.py')
cd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cd)


def main():
    apk, cls_desc, meth = sys.argv[1], sys.argv[2], sys.argv[3]
    want = cls_desc if cls_desc.endswith(';') else cls_desc + ';'
    with zipfile.ZipFile(apk) as z:
        dexes = sorted(n for n in z.namelist()
                       if n.startswith('classes') and n.endswith('.dex'))
        print(f"# {len(dexes)} dex files: {dexes}")
        for dn in dexes:
            d = cd.Dex(z.read(dn))
            off = d.find_class(want)
            if off is None:
                continue
            cm = d.class_methods(off)
            print(f"# FOUND {want} in {dn} super={cm['super']}")
            hits = [m for m in cm['direct'] + cm['virtual'] if m[0] == meth]
            if not hits:
                print(f"# no method '{meth}' (direct+virtual listed below)")
                for m in cm['direct'] + cm['virtual']:
                    print(f"   {m[0]}{m[1]} acc={m[2]:#x} size={m[3]}")
                return
            for m in hits:
                print(f"\n=== {want}.{m[0]}{m[1]} acc={m[2]:#x} code_off={m[4]:#x} ===")
                for line in d.disasm(m[4]):
                    print(line)
            return
        print(f"# class {want} NOT FOUND in any dex")


if __name__ == '__main__':
    main()
