#!/usr/bin/env python3
"""cont104_disasm.py — precise per-method disassembly via androguard.

Usage: python3.13 cont104_disasm.py <apk> <class-desc> <method> [<byte-offset-hex>]
Prints the method's instructions with byte offsets; if an offset is given,
prints a window around the instruction that STARTS at or before it.
"""
import sys
from androguard.misc import AnalyzeDex


def main():
    apk_path, cls, method = sys.argv[1], sys.argv[2], sys.argv[3]
    want_off = int(sys.argv[4], 16) if len(sys.argv) > 4 else None
    # classes.dex only needed when the class lives there; androguard takes dex
    import zipfile, tempfile, os
    with zipfile.ZipFile(apk_path) as z:
        names = [n for n in z.namelist() if n.endswith('.dex')]
        for name in names:
            tmp = tempfile.NamedTemporaryFile(suffix='.dex', delete=False)
            tmp.write(z.read(name))
            tmp.close()
            try:
                _, d, _ = AnalyzeDex(tmp.name)
            except Exception:
                os.unlink(tmp.name)
                continue
            for c in d.get_classes():
                if c.get_name() == cls:
                    for m in c.get_methods():
                        if m.get_name() == method:
                            print(f"== {cls} {m.get_descriptor()} in {name}")
                            code = m.get_code()
                            if code is None:
                                print("  (abstract/native)")
                                return
                            bc = m.get_instructions()
                            off = 0
                            lines = []
                            for i in bc:
                                op = i.get_name()
                                out = i.get_output()
                                lines.append((off, f"0x{off:04x}: {op} {out}"))
                                off += i.get_length()
                            if want_off is None:
                                for _, l in lines:
                                    print(l)
                            else:
                                idx = 0
                                for j, (o, _) in enumerate(lines):
                                    if o <= want_off:
                                        idx = j
                                    else:
                                        break
                                lo, hi = max(0, idx - 12), min(len(lines), idx + 13)
                                for o, l in lines[lo:hi]:
                                    mark = " >>>" if o <= want_off < o + 8 else "    "
                                    print(mark, l)
                            os.unlink(tmp.name)
                            return
            os.unlink(tmp.name)
    print(f"NOT FOUND {cls}.{method}")


if __name__ == '__main__':
    main()
