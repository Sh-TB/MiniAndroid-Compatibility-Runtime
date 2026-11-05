#!/usr/bin/env python3
"""s172_disasm_run_full.py — full unit-annotated disasm of
Fragment$$ExternalSyntheticLambda0.run() with the invoke_pc=0xf5 marker."""
import struct
import sys
import zipfile

sys.path.insert(0, '/home/z/my-project/scripts')
from s169_disasm import OPS, opname, APK
from cont9_dexdump import Dex

CLS = 'Landroidx/fragment/app/Fragment$$ExternalSyntheticLambda0;'
MARK_BYTES = 0xf5 * 2  # engine pc is in code units; 0xf5 units = byte 490


def main():
    z = zipfile.ZipFile(APK)
    for dname in sorted(n for n in z.namelist()
                        if n.startswith('classes') and n.endswith('.dex')):
        dex_bytes = z.read(dname)
        d = Dex(dex_bytes)
        cdef = d.find_class(CLS)
        if cdef is None:
            continue
        info = d.class_methods(cdef)
        for kind in ('direct', 'virtual'):
            for (mn, md, acc, sz, code) in info[kind]:
                if mn != 'run':
                    continue
                insns_size = struct.unpack_from('<I', dex_bytes, code + 12)[0]
                off = code + 16
                print(f"run{md} code_off=0x{code:x} insns={insns_size} units "
                      f"({insns_size*2} bytes)")

                def fstr(idx):
                    try:
                        return "%s.%s:%s" % d.field_ref(idx)
                    except Exception:
                        return f"field@{idx}"

                def mstr(idx):
                    try:
                        return "%s.%s%s" % d.method_ref(idx)
                    except Exception:
                        return f"method@{idx}"

                pc = 0
                end = insns_size * 2
                buf = dex_bytes
                while pc < end:
                    op = buf[off + pc]
                    size, fmt, _ = OPS.get(op, (2, '??', '?'))
                    detail = ''
                    try:
                        if fmt == '21t':
                            reg = buf[off + pc + 1]
                            o = struct.unpack_from('<h', buf, off + pc + 2)[0]
                            detail = f"v{reg} -> 0x{pc + o*2:x}"
                        elif fmt == '10t':
                            o = struct.unpack_from('<b', buf, off + pc + 1)[0]
                            detail = f"-> 0x{pc + o*2:x}"
                        elif fmt in ('20t',):
                            o = struct.unpack_from('<h', buf, off + pc + 2)[0]
                            detail = f"-> 0x{pc + o*2:x}"
                        elif fmt == '30t':
                            o = struct.unpack_from('<i', buf, off + pc + 2)[0]
                            detail = f"-> 0x{pc + o*2:x}"
                        elif fmt == '31t':
                            o = struct.unpack_from('<i', buf, off + pc + 2)[0]
                            detail = f"v{buf[off+pc+1]} payload=0x{pc + o*2:x}"
                        elif fmt == '21c':
                            reg = buf[off + pc + 1]
                            idx = struct.unpack_from('<H', buf, off + pc + 2)[0]
                            if op in (0x1a, 0x1b):
                                try:
                                    detail = f'v{reg}, "{d.string_ref(idx)}"'
                                except Exception:
                                    detail = f"v{reg}, str@{idx}"
                            else:
                                detail = f"v{reg}, @{fstr(idx)}"
                        elif fmt == '31c':
                            reg = buf[off + pc + 1]
                            idx = struct.unpack_from('<I', buf, off + pc + 2)[0]
                            try:
                                detail = f'v{reg}, "{d.string_ref(idx)}"'
                            except Exception:
                                detail = f"v{reg}, str@{idx}"
                        elif fmt == '22c':
                            ra = buf[off + pc + 1] & 0xF
                            rb = buf[off + pc + 1] >> 4
                            idx = struct.unpack_from('<H', buf, off + pc + 2)[0]
                            detail = f"v{ra}, v{rb}, @{fstr(idx)}"
                        elif fmt == '35c':
                            idx = struct.unpack_from('<H', buf, off + pc + 2)[0]
                            regs = buf[off + pc + 4:off + pc + 6]
                            rl = [f"v{b & 0xF if i == 0 else b >> 4}"
                                  for i, b in enumerate(regs)]
                            detail = f"{','.join(rl)}, @{mstr(idx)}"
                        elif fmt == '3rc':
                            idx = struct.unpack_from('<H', buf, off + pc + 2)[0]
                            ra = buf[off + pc + 4]
                            cnt = buf[off + pc + 5]
                            detail = (f"v{ra}..v{ra+cnt-1}"
                                      if cnt else f"v{ra}), @{mstr(idx)}")
                        elif fmt == '10x':
                            pass
                        elif fmt == '11x':
                            detail = f"v{buf[off+pc+1]}"
                        elif fmt == '11n':
                            r = buf[off + pc + 1] & 0xF
                            lit = buf[off + pc + 1] >> 4
                            detail = f"v{r}, {lit - 16 if lit > 7 else lit}"
                        elif fmt == '22b':
                            ra = buf[off + pc + 1]
                            rb = buf[off + pc + 2]
                            lit = struct.unpack_from('<b', buf, off + pc + 3)[0]
                            detail = f"v{ra}, v{rb}, {lit}"
                        elif fmt == '31i':
                            reg = buf[off + pc + 1]
                            lit = struct.unpack_from('<i', buf, off + pc + 2)[0]
                            detail = f"v{reg}, {lit}"
                        elif fmt == '22s':
                            ra = buf[off + pc + 1] & 0xF
                            rb = buf[off + pc + 1] >> 4
                            lit = struct.unpack_from('<h', buf, off + pc + 2)[0]
                            detail = f"v{ra}, v{rb}, {lit}"
                        elif fmt == '22t':
                            ra = buf[off + pc + 1] & 0xF
                            rb = buf[off + pc + 1] >> 4
                            o = struct.unpack_from('<h', buf, off + pc + 2)[0]
                            detail = f"v{ra}, v{rb} -> 0x{pc + o*2:x}"
                        elif fmt == '21s':
                            reg = buf[off + pc + 1]
                            lit = struct.unpack_from('<h', buf, off + pc + 2)[0]
                            detail = f"v{reg}, {lit}"
                        elif fmt == '23x':
                            ra = buf[off + pc + 1] & 0xF
                            rb = buf[off + pc + 1] >> 4
                            rc = buf[off + pc + 2]
                            detail = f"v{ra}, v{rb}, v{rc}"
                        elif fmt == '12x':
                            ra = buf[off + pc + 1] & 0xF
                            rb = buf[off + pc + 1] >> 4
                            detail = f"v{ra}, v{rb}"
                    except Exception as e:
                        detail = f"(decode err {e})"
                    unit = pc // 2
                    mark = "  <<<< invoke_pc=0xf5 UNIT" if pc <= MARK_BYTES < pc + size else ""
                    print(f"  u=0x{unit:04x} b=0x{pc:04x}: "
                          f"{opname(op):<24} {detail}{mark}")
                    pc += size
    print("done")


if __name__ == '__main__':
    main()
